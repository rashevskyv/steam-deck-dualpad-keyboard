# Steam Native Keyboard Prototype

This branch contains an experimental prototype that uses the Steam native on-screen keyboard. It is separate from the dualpad keyboard implementation on `main`.

The Millennium plugin is loaded, but its actual appearance is still **awaiting user verification**. Treat this experimental behavior and layout as work in progress; visual fit, focus behavior, and interaction details may change.

## Source files

The prototype includes `addon.js`, the Millennium plugin definition and Lua backend, `build_plugin.py`, and helper scripts for the tray, KWin window positioning, and user-scoped loader setup. `build_plugin.py` derives Steam bundle patches from a local Steam UI bundle and the addon source. The loader setup script refers to runtime dependencies in an unversioned local `millennium-runtime/` directory. That directory and the packaged `.star` plugin are intentionally not included in this branch, so `install-user-loader.sh` is not a ready-to-run general installer. Review and adapt the scripts and obtain a compatible Millennium build through its official project before considering local setup.

Millennium is a community project for Steam Client themes and plugins; it is not a Valve or Steam feature. See the [official Millennium project](https://github.com/SteamClientHomebrew/Millennium). Steam client or runtime updates can change internal UI behavior and may break this prototype. Recheck compatibility after Steam updates before relying on it.

No Steam installation, configuration, or restart is performed by publishing this source branch.
