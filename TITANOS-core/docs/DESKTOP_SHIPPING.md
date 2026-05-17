# TITANOS Desktop Shipping Stack

TITANOS should ship as one desktop application. Users should not need to open a terminal, run a folder, or know about localhost.

TITANOS is an open-source, plug-and-play local workspace. The desktop product
does not require a product login. Users can customize workspace mode, technical
level, visible tools, and providers on first launch.

## Runtime Shape

- Electron owns the desktop window.
- The UI loads from packaged app files, not a dev server.
- The canonical desktop UI is the staged React build from `../titanos-ui/dist`,
  copied into `TITANOS-core/desktop-ui/`.
- `TITANOS-core/ui/` remains a temporary fallback until React parity is complete.
- The Python backend is frozen into a `titanos-backend` executable.
- Electron launches the backend internally on `127.0.0.1:18789`.
- The port is an internal loopback transport, not a user-facing localhost workflow.
- If the default internal port is busy, Electron selects the next available port
  and passes it to the UI through the preload bridge.
- Runtime data is stored in the OS app profile through `TITANOS_DATA_DIR`, not inside the project folder.
- Backend status, log paths, and data paths are exposed to the UI through
  `window.titanosDesktop.getRuntimeInfo()`.

## Development Commands

```powershell
npm.cmd install
npm.cmd run ui:desktop
npm.cmd run desktop
```

`npm.cmd run ui:desktop` builds and stages the canonical React UI. `npm.cmd run desktop` opens the app window and starts the Python backend from source.

## Shipping Commands

```powershell
pip install pyinstaller
npm.cmd install
npm.cmd run dist:win
```

The `dist:win` command:

1. Builds and stages the React UI into `desktop-ui/`.
2. Builds `dist/titanos-backend.exe` with PyInstaller.
3. Stages it into `desktop-runtime/backend`.
4. Writes `desktop-runtime/backend/backend-manifest.json` with size and SHA-256.
5. Starts the staged backend executable and verifies `/readyz` plus `/runtime`.
6. Builds the Windows installer with Electron Builder.

The final installer is written to `release/`.

If the installer builder stalls, the verified unpacked desktop app can still be
run from:

```powershell
release\win-unpacked\TITANOS.exe
```

This unpacked app includes the UI and bundled backend executable. It launches
the backend internally and stores runtime data in the user's app profile.

## Smoke Gates

Use the fast source smoke while iterating on backend runtime behavior:

```powershell
python scripts/run.py desktop-smoke
```

Use the staged executable smoke after `npm.cmd run backend:bundle` and
`npm.cmd run desktop:stage-backend`:

```powershell
npm.cmd run backend:smoke
```

Both smoke checks require desktop mode to report `mode: desktop`, bind only to
`127.0.0.1`, and write runtime data to a temporary profile directory.

## Important Product Rule

Do not point users to `http://localhost`. If backend communication is needed, it must be launched and managed internally by the desktop app.

Do not add a product login screen to the desktop app. Sensitive backend actions
must stay protected through local command approvals, internal desktop runtime
identity, and loopback-only API access.

## Production Follow-Ups

- Add code signing certificate for Windows installer trust.
- Add auto-update channel.
- Add app icon assets in `.ico`, `.icns`, and PNG formats.
- Add crash reporting after privacy review.
- Replace mock/local auth and provider storage with production services where required.
- Investigate NSIS installer timeout in CI or a non-sandbox Windows build machine.

## Windows Manual QA Checklist

Follow this checklist to manually verify desktop product readiness on Windows:

### 1. Zero-Config Onboarding
- Run `npm run ui:desktop && npm run desktop` in a clean environment.
- Confirm the app bypasses any traditional SaaS login/signup flow and boots directly into the local onboarding screens.
- Advance through workspace and operator customization screens (e.g., Coding Workspace, Developer experience level).
- Verify completing setup redirects immediately to the Operator Workspace with the `titanos_onboarded` preference stored locally.

### 2. Live Backend Status & Reconnect
- Launch the Electron app with the backend online. Check the top navbar for a **Connected** badge with a green dot and subtle glow.
- Simulate a backend offline event (e.g., terminate python backend process).
- Confirm the badge switches to **Backend Offline** with a red dot and displays a **Retry** button.
- Click **Retry** to invoke the Electron `window.titanosDesktop.restartBackend()` API and confirm reconnect returns the badge to green.

### 3. API Providers & Connection Testing
- Open **Settings** (Operator Control) and navigate to **API Providers**.
- Click **Add Provider** and fill out the endpoint details (e.g., OpenAI/Anthropic/Local).
- Click **Test Connection** to execute the connection validation via `POST /providers/config/{provider_id}/test`.
- Save the provider and verify the key is immediately masked (e.g. `sk-...`). **CRITICAL**: Refresh or inspect the DOM to ensure raw credentials are never rendered or returned.

### 4. Risk-Based Command Approvals
- Propose a command requiring environment modification (e.g., write a new code script or invoke pip).
- Navigate to **Command Approvals** in Settings.
- Verify the proposed action is listed in the **PENDING** view, detailing the command string, proposed risk, and safety justification.
- Click **Approve & Execute** to trigger `POST /hands/approvals/{id}/approve` and verify the execution summary completes.

### 5. Persistent Run History
- Perform several agent execution goals.
- Open **Run History** under Settings and select a run.
- Confirm the detail card loads SQLite-backed run details: Original Goal, System Routing, routing confidence, routing justification, execution duration, and produced artifacts paths.

### 6. Append-Only Audit Logs
- Perform actions across systems to write audit events.
- Open the **Audit Events** tab. Filter logs using the text search input.
- Check that logs accurately list event timestamps, actor types, and meta event payloads (rendered as cleanly formatted JSON).

### 7. Secure Backup & File Restores
- Trigger an agent file edit to force an automatic pre-modification backup.
- Go to the **Backup & Restore** settings tab.
- Click **Restore** on the backup. Verify the warning dialog renders: *"WARNING: Restoring this file will overwrite the current live copy... Proceed?"*
- Click **Confirm Overwrite** to dispatch the `POST /hands/backups/{id}/restore` endpoint and verify the success notification.

### 8. Telemetry & Export Diagnostics
- Navigate to the **Diagnostics** tab.
- Verify Mode reports `DESKTOP`, Environment reports `production`, and Database Connected displays `Yes`.
- Confirm local resolved directories (Data, Log, DB paths) are fully populated.
- Click **Export Diagnostics** to package a redacted zip diagnostic bundle. Verify the target output path and size.
