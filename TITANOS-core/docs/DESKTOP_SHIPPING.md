# TITANOS Desktop Shipping Stack

TITANOS should ship as one desktop application. Users should not need to open a terminal, run a folder, or know about localhost.

## Runtime Shape

- Electron owns the desktop window.
- The UI loads from packaged app files, not a dev server.
- The Python backend is frozen into a `titanos-backend` executable.
- Electron launches the backend internally on `127.0.0.1:18789`.
- The port is an internal loopback transport, not a user-facing localhost workflow.
- Runtime data is stored in the OS app profile through `TITANOS_DATA_DIR`, not inside the project folder.

## Development Commands

```powershell
npm.cmd install
npm.cmd run desktop
```

`npm.cmd run desktop` opens the app window and starts the Python backend from source.

## Shipping Commands

```powershell
pip install pyinstaller
npm.cmd install
npm.cmd run dist:win
```

The `dist:win` command:

1. Builds `dist/titanos-backend.exe` with PyInstaller.
2. Stages it into `desktop-runtime/backend`.
3. Builds the Windows installer with Electron Builder.

The final installer is written to `release/`.

If the installer builder stalls, the verified unpacked desktop app can still be
run from:

```powershell
release\win-unpacked\TITANOS.exe
```

This unpacked app includes the UI and bundled backend executable. It launches
the backend internally and stores runtime data in the user's app profile.

## Important Product Rule

Do not point users to `http://localhost`. If backend communication is needed, it must be launched and managed internally by the desktop app.

## Production Follow-Ups

- Add code signing certificate for Windows installer trust.
- Add auto-update channel.
- Add app icon assets in `.ico`, `.icns`, and PNG formats.
- Add crash reporting after privacy review.
- Replace mock/local auth and provider storage with production services where required.
- Investigate NSIS installer timeout in CI or a non-sandbox Windows build machine.
