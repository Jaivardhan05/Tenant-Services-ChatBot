const express = require('express');
const store = require('../models/inMemoryStore');

const router = express.Router();

router.get('/', (req, res) => {
  try {
    res.json({ ok: true, announcements: store.announcements });
  } catch (err) {
    console.error('Failed to get announcements', err);
    res.status(500).json({ ok: false, error: 'Could not fetch announcements' });
  }
});

module.exports = router;
