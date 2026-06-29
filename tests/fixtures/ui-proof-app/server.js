const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");

const PORT = Number(process.env.UI_PROOF_PORT) || 4317;
const PUBLIC = path.join(__dirname, "public");

function send(res, status, type, body) {
  res.writeHead(status, { "Content-Type": type });
  res.end(body);
}

function serveFile(res, file) {
  fs.readFile(path.join(PUBLIC, file), (err, data) => {
    if (err) {
      send(res, 404, "text/plain", "not found");
      return;
    }
    send(res, 200, "text/html; charset=utf-8", data);
  });
}

// Routes give one app both a clean state and a seeded-defect state without a
// reboot, so a single webServer boot can prove both. Defect classes match the
// ui-proof assertion bar: page error, unhandled rejection, same-origin 5xx,
// dead link, axe violations.
const server = http.createServer((req, res) => {
  const url = req.url.split("?")[0];
  switch (url) {
    case "/":
      return serveFile(res, "index.html");
    case "/broken":
      return serveFile(res, "broken.html");
    case "/api/ok":
      return send(res, 200, "application/json", JSON.stringify({ ok: true }));
    case "/api/boom":
      return send(res, 500, "application/json", JSON.stringify({ error: "seeded 500" }));
    default:
      return send(res, 404, "text/plain", "not found");
  }
});

server.listen(PORT, "127.0.0.1", () => {
  process.stdout.write(`ui-proof fixture listening on ${PORT}\n`);
});
