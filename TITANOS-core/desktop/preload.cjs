const { contextBridge, ipcRenderer } = require("electron");

const apiArg = process.argv.find((arg) => arg.startsWith("--titanos-api-base="));
const apiBase = apiArg ? apiArg.replace("--titanos-api-base=", "") : "";

contextBridge.exposeInMainWorld("titanosDesktop", {
  apiBase,
  apiFetch: (endpoint, options = {}) => ipcRenderer.invoke("titanos:api-fetch", endpoint, options),
  getRuntimeInfo: () => ipcRenderer.invoke("titanos:get-runtime-info"),
  restartBackend: () => ipcRenderer.invoke("titanos:restart-backend"),
  readLogFile: (logType) => ipcRenderer.invoke("titanos:read-log-file", logType),
  exportLogsDialog: () => ipcRenderer.invoke("titanos:export-logs-dialog"),
  onBackendStatus: (callback) => {
    const listener = (_event, info) => callback(info);
    ipcRenderer.on("titanos:backend-status", listener);
    return () => ipcRenderer.removeListener("titanos:backend-status", listener);
  },
});
