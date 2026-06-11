.PHONY: test lint check bump

test:
	python3 -m unittest discover -s hooks -p "test_*.py"

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
