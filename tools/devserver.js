/* 本地演示服务器：静态托管 design/，并把 /api 代理到后端 8000
   由根目录的「启动本地演示.bat」调用，也可以单独跑：
     node tools/devserver.js */
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 8123;
const ROOT = path.resolve(__dirname, '..', 'design');
const BACKEND = { host: '127.0.0.1', port: 8000 };

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.json': 'application/json; charset=utf-8',
  '.ico': 'image/x-icon',
  '.woff2': 'font/woff2'
};

http.createServer((req, res) => {
  if (req.url.startsWith('/api')) {
    const proxy = http.request(
      { ...BACKEND, path: req.url, method: req.method, headers: req.headers },
      (r) => {
        res.writeHead(r.statusCode, r.headers);
        r.pipe(res);
      }
    );
    proxy.on('error', () => {
      res.writeHead(502, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({ detail: 'backend not running on :8000' }));
    });
    req.pipe(proxy);
    return;
  }

  let rel = decodeURIComponent(req.url.split('?')[0]);
  if (rel === '/' || rel === '') rel = '/home.html';
  const file = path.join(ROOT, path.normalize(rel).replace(/^([/\\])+/, ''));
  if (!file.startsWith(ROOT)) {
    res.writeHead(403).end('forbidden');
    return;
  }
  fs.readFile(file, (err, buf) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('404 ' + rel);
      return;
    }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream' });
    res.end(buf);
  });
}).listen(PORT, '127.0.0.1', () => {
  console.log('frontend: http://127.0.0.1:' + PORT + '  ->  api proxy :8000');
});
