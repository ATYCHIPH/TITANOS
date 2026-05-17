import { Activity, ChevronDown, ChevronUp, Download, Trash2 } from 'lucide-react';

const logs = [
  ['21:04:40', 'INFO', 'Brain session initialized'],
  ['21:04:49', 'OK', 'Provider presets loaded'],
  ['21:13:10', 'OK', 'Voice routed conversation'],
  ['21:13:24', 'OK', 'API key vault redaction verified'],
  ['21:14:02', 'INFO', 'Workspace inspector ready']
];

const ActivityPanel = ({ isExpanded, onToggle }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: 'rgba(5,8,12,0.72)' }}>
      <div
        onClick={onToggle}
        style={{
          height: 40,
          padding: '0 18px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
          userSelect: 'none'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Activity size={16} color="var(--accent-cyan)" />
          <span className="eyebrow">System Activity</span>
          <span className="status-pill"><span className="status-dot" /> Connected</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ color: 'var(--text-tertiary)', fontSize: '0.75rem' }}>5 events</span>
          {isExpanded ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
        </div>
      </div>

      {isExpanded && (
        <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 260px', gap: 12, padding: 12, minHeight: 0, overflow: 'hidden' }}>
          <div className="glass-tile" style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <div style={{ height: 34, display: 'flex', alignItems: 'center', gap: 12, padding: '0 12px', borderBottom: '1px solid var(--border-subtle)' }}>
              <span className="eyebrow">Console</span>
              <span style={{ color: 'var(--text-tertiary)', fontSize: '0.75rem' }}>Network</span>
              <span style={{ color: 'var(--text-tertiary)', fontSize: '0.75rem' }}>Runtime</span>
              <div style={{ flex: 1 }} />
              <button className="btn btn-ghost" style={{ padding: 4 }} title="Download logs"><Download size={14} /></button>
              <button className="btn btn-ghost" style={{ padding: 4 }} title="Clear logs"><Trash2 size={14} /></button>
            </div>
            <div style={{ flex: 1, padding: 12, overflowY: 'auto', fontFamily: 'Consolas, monospace', fontSize: '0.78rem' }}>
              {logs.map(([time, level, message]) => (
                <div key={`${time}-${message}`} style={{ display: 'grid', gridTemplateColumns: '72px 54px 1fr', gap: 8, marginBottom: 6 }}>
                  <span style={{ color: 'var(--text-tertiary)' }}>[{time}]</span>
                  <span style={{ color: level === 'OK' ? 'var(--success)' : 'var(--accent-cyan)' }}>{level}</span>
                  <span style={{ color: 'var(--text-secondary)' }}>{message}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-tile" style={{ padding: 12 }}>
            <div className="eyebrow" style={{ marginBottom: 10 }}>Health</div>
            {[
              ['UI Bridge', 100],
              ['Backend', 100],
              ['Sessions', 92],
              ['Provider Keys', 78],
            ].map(([label, value]) => (
              <div key={label} style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: 5 }}>
                  <span>{label}</span>
                  <span>{value}%</span>
                </div>
                <div style={{ height: 5, borderRadius: 999, background: 'rgba(255,255,255,0.08)', overflow: 'hidden' }}>
                  <div style={{ width: `${value}%`, height: '100%', background: 'linear-gradient(90deg, var(--accent-cyan), var(--success))' }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ActivityPanel;
