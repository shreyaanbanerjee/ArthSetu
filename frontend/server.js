const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 3000;
const PUBLIC_DIR = path.join(__dirname, 'public');
const STATIC_DIR = path.join(__dirname, '.next', 'static');
const APP_DIR = path.join(__dirname, '.next', 'server', 'app');

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff2': 'font/woff2',
  '.woff': 'font/woff',
  '.ttf': 'font/ttf',
};

const server = http.createServer((req, res) => {
  let urlPath = req.url.split('?')[0];

  if (urlPath === '/' || urlPath === '') {
    const indexPath = path.join(APP_DIR, 'index.html');
    if (fs.existsSync(indexPath)) {
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      return fs.createReadStream(indexPath).pipe(res);
    }
  }

  if (urlPath.startsWith('/_next/static/')) {
    const rel = urlPath.replace('/_next/static/', '');
    const filePath = path.join(STATIC_DIR, rel);
    if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
      const ext = path.extname(filePath);
      res.writeHead(200, { 'Content-Type': MIME_TYPES[ext] || 'application/octet-stream', 'Cache-Control': 'public, max-age=31536000, immutable' });
      return fs.createReadStream(filePath).pipe(res);
    }
  }

  const pubPath = path.join(PUBLIC_DIR, urlPath);
  if (fs.existsSync(pubPath) && fs.statSync(pubPath).isFile()) {
    const ext = path.extname(pubPath);
    res.writeHead(200, { 'Content-Type': MIME_TYPES[ext] || 'application/octet-stream' });
    return fs.createReadStream(pubPath).pipe(res);
  }

  // Check sub-routes like /score, /schemes, /educator
  const subHtml = path.join(APP_DIR, `${urlPath.replace(/^\//, '')}.html`);
  if (fs.existsSync(subHtml) && fs.statSync(subHtml).isFile()) {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    return fs.createReadStream(subHtml).pipe(res);
  }

  // SPA fallback
  const fallbackIndex = path.join(APP_DIR, 'index.html');
  if (fs.existsSync(fallbackIndex)) {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    return fs.createReadStream(fallbackIndex).pipe(res);
  }

  res.writeHead(404, { 'Content-Type': 'text/plain' });
  res.end('Not found');
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`ArthSetu Frontend running at http://localhost:${PORT}`);
});
