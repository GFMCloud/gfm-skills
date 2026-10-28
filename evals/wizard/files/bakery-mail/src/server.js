// Demo order server.
require('dotenv').config();
const http = require('http');
http.createServer((req, res) => res.end('Crumb & Co (demo)')).listen(process.env.PORT || 3000);
