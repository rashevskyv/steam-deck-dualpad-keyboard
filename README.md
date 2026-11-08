# Steam Deck DualPad Keyboard

An experimental on-screen keyboard for Steam Deck with dual trackpad input, swipe typing, word suggestions, and configurable layouts.

## Status

This project is under active development. It has not been packaged as a stable release, and behavior may change. Hardware-specific input and display behavior should be considered experimental.

## Install

The scripts target SteamOS and rely on its desktop environment, Python GTK bindings, `evdev`, and related system services. Review `start.sh` before running it and adapt dependencies or permissions for your setup. `config/config.example.json` and the layouts/locales under `config/` are examples and defaults; runtime configuration is ignored by Git.

## Upstream attribution

This repository is based on [better-handheld-keyboard](https://github.com/AdamLovattDevOps/better-handheld-keyboard). The upstream MIT license is preserved in [LICENSE](LICENSE). This fork adds dual trackpad input and related experimental behavior.
