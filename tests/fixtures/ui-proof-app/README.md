# ui-proof fixture app

A deliberately small web app used to dogfood the `ui-proof` skill. It serves two
states from one server, reachable by route, so a single Playwright `webServer`
boot can prove both.

## Routes

- `/` clean flow. A successful same-origin request, valid alt text, no thrown
  errors. The skill should find zero Findings here.
- `/broken` seeded-defect flow. It triggers the Proof-complete defect classes
  the skill asserts:
  - an uncaught exception during load
  - an unhandled promise rejection
  - a same-origin 5xx (`GET /api/boom`)
  - a dead link to a 404 route
  - two axe violations (an image with no alt text, a button with no accessible
    name)
- `/api/ok` returns 200. `/api/boom` returns 500.

## Run it

From this directory:

```
npx playwright install chromium   # first run only
npx playwright test
```

Playwright boots `node server.js` through the `webServer` block, runs
`smoke.spec.ts`, and tears the server down. Both tests pass. The clean test
asserts no error signal, the broken test asserts the seeded signals appear.

## Where this runs

These are browser dogfood runs, not part of `make check`. `make check` proves the
static skill contract (the validator and the hook unit tests) and never launches
a browser. Run the fixture locally during development, and optionally in a
dedicated CI lane built on a Playwright image so the browser is preinstalled.
Keep it off the default Python test path.
