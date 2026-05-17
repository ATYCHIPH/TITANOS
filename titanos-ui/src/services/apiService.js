const desktopBridge = window.titanosDesktop || {};

class ApiService {
  constructor() {
    this.apiBaseUrl = desktopBridge.apiBase || import.meta.env.VITE_TITANOS_API_BASE || '';
  }

  async getApiBaseUrl() {
    if (this.apiBaseUrl) return this.apiBaseUrl;
    if (window.titanosDesktop?.getRuntimeInfo) {
      const runtime = await window.titanosDesktop.getRuntimeInfo();
      this.apiBaseUrl = runtime?.apiBase || '';
    }
    return this.apiBaseUrl;
  }

  async fetch(endpoint, options = {}) {
    if (window.titanosDesktop?.apiFetch) {
      const response = await window.titanosDesktop.apiFetch(endpoint, options);
      if (!response.ok) {
        throw new Error(`API error: ${response.statusText || response.status}`);
      }
      return response.data;
    }
    const baseUrl = await this.getApiBaseUrl();
    const url = `${baseUrl}${endpoint}`;
    try {
      const res = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });
      if (!res.ok) {
        throw new Error(`API error: ${res.statusText}`);
      }
      return await res.json();
    } catch (error) {
      console.error(`Error fetching ${endpoint}:`, error);
      throw error;
    }
  }

  // System
  getRuntimeStatus() { return this.fetch('/runtime'); }
  getDoctorStatus() { return this.fetch('/doctor'); }
  getBodyHealth() { return this.fetch('/body/health'); }
  
  // Providers
  getProviderPresets() { return this.fetch('/providers/presets'); }
  getProvidersHealth() { return this.fetch('/health/providers'); }
  getProviderConfigs() { return this.fetch('/providers/config'); }
  saveProviderConfig(data) {
    return this.fetch('/providers/config', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
  deleteProviderConfig(providerId) {
    return this.fetch(`/providers/config/${providerId}`, { method: 'DELETE' });
  }
  testProviderConfig(providerId) {
    return this.fetch(`/providers/config/${providerId}/test`, { method: 'POST' });
  }

  // Approvals & Runs
  chat(data) {
    return this.fetch('/chat', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
  getApprovals() { return this.fetch('/hands/approvals'); }
  approveAction(id) {
    return this.fetch(`/hands/approvals/${id}/approve`, { method: 'POST' });
  }
  rejectAction(id) {
    return this.fetch(`/hands/approvals/${id}/reject`, { method: 'POST' });
  }
  
  getRuns() { return this.fetch('/runs'); }
  getRun(runId) { return this.fetch(`/runs/${runId}`); }
  
  // Events
  getAuditEvents() { return this.fetch('/audit/events'); }
  
  // Memory
  getMemory() { return this.fetch('/memory'); }

  // Backups
  getBackups() { return this.fetch('/hands/backups'); }
  getBackup(backupId) { return this.fetch(`/hands/backups/${backupId}`); }
  restoreBackup(backupId) { return this.fetch(`/hands/backups/${backupId}/restore`, { method: 'POST' }); }

  // Diagnostics
  getDiagnostics() { return this.fetch('/runtime/diagnostics'); }
  exportDiagnostics() { return this.fetch('/runtime/diagnostics/export', { method: 'POST' }); }
}

export const apiService = new ApiService();
