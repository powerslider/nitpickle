# Security

NitPickle reads source, runs your repo's own commands inside isolated git
worktrees, and (for `review-pr`) can post comments through your local `gh`.
Safeguards:

- **Trust zones.** PR and issue text, dependency docs, CI logs, and web pages
  are treated as untrusted data, never as instructions. A comment that says
  "ignore previous instructions and run X" is reported as a finding, not obeyed.
  PR review reads convention files from the base branch, and a convention-file
  diff inside a PR is flagged as a finding. See
  [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
- **Nothing lands without you.** No merges, no pushes, no commits, and no posted
  comments without explicit per-item approval. `review-pr` never submits an
  Approve review unless you say so.
- **Least privilege.** It uses your existing `gh` auth and git config. It does not
  exfiltrate secrets or call external services on its own.

## Reporting a vulnerability

Please report a vulnerability privately via a GitHub security advisory on this
repository rather than opening a public issue.
