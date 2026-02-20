const nodemailer = require('nodemailer');

async function sendReminder(to, subject, body) {
  if (!process.env.SMTP_HOST) {
    console.log(`Email stub: to=${to} subject=${subject} body=${body}`);
    return;
  }

  const transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST,
    port: process.env.SMTP_PORT || 587,
    auth: process.env.SMTP_USER ? { user: process.env.SMTP_USER, pass: process.env.SMTP_PASS } : undefined
  });

  await transporter.sendMail({ from: process.env.SMTP_FROM || 'no-reply@example.com', to, subject, text: body });
}

module.exports = { sendReminder };
