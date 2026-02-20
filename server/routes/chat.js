const express = require('express');
const scaledown = require('../services/scaledown');
const aiService = require('../services/aiService');
const store = require('../models/inMemoryStore');

const router = express.Router();

router.post('/', async (req, res) => {
  try {
    const { message, sessionId, tenantId } = req.body;
    const result = await aiService.handleMessage({ message, sessionId, tenantId });

    // If lease intent, attach compressed lease summary (simulate)
    if (result.intent === 'lease') {
      const sampleLease = Buffer.from('Sample lease content for ' + (tenantId || 'tenant'));
      const pdfResult = await scaledown.compressPDF(sampleLease);
      result.leaseSummary = pdfResult.summary;
    }

    // emit via socket if available
    const io = req.app.get('io');
    if (io) io.emit('bot:reply', { sessionId: result.sessionId || sessionId, ...result });

    res.json({ ok: true, ...result });
  } catch (err) {
    console.error(err);
    res.status(500).json({ ok: false, error: 'Chat failed' });
  }
});

module.exports = router;
