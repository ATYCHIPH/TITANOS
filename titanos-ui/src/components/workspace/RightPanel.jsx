import {
  Activity,
  Bell,
  Brain,
  Database,
  FileText,
  Globe,
  Layers,
  RefreshCw,
  Settings,
  Share2
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { apiService } from '../../services/apiService';

const tools = [
  { id: 'status', name: 'Runtime', icon: Activity },
  { id: 'providers', name: 'Providers', icon: Brain },
  { id: 'files', name: 'Files', icon: Layers },
  { id: 'knowledge', name: 'Knowledge', icon: Globe },
];

const RightPanel = ({ activePanel, onPanelChange }) => {
  const [runtimeData, setRuntimeData] = useState(null);
  const [providers, setProviders] = useState([]);

  const refreshRuntime = () => {
    apiService.getRuntimeStatus().then(setRuntimeData).catch(() => setRuntimeData(null));
    apiService.getProviderConfigs().then((data) => setProviders(data.providers || [])).catch(() => setProviders([]));
  };

  useEffect(() => {
    refreshRuntime();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minWidth: 0 }}>
      <div className="panel-header">
        <div>
          <div className="eyebrow">Inspector</div>
          <div style={{ fontWeight: 700, marginTop: 2 }}>Runtime control</div>
        </div>
        <button className="btn btn-ghost" style={{ padding: 7 }} onClick={refreshRuntime} title="Refresh">
          <RefreshCw size={15} />
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${tools.length}, 1fr)`, gap: 6, padding: 10, borderBottom: '1px solid var(--border-subtle)' }}>
        {tools.map((tool) => (
          <button
            key={tool.id}
            type="button"
            className="btn btn-ghost"
            onClick={() => onPanelChange(tool.id)}
            title={tool.name}
            style={{
              padding: 9,
              color: activePanel === tool.id ? 'var(--accent-cyan)' : 'var(--text-tertiary)',
              background: activePanel === tool.id ? 'rgba(35,211,238,0.08)' : 'transparent',
              borderColor: activePanel === tool.id ? 'rgba(35,211,238,0.22)' : 'transparent'
            }}
          >
            <tool.icon size={17} />
          </button>
        ))}
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: 14, display: 'grid', gap: 12, alignContent: 'start' }}>
        <section className="glass-tile" style={{ padding: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <span className="eyebrow">System</span>
            <span className="status-pill"><span className="status-dot" /> Online</span>
          </div>
          <div className="metric-grid">
            <div className="metric-card">
              <span className="eyebrow">Mode</span>
              <strong style={{ fontSize: '0.95rem' }}>{runtimeData?.desktop ? 'Desktop' : 'Local'}</strong>
            </div>
            <div className="metric-card">
              <span className="eyebrow">Backend</span>
              <strong style={{ fontSize: '0.95rem' }}>127.0.0.1</strong>
            </div>
          </div>
        </section>

        <section className="glass-tile" style={{ padding: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <Brain size={15} color="var(--accent-cyan)" />
            <span className="eyebrow">Provider Routing</span>
          </div>
          <div style={{ display: 'grid', gap: 8 }}>
            {(providers.length ? providers : [{ provider_id: 'google', label: 'Google Gemini', status: 'configure key' }]).slice(0, 4).map((provider) => (
              <div key={provider.provider_id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, fontSize: '0.8rem' }}>
                <span style={{ color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {provider.label || provider.provider_id}
                </span>
                <span className="status-pill" style={{ height: 22 }}>{provider.status || 'saved'}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="glass-tile" style={{ padding: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <Bell size={15} color="var(--warning)" />
            <span className="eyebrow">Alerts</span>
          </div>
          {['Conversation context scoped', 'API keys encrypted', 'Backend bridge active'].map((alert) => (
            <div key={alert} style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-secondary)', fontSize: '0.78rem', marginBottom: 8 }}>
              <span className="status-dot" style={{ width: 6, height: 6 }} />
              {alert}
            </div>
          ))}
        </section>

        <section className="glass-tile" style={{ padding: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <Database size={15} color="var(--success)" />
            <span className="eyebrow">Artifacts</span>
          </div>
          {['runtime.sqlite', 'session history', 'provider vault', 'audit events'].map((item) => (
            <div key={item} style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-secondary)', fontSize: '0.78rem', marginBottom: 8 }}>
              <FileText size={13} color="var(--text-tertiary)" />
              {item}
            </div>
          ))}
        </section>
      </div>

      <div style={{ padding: 14, borderTop: '1px solid var(--border-subtle)', display: 'grid', gap: 8 }}>
        <button className="btn btn-secondary" style={{ width: '100%', justifyContent: 'space-between' }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}><Share2 size={15} /> Share Workspace</span>
          <Settings size={14} />
        </button>
      </div>
    </div>
  );
};

export default RightPanel;
