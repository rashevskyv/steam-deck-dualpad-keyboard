# Steam Native Keyboard Prototype

This branch contains an experimental prototype that uses the Steam native on-screen keyboard. It is separate from the dualpad keyboard implementation on `main`.

The Millennium layout plugin and its integration have **not had visual verification in Steam**. Treat the current behavior and layout as a work in progress; visual fit, focus behavior, and interaction details may change.

## Source files

The prototype includes `addon.js`, the Millennium plugin definition and Lua backend, and helper scripts for the tray, KWin window positioning, and user-scoped loader setup. The loader setup script refers to runtime dependencies in an unversioned local `millennium-runtime/` directory. That directory and the packaged `.star` plugin are intentionally not included in this branch, so `install-user-loader.sh` is not a ready-to-run general installer. Review and adapt the scripts and obtain a compatible Millennium build through its official project before considering local setup.

Millennium is a community project for Steam Client themes and plugins; it is not a Valve or Steam feature. See the [official Millennium project](https://github.com/SteamClientHomebrew/Millennium). Steam client or runtime updates can change internal UI behavior and may break this prototype. Recheck compatibility after Steam updates before relying on it.

No Steam installation, configuration, or restart is performed by publishing this source branch.
