.PHONY: test lint check bump install-codex codex-dist

# Install the full Codex layout into the user's home (skills, hooks, defaults).
install-codex:
	python3 tools/generate.py --install

# Regenerate the committed Codex marketplace bundle under .agents/plugins.
# Run after editing any skill, the validator drift check (11) enforces it.
# To dogfood the real install path: `codex plugin marketplace add ./` then
# `codex plugin add nitpickle@nitpickle`.
codex-dist:
	python3 tools/generate.py --codex-dist

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
		for p in map(pathlib.Path, ['.claude-plugin/plugin.json', '.claude-plugin/marketplace.json'])]"
	python3 tools/generate.py --codex-dist
	@grep -h '"version"' .claude-plugin/plugin.json .claude-plugin/marketplace.json
