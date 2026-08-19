.PHONY: test lint check bump install-hooks seed-defaults

# Install the Codex write guardrail (hooks) into the user's home. A Codex plugin
# cannot carry hooks, so run this after `codex plugin add`, then trust with /hooks.
# It also seeds the global defaults.
install-hooks:
	python3 tools/install-hooks.py

# Seed the global default config so any repo inherits it. HARNESS defaults to
# claude, pass HARNESS=codex for Codex. Existing files are kept, add FORCE=1 to
# overwrite. Usage: make seed-defaults [HARNESS=claude|codex] [FORCE=1]
seed-defaults:
	python3 tools/seed_defaults.py --harness $(or $(HARNESS),claude) $(if $(FORCE),--force,)

test:
	python3 -m unittest discover -s hooks -p "test_*.py"
	python3 -m unittest discover -s tools -p "test_*.py"

lint:
	python3 tools/validate.py

check: test lint

# Usage: make bump VERSION=0.1.4
bump:
	@test -n "$(VERSION)" || (echo "usage: make bump VERSION=x.y.z" && exit 1)
	@python3 -c "import re, pathlib; \
		[p.write_text(re.sub(r'\"version\": \"[0-9]+\.[0-9]+\.[0-9]+\"', '\"version\": \"$(VERSION)\"', p.read_text())) \
		for p in map(pathlib.Path, ['.claude-plugin/plugin.json', '.claude-plugin/marketplace.json', '.codex-plugin/plugin.json'])]"
	@grep -h '"version"' .claude-plugin/plugin.json .claude-plugin/marketplace.json .codex-plugin/plugin.json
