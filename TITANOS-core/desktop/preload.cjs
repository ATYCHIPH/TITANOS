const { contextBridge, ipcRenderer } = require("electron");

const apiArg = process.argv.find((arg) => arg.startsWith("--titanos-api-base="));
const apiBase = apiArg ? apiArg.replace("--titanos-api-base=", "") : "http://127.0.0.1:18789";

contextBridge.exposeInMainWorld("titanosDesktop", {
  apiBase,
  getRuntimeInfo: () => ipcRenderer.invoke("titanos:get-runtime-info"),
});
