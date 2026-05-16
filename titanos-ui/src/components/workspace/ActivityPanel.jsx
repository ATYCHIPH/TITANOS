import React from 'react';
import { Terminal, ChevronUp, ChevronDown, Activity, Trash2, Download } from 'lucide-react';

const ActivityPanel = ({ isExpanded, onToggle }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Panel Header */}
      <div 
        onClick={onToggle}
        style={{ 
          height: '40px', 
          padding: '0 var(--space-lg)', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          cursor: 'pointer',
          userSelect: 'none'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
          <Activity size={16} color="var(--text-tertiary)" />
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            System Activity & Logs
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--success)' }} />
            Connected
          </div>
          {isExpanded ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: '#050505', overflow: 'hidden' }}>
          <div style={{ 
            height: '36px', 
            background: 'var(--bg-tertiary)', 
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            padding: '0 var(--space-md)',
            gap: 'var(--space-md)'
          }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Console</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>Network</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>Environment</div>
            <div style={{ flex: 1 }} />
            <button className="btn btn-ghost" style={{ padding: '2px' }}><Download size={14} /></button>
            <button className="btn btn-ghost" style={{ padding: '2px' }}><Trash2 size={14} /></button>
          </div>
          
          <div style={{ 
            flex: 1, 
            padding: 'var(--space-md)', 
            fontFamily: 'monospace', 
            fontSize: '0.8rem', 
            color: '#888',
            overflowY: 'auto'
          }}>
            <div style={{ marginBottom: '4px' }}><span style={{ color: '#555' }}>[23:40:01]</span> <span style={{ color: 'var(--accent-primary)' }}>INFO</span>: Initializing agent runtime...</div>
            <div style={{ marginBottom: '4px' }}><span style={{ color: '#555' }}>[23:40:02]</span> <span style={{ color: 'var(--accent-primary)' }}>INFO</span>: Connecting to TITANOS-core gateway...</div>
            <div style={{ marginBottom: '4px' }}><span style={{ color: '#555' }}>[23:40:03]</span> <span style={{ color: 'var(--success)' }}>SUCCESS</span>: Secure connection established.</div>
            <div style={{ marginBottom: '4px' }}><span style={{ color: '#555' }}>[23:40:05]</span> <span style={{ color: 'var(--warning)' }}>WARN</span>: Provider 'OpenAI' key not found. Using mock mode.</div>
            <div style={{ marginBottom: '4px' }}><span style={{ color: '#555' }}>[23:40:10]</span> <span style={{ color: 'var(--accent-primary)' }}>INFO</span>: Ready for commands.</div>
            <div style={{ color: '#ddd' }}>$ titanos-agent --status</div>
            <div style={{ color: '#aaa' }}>Agent ID: titanos-alpha-01</div>
            <div style={{ color: '#aaa' }}>Uptime: 00:00:15</div>
            <div style={{ color: '#aaa' }}>Memory: 124MB / 1024MB</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ActivityPanel;
