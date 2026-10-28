// Sends order confirmations through PostLark (demo).
require('dotenv').config();
const { PostLark } = require('postlark-node');

const client = new PostLark({ apiKey: process.env.POSTLARK_API_KEY });

async function sendOrderConfirmation(order) {
  return client.send({
    from: process.env.MAIL_FROM,
    to: order.email,
    subject: `Your Crumb & Co order ${order.id}`,
    text: `Thanks! Collect from ${order.pickupTime}.`,
  });
}

module.exports = { sendOrderConfirmation };
