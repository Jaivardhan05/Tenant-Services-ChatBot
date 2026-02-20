const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '..', '.env') });
const express = require('express');
const http = require('http');
const cors = require('cors');
const { Server } = require('socket.io');

const maintenanceRoutes = require('./routes/maintenance');
const chatRoutes = require('./routes/chat');
const configRoutes = require('./routes/config');
const announcementsRoutes = require('./routes/announcements');
const scheduler = require('./services/scheduler');
const scaledown = require('./services/scaledown');
const aiService = require('./services/aiService');

const app = express();
const server = http.createServer(app);

const io = new Server(server, {
  cors: { origin: '*' }
});

app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Attach io to app for routes
app.set('io', io);

app.use('/api/maintenance', maintenanceRoutes);
app.use('/api/chat', chatRoutes);
app.use('/api/config', configRoutes);
app.use('/api/announcements', announcementsRoutes);

app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

const PORT = process.env.PORT || 3001;

server.listen(PORT, () => {
  console.log(`Server listening on ${PORT}`);
});

// Initialize ScaleDown and AI services, then start scheduler
(async function startup(){
  const sdRes = await scaledown.init().catch(()=>({ connected: false }));
  if (sdRes && sdRes.connected) {
    console.log('✅ AI + Compression both powered by ScaleDown API');
  } else {
    console.warn('⚠️ ScaleDown not connected — running in local fallback mode');
  }
  await aiService.init().catch(()=>{});
  scheduler.start();

  // socket handlers (simple)
  io.on('connection', (socket) => {
    console.log('Socket connected', socket.id);
    socket.on('disconnect', (reason) => {
      console.log('Socket disconnected', socket.id, reason);
    });
    socket.on('tenant:message', (payload) => {
      console.log('tenant:message', payload);
    });
  });
})();

// Initialize ScaleDown and AI services, then start scheduler
(async function startup(){
  await scaledown.init().catch(()=>{});
  await aiService.init().catch(()=>{});
  scheduler.start();

  // socket handlers (simple)
  io.on('connection', (socket) => {
    console.log('Socket connected', socket.id);
    socket.on('disconnect', (reason) => {
      console.log('Socket disconnected', socket.id, reason);
    });
    socket.on('tenant:message', (payload) => {
      console.log('tenant:message', payload);
    });
  });
})();
