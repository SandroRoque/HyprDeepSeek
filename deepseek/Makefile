# DeepSeek rate whale for Waybar (Omarchy / Arch)

.PHONY: install uninstall font check

install:
	./install.sh

uninstall:
	./install.sh uninstall

# regenerate resources/DeepSeekWhale.ttf from resources/whale.path
font:
	python3 lib/build-font.py

# sanity-check the resources without touching the user's config
check:
	@bash -n resources/deepseek-price && echo "  deepseek-price syntax OK"
	@resources/deepseek-price json | jq -e '.tooltip and .class' >/dev/null \
		&& echo "  json contract OK" || { echo "  json contract BROKEN"; exit 1; }
	@echo "  state: $$(resources/deepseek-price state)  next: $$(resources/deepseek-price next) UTC"
