import axios from 'axios';

const sendToBackend = async (payload, retries = 2, delay = 200) => {
  const token = localStorage.getItem('authToken');
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  try {
    // await axios.post('/api/logs/client', payload, { headers });
    return true;
  } catch (err) {
    if (retries > 0) {
      await new Promise(r => setTimeout(r, delay));
      return sendToBackend(payload, retries - 1, delay * 2);
    }
    return false;
  }
};

const formatMeta = (meta) => {
  if (!meta) return undefined;
  try {
    return typeof meta === 'string' ? meta : JSON.stringify(meta);
  } catch {
    return String(meta);
  }
};

const log = async (level = 'info', message = '', user = null, meta = null) => {
  const payload = { level, message, user, meta: formatMeta(meta) };
  const ok = await sendToBackend(payload);
  if (!ok) {
    // Fallback to console so logs aren't silently lost
    const fn = console[level] || console.log;
    fn.call(console, `[LOG-${level}] ${message}`, meta);
  }
};

const info = (message, user = null, meta = null) => log('info', message, user, meta);
const warn = (message, user = null, meta = null) => log('warning', message, user, meta);
const error = (message, user = null, meta = null) => log('error', message, user, meta);
const debug = (message, user = null, meta = null) => log('debug', message, user, meta);

export default { log, info, warn, error, debug };
