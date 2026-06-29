.PHONY: test lint check bump install-codex codex-dogfood

# Install the Codex layout into the user's home (skills, hooks, defaults).
install-codex:
	python3 tools/generate.py --install

# Generate a gitignored repo-local Codex layout for dogfooding with real codex.
codex-dogfood:
	python3 tools/generate.py .agents/skills
	python3 -c "import sys; sys.path.insert(0,'tools'); import generate, os; generate.generate_hooks_config('.', '.codex')"
	@echo "generated .agents/skills and .codex/hooks.json (gitignored)"

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
	@grep -h '"version"' .claude-plugin/plugin.json .claude-plugin/marketplace.json
