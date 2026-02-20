const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

// Local fallbacks
let sharpAvailable = true;
let sharp;
try { sharp = require('sharp'); } catch (e) { sharpAvailable = false; }

let pdfParseAvailable = true;
let pdfParse;
try { pdfParse = require('pdf-parse'); } catch (e) { pdfParseAvailable = false; }

const SCALEDOWN_KEY = process.env.SCALEDOWN_API_KEY;
const SCALEDOWN_URL = process.env.SCALEDOWN_API_URL || 'https://api.scaledown.xyz/compress/raw/';

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + sizes[i];
}

async function callScaleDownAPIJSON(body) {
  const headers = { 'x-api-key': SCALEDOWN_KEY, 'Content-Type': 'application/json' };
  const resp = await axios.post(SCALEDOWN_URL, body, { headers, timeout: 20000 });
  return resp;
}

async function compressImage(buffer, mimetype) {
  const originalSize = buffer.length;
  // Use ScaleDown API when key present
  if (SCALEDOWN_KEY) {
    try {
      const b64 = buffer.toString('base64');
      const body = { context: `Compress and summarize this document for property management use`, prompt: b64, scaledown: { rate: 'auto' } };
      const resp = await callScaleDownAPIJSON(body);
      const data = resp && resp.data;
      // Expecting compressed data or JSON fields — try common fields
      const candidate = data && (data.output || data.result || data.response || data.compressed || data.file || data.compressedFile || data.reply);
      if (candidate) {
        // If candidate is base64 string
        if (typeof candidate === 'string' && /^[A-Za-z0-9+/=\s]+$/.test(candidate.trim())) {
          const compressedBuffer = Buffer.from(candidate, 'base64');
          const compressedSize = compressedBuffer.length;
          const ratio = Math.round((1 - compressedSize / originalSize) * 100);
          console.log(`ScaleDown: ${formatBytes(originalSize)} → ${formatBytes(compressedSize)} (${ratio}% reduction)`);
          return { compressedBuffer, originalSize, compressedSize, ratio };
        }
        // If candidate is object with base64
        if (candidate.compressedFile || candidate.file) {
          const b = candidate.compressedFile || candidate.file;
          const compressedBuffer = Buffer.from(b, 'base64');
          const compressedSize = compressedBuffer.length;
          const ratio = Math.round((1 - compressedSize / originalSize) * 100);
          console.log(`ScaleDown: ${formatBytes(originalSize)} → ${formatBytes(compressedSize)} (${ratio}% reduction)`);
          return { compressedBuffer, originalSize, compressedSize, ratio };
        }
      }
      // If we get here, no usable compressed binary — fallthrough to local
    } catch (err) {
      console.error('ScaleDown API image error, falling back to local', err.message || err);
    }
  }

  // Local fallback using sharp
  try {
    if (sharpAvailable) {
      const img = sharp(buffer).resize({ width: 1200, withoutEnlargement: true }).webp({ quality: 60 }).withMetadata({ orientation: undefined });
      const compressedBuffer = await img.toBuffer();
      const compressedSize = compressedBuffer.length;
      const ratio = Math.round((1 - compressedSize / originalSize) * 100);
      console.log(`ScaleDown (local): ${formatBytes(originalSize)} → ${formatBytes(compressedSize)} (${ratio}% reduction)`);
      return { compressedBuffer, originalSize, compressedSize, ratio };
    }
  } catch (err) {
    console.error('Local image compress error', err);
  }

  // Last resort: return original
  return { compressedBuffer: buffer, originalSize, compressedSize: buffer.length, ratio: 0 };
}

async function compressPDF(buffer) {
  const originalSize = buffer.length;
  // Prefer ScaleDown API
  if (SCALEDOWN_KEY) {
    try {
      // Prefer sending extracted text if available
      let text = '';
      if (pdfParseAvailable) {
        const data = await pdfParse(buffer);
        text = data.text || '';
      } else {
        text = buffer.toString('utf8').slice(0, 20000);
      }
      const body = { context: 'Compress and summarize this document for property management use', prompt: text.slice(0, 20000), scaledown: { rate: 'auto' } };
      const resp = await callScaleDownAPIJSON(body);
      const data = resp && resp.data;
      const candidate = data && (data.output || data.result || data.response || data.summary || data.reply);
      if (candidate) {
        const summary = typeof candidate === 'string' ? { summary: candidate } : candidate;
        const compressedJSON = JSON.stringify(summary);
        const compressedSize = Buffer.byteLength(compressedJSON);
        const ratio = Math.round((1 - compressedSize / originalSize) * 100);
        console.log(`ScaleDown: ${formatBytes(originalSize)} → ${formatBytes(compressedSize)} (${ratio}% reduction)`);
        return { summary, originalSize, compressedSize, ratio, extractedText: text.slice(0, 20000) };
      }
    } catch (err) {
      console.error('ScaleDown API pdf error, falling back to local', err.message || err);
    }
  }

  // Local fallback: extract text and return JSON summary
  try {
    let text = '';
    if (pdfParseAvailable) {
      const data = await pdfParse(buffer);
      text = data.text || '';
    } else {
      text = buffer.toString('utf8').slice(0, 20000);
    }

    const lines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
    const sections = {};
    let current = 'Introduction';
    sections[current] = [];
    for (const line of lines) {
      if (/^[A-Z][A-Z\s]{3,}$/.test(line) || /:\s*$/.test(line)) {
        current = line.replace(/[:\s]+$/g, '').slice(0, 50);
        sections[current] = [];
      } else {
        sections[current].push(line);
      }
    }

    const result = {
      summary: Object.fromEntries(Object.entries(sections).map(([k, v]) => [k, v.slice(0, 200).join(' ')])),
      pageCount: Math.max(1, Math.ceil(text.length / 3000)),
      extractedText: text.slice(0, 20000)
    };

    const compressedJSON = JSON.stringify(result);
    const compressedSize = Buffer.byteLength(compressedJSON);
    const ratio = Math.round((1 - compressedSize / originalSize) * 100);
    console.log(`ScaleDown (local): ${formatBytes(originalSize)} → ${formatBytes(compressedSize)} (${ratio}% reduction)`);
    return { ...result, originalSize, compressedSize, ratio };
  } catch (err) {
    console.error('Local PDF compress error', err);
    return { summary: { Introduction: 'Could not extract' }, extractedText: '', originalSize, compressedSize: originalSize, ratio: 0 };
  }
}

async function compressDocument(buffer, mimetype) {
  if (mimetype === 'application/pdf' || mimetype === 'application/x-pdf') return compressPDF(buffer);
  if (mimetype && mimetype.startsWith('image/')) return compressImage(buffer, mimetype);
  // default text fallback
  const str = buffer.toString('utf8');
  const compressed = { summary: { text: str.slice(0, 1000) }, originalSize: buffer.length, compressedSize: Buffer.byteLength(str.slice(0, 1000)), ratio: Math.round((1 - (Buffer.byteLength(str.slice(0, 1000)) / buffer.length)) * 100) };
  console.log(`ScaleDown: ${formatBytes(buffer.length)} → ${formatBytes(compressed.compressedSize)} (${compressed.ratio}% reduction)`);
  return compressed;
}

module.exports = { compressImage, compressPDF, compressDocument };

async function init() {
  if (!SCALEDOWN_KEY) {
    console.warn('⚠️  ScaleDown API key not set — falling back to local compression');
    return { connected: false };
  }

  if (!SCALEDOWN_URL) {
    console.error('❌ ScaleDown API URL not configured');
    return { connected: false };
  }

  const body = { context: 'test', prompt: 'ping', scaledown: { rate: 'auto' } };
  try {
    const resp = await axios.post(SCALEDOWN_URL, body, { headers: { 'x-api-key': SCALEDOWN_KEY, 'Content-Type': 'application/json' }, timeout: 8000 });
    const status = resp && resp.status;
    if (status === 200) {
      console.log(`✅ ScaleDown API connected successfully at ${SCALEDOWN_URL}`);
      return { connected: true };
    }
    if (status === 403) {
      console.error('❌ Invalid API key — check SCALEDOWN_API_KEY in .env');
      return { connected: false };
    }
    if (status === 404) {
      console.error('❌ Wrong endpoint — check SCALEDOWN_API_URL in .env');
      return { connected: false };
    }
    console.error(`❌ ScaleDown API connection failed — status ${status}`);
    return { connected: false };
  } catch (err) {
    const status = err && err.response && err.response.status;
    if (status === 403) {
      console.error('❌ Invalid API key — check SCALEDOWN_API_KEY in .env');
    } else if (status === 404) {
      console.error('❌ Wrong endpoint — check SCALEDOWN_API_URL in .env');
    } else {
      console.error(`❌ ScaleDown API connection failed — ${err.message || err}`);
    }
    return { connected: false };
  }
}

module.exports.init = init;
