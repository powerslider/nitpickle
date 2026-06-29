import { defineConfig } from "@playwright/test";

const PORT = Number(process.env.UI_PROOF_PORT) || 4317;

// retries 0 keeps proof runs honest: a red must be deterministic on its own,
// not papered over by a retry. The ui-proof determinism gate runs the spec N
// times rather than relying on Playwright retries.
export default defineConfig({
  testDir: ".",
  retries: 0,
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
  },
  webServer: {
    command: "node server.js",
    url: `http://127.0.0.1:${PORT}/`,
    reuseExistingServer: !process.env.CI,
    env: { UI_PROOF_PORT: String(PORT) },
  },
});
