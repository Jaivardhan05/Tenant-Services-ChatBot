const express = require('express');
const multer = require('multer');
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const scaledown = require('../services/scaledown');
const store = require('../models/inMemoryStore');

const router = express.Router();
const maxMb = parseInt(process.env.MAX_FILE_SIZE_MB || '10', 10);
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: maxMb * 1024 * 1024 }, fileFilter: (req, file, cb) => {
  if (!file.mimetype.startsWith('image/')) return cb(new Error('Only image uploads are supported'));
  cb(null, true);
}});

function detectPriority(text) {
  const urgentKeywords = ['flood', 'fire', 'gas', 'electrocution', 'explosion'];
  const low = urgentKeywords.every(k => !text.toLowerCase().includes(k));
  return low ? 'normal' : 'urgent';
}

// POST /api/maintenance
router.post('/', upload.single('photo'), async (req, res) => {
  try {
    const { tenantId, category, description } = req.body;
    const tenant = store.tenants.find(t => t.id === tenantId) || { unit: 'Unknown' };
    let photoPath = null;
    if (req.file) {
      try {
        const { compressedBuffer, originalSize, compressedSize, ratio } = await scaledown.compressImage(req.file.buffer, req.file.mimetype);
        const filename = `${uuidv4()}.webp`;
        const uploadDir = path.join(__dirname, '..', 'uploads');
        if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir, { recursive: true });
        const fullPath = path.join(uploadDir, filename);
        fs.writeFileSync(fullPath, compressedBuffer);
        photoPath = `/uploads/${filename}`;
      } catch (imgErr) {
        console.error('Image compress failed', imgErr);
        return res.status(500).json({ ok: false, error: 'Image compression failed' });
      }
    }

    const priority = detectPriority(description || '');
    const mr = { id: uuidv4(), tenantId, unit: tenant.unit, category, description, status: 'pending', priority, photoPath, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() };
    store.maintenanceRequests.push(mr);
    res.json({ ok: true, request: mr });
  } catch (err) {
    console.error(err);
    if (err && err.message && err.message.includes('File too large')) return res.status(413).json({ ok: false, error: 'File too large' });
    res.status(500).json({ ok: false, error: 'Could not create request' });
  }
});

// GET /api/maintenance/:tenantId
router.get('/:tenantId', (req, res) => {
  const { tenantId } = req.params;
  const list = store.maintenanceRequests.filter(r => r.tenantId === tenantId);
  res.json({ ok: true, list });
});

// PATCH /api/maintenance/:id/status
router.patch('/:id/status', (req, res) => {
  const { id } = req.params;
  const { status } = req.body;
  const reqItem = store.maintenanceRequests.find(r => r.id === id);
  if (!reqItem) return res.status(404).json({ ok: false, error: 'Not found' });
  reqItem.status = status;
  reqItem.updatedAt = new Date().toISOString();
  res.json({ ok: true, request: reqItem });
});

module.exports = router;
