const cron = require('node-cron');
const store = require('../models/inMemoryStore');
const notificationService = require('./notificationService');

function start() {
  // Runs every day at 9:00
  cron.schedule('0 9 * * *', async () => {
    const now = Date.now();
    for (const p of store.payments) {
      const due = new Date(p.dueDate).getTime();
      const diff = Math.ceil((due - now) / (24 * 3600 * 1000));
      if (diff === 3 && p.status === 'due') {
        const tenant = store.tenants.find(t => t.id === p.tenantId);
        const msg = `Reminder: Unit ${tenant.unit} - $${p.amount} due in 3 days`;
        console.log(`Reminder sent to ${tenant.unit} - $${p.amount} due in 3 days`);
        await notificationService.sendReminder(tenant.email, 'Rent due in 3 days', msg);
      }
    }
  }, { timezone: process.env.TZ || 'UTC' });
}

module.exports = { start };
