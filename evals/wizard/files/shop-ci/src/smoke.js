// Demo smoke test: checks the payment and webhook settings are present.
for (const k of ['PAYLY_SECRET_KEY', 'HOOKWISE_SIGNING_SECRET']) {
  if (!process.env[k]) { console.error(`missing ${k}`); process.exit(1); }
}
console.log('smoke ok');
