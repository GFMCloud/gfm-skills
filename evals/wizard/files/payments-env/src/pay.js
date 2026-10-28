// Demo payment setup: reads keys from the environment (dotenv loads .env).
require('dotenv').config();
const cfg = {
  publishable: process.env.PAYLY_PUBLISHABLE_KEY,
  secret: process.env.PAYLY_SECRET_KEY,
  webhookSecret: process.env.PAYLY_WEBHOOK_SECRET,
};
if (!cfg.secret || !cfg.webhookSecret) { console.error('Payly keys missing'); process.exit(1); }
console.log('payments configured');
