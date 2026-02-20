const axios = require('axios');
const store = require('../models/inMemoryStore');
const { v4: uuidv4 } = require('uuid');

const sessions = store.chatSessions; // persistent in-memory

function detectIntent(text) {
  const t = text.toLowerCase();
  if (/(leak|flood|fire|gas|broken|not working)/.test(t)) return 'maintenance';
  if (/(rent|pay|balance|due)/.test(t)) return 'payment';
  if (/(lease|agreement|term|renew)/.test(t)) return 'lease';
  if (/(book|amenit|pool|gym|parking)/.test(t)) return 'amenity';
  if (/(announce|notice|party|event)/.test(t)) return 'announcement';
  return 'general';
}

async function handleMessage({ message, sessionId, tenantId }) {
  const sid = sessionId || uuidv4();
  if (!sessions[sid]) sessions[sid] = [];
  sessions[sid].push({ role: 'user', message, at: new Date().toISOString() });

  const intent = detectIntent(message);
  let reply = '';
  const suggestedActions = [];
  // Simple rule-based replies augmented with FAQ/policies (keep logic for suggestedActions/intents)
  if (intent === 'maintenance') {
    reply = 'I can help with that. Please provide a short description and a photo if available.';
    suggestedActions.push({ label: 'Open Maintenance Form', action: 'open_maintenance' });
  } else if (intent === 'payment') {
    const tenant = store.tenants.find(t => t.id === tenantId) || {};
    reply = `Your current balance is $${tenant.balance || 0}. You can pay via the Payments panel.`;
    suggestedActions.push({ label: 'Pay Rent', action: 'open_payments' });
  } else if (intent === 'lease') {
    reply = 'I can fetch your lease summary. One moment while I retrieve a compressed version of your lease.';
    suggestedActions.push({ label: 'View Lease', action: 'view_lease' });
  } else if (intent === 'amenity') {
    reply = 'Which amenity would you like to book? (Pool, Gym, Guest room)';
    suggestedActions.push({ label: 'Book Amenity', action: 'open_amenity' });
  } else if (intent === 'announcement') {
    const latest = store.announcements.slice(-3);
    reply = 'Here are the latest announcements:\n' + latest.map(a => `- ${a.title}: ${a.body}`).join('\n');
  } else {
    // search FAQ
    const found = store.faq.find(f => message.toLowerCase().includes(f.q.split(' ')[0].toLowerCase()));
    reply = found ? found.a : "I'm happy to help — can you provide more detail?";
  }

  // Build a single prompt string from conversation history (include latest message)
  const convoMsgs = sessions[sid].map(m => `${m.role.toUpperCase()}: ${m.message}`).join('\n');
  const promptString = convoMsgs + '\nUSER: ' + message;

  const scaledownKey = process.env.SCALEDOWN_API_KEY;
  const scaledownUrl = process.env.SCALEDOWN_API_URL;
  const systemContext = `You are a helpful tenant services assistant for ${process.env.PROPERTY_NAME || 'Property'} apartments. You help with maintenance requests, rent questions, lease terms, amenity bookings, and community announcements. Be friendly, concise, and professional.`;

  // Call ScaleDown endpoint if configured
  if (scaledownKey && scaledownUrl) {
    try {
      const body = { context: systemContext, prompt: promptString, scaledown: { rate: 'auto' } };
      const resp = await axios.post(scaledownUrl, body, { headers: { 'x-api-key': scaledownKey, 'Content-Type': 'application/json' }, timeout: 20000 });
      const data = resp && resp.data;

      // Log full response once for inspection
      if (!global.__SCALEDOWN_FULL_RESPONSE_LOGGED__) {
        try { console.log('ScaleDown full response (first call):', JSON.stringify(data)); } catch(e){ console.log('ScaleDown full response (first call):', data); }
        global.__SCALEDOWN_FULL_RESPONSE_LOGGED__ = true;
      }

      // Extract reply from common fields
      let extracted = null;
      if (!data) extracted = null;
      else if (typeof data === 'string') extracted = data;
      else if (data.output) extracted = data.output;
      else if (data.result) extracted = data.result;
      else if (data.response) extracted = data.response;
      else if (data.reply) extracted = data.reply;
      else if (data.message && data.message.content) extracted = data.message.content;
      else if (data.choices && data.choices[0]) extracted = (data.choices[0].message && data.choices[0].message.content) || data.choices[0].text;

      if (extracted) {
        reply = Array.isArray(extracted) ? extracted.join('\n') : String(extracted);
      }
    } catch (err) {
      console.error('ScaleDown chat call failed, using local reply:', err && err.response && err.response.status, err.message || err);
    }
  }

  const botMessage = { role: 'bot', message: reply, at: new Date().toISOString(), intent, suggestedActions };
  sessions[sid].push(botMessage);

  return { sessionId: sid, reply, intent, suggestedActions };
}

module.exports = { handleMessage };

async function init() {
  const scaledownKey = process.env.SCALEDOWN_API_KEY;
  const scaledownUrl = process.env.SCALEDOWN_API_URL;
  if (!scaledownKey || !scaledownUrl) {
    console.warn('⚠️ ScaleDown chat endpoint not configured — AI will use local responses');
    return { connected: false };
  }

  const body = { context: `test`, prompt: 'ping', scaledown: { rate: 'auto' } };
  try {
    const resp = await axios.post(scaledownUrl, body, { headers: { 'x-api-key': scaledownKey, 'Content-Type': 'application/json' }, timeout: 8000 });
    const status = resp && resp.status;
    if (status === 200) {
      console.log(`✅ ScaleDown chat endpoint reachable at ${scaledownUrl}`);
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
    console.warn(`ScaleDown chat endpoint test returned status ${status}`);
  } catch (err) {
    const status = err && err.response && err.response.status;
    if (status === 403) console.error('❌ Invalid API key — check SCALEDOWN_API_KEY in .env');
    else if (status === 404) console.error('❌ Wrong endpoint — check SCALEDOWN_API_URL in .env');
    else console.warn('❌ ScaleDown chat endpoint test failed —', err.message || err);
  }
  return { connected: false };
}

module.exports.init = init;
