const { v4: uuidv4 } = require('uuid');

const tenants = [
  { id: 'T001', name: 'Alice Park', unit: '1A', email: 'alice@example.com', leaseEnd: '2026-08-31', balance: 1250 },
  { id: 'T002', name: 'Ben Turner', unit: '1B', email: 'ben@example.com', leaseEnd: '2025-11-30', balance: 0 },
  { id: 'T003', name: 'Carmen Diaz', unit: '2A', email: 'carmen@example.com', leaseEnd: '2026-03-15', balance: 300 },
  { id: 'T004', name: 'David Lee', unit: '2B', email: 'david@example.com', leaseEnd: '2027-01-01', balance: 600 },
  { id: 'T005', name: 'Eve Martin', unit: '3C', email: 'eve@example.com', leaseEnd: '2025-12-01', balance: 0 }
];

const maintenanceRequests = [
  { id: uuidv4(), tenantId: 'T001', unit: '1A', category: 'Plumbing', description: 'Leaky faucet in kitchen', status: 'pending', priority: 'normal', photoPath: null, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() },
  { id: uuidv4(), tenantId: 'T003', unit: '2A', category: 'Electrical', description: 'Power outage in living room', status: 'in-progress', priority: 'urgent', photoPath: null, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() },
  { id: uuidv4(), tenantId: 'T004', unit: '2B', category: 'HVAC', description: 'AC not cooling', status: 'pending', priority: 'normal', photoPath: null, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() }
];

const payments = [
  { tenantId: 'T001', amount: 1250, dueDate: new Date(Date.now() + 3 * 24 * 3600 * 1000).toISOString(), status: 'due', paidAt: null },
  { tenantId: 'T003', amount: 1500, dueDate: new Date(Date.now() + 7 * 24 * 3600 * 1000).toISOString(), status: 'due', paidAt: null }
];

const amenityBookings = [];

const announcements = [
  { id: uuidv4(), title: 'Pool Maintenance', body: 'Pool will be closed this Friday for maintenance.', createdAt: new Date().toISOString() },
  { id: uuidv4(), title: 'Package Policy Update', body: 'Packages will be held for 7 days.', createdAt: new Date().toISOString() },
  { id: uuidv4(), title: 'Holiday Party', body: 'Join us in the lobby on Dec 20 for a community party.', createdAt: new Date().toISOString() }
];

const chatSessions = {};

const buildingPolicies = {
  smoking: 'No smoking anywhere inside the building',
  quietHours: 'Quiet hours 10pm-8am',
  pets: 'Pets allowed with registration and deposit',
  parking: 'Guest parking in lot B during daytime'
};

const faq = [
  { q: 'When is rent due?', a: 'Rent is due on the 1st of every month.' },
  { q: 'How do I submit maintenance?', a: 'Use the maintenance form or chat with the bot.' },
  { q: 'How do I renew my lease?', a: 'Contact leasing office 60 days before lease end.' }
];

module.exports = {
  tenants,
  maintenanceRequests,
  payments,
  amenityBookings,
  announcements,
  chatSessions,
  buildingPolicies,
  faq
};
