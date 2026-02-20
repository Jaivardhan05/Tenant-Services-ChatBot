const express = require('express');
const router = express.Router();

router.get('/', (req, res) => {
  res.json({ scaledownEnabled: !!process.env.SCALEDOWN_API_KEY });
});

module.exports = router;
