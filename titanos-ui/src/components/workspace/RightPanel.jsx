import React from 'react';
import { 
  FileText, Globe, Layers, BookOpen, 
  Settings, Database, Zap, Share2 
} from 'lucide-react';

const RightPanel = ({ activePanel, onPanelChange }) => {
  const tools = [
    { id: 'editor', name: 'Editor', icon: FileText },
    { id: 'files', name: 'Files', icon: Layers },
    { id: 'browser', name: 'Browser', icon: Globe },
    { id: 'knowledge', name: 'Knowledge', icon: BookOpen },
    { id: 'data', name: 'Data', icon: Database },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Tool Tabs */}
      <div style={{ 
        display: 'flex', 
        borderBottom: '1px solid var(--border-subtle)',
        padding: 'var(--space-xs)'
      }}>
        {tools.map(tool => (
          <button 
            key={tool.id}
            onClick={() => onPanelChange(tool.id)}
            className="btn btn-ghost"
            style={{ 
              flex: 1, 
              padding: '8px', 
              color: activePanel === tool.id ? 'var(--accent-primary)' : 'var(--text-tertiary)',
              background: activePanel === tool.id ? 'rgba(59, 130, 246, 0.05)' : 'transparent',
              borderRadius: 'var(--radius-md)'
            }}
            title={tool.name}
          >
            <tool.icon size={18} />
          </button>
        ))}
      </div>

      {/* Tool Content */}
      <div style={{ flex: 1, overflowY: 'auto', padding: 'var(--space-md)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-md)' }}>
          <h4 style={{ fontSize: '0.9rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)' }}>
            {activePanel.charAt(0).toUpperCase() + activePanel.slice(1)}
          </h4>
          <button className="btn btn-ghost" style={{ padding: '4px' }}><Settings size={14} /></button>
        </div>

        {/* Mock Content based on activePanel */}
        {activePanel === 'browser' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
            <div className="card" style={{ padding: 'var(--space-sm)', fontSize: '0.85rem' }}>
              <div style={{ color: 'var(--accent-primary)', marginBottom: '4px', fontWeight: 500 }}>Market Trends 2024</div>
              <div style={{ color: 'var(--text-tertiary)', fontSize: '0.75rem' }}>https://techcrunch.com/trends...</div>
            </div>
            <div className="card" style={{ padding: 'var(--space-sm)', fontSize: '0.85rem' }}>
              <div style={{ color: 'var(--accent-primary)', marginBottom: '4px', fontWeight: 500 }}>AI Agent Architecture</div>
              <div style={{ color: 'var(--text-tertiary)', fontSize: '0.75rem' }}>https://arxiv.org/abs/2401...</div>
            </div>
          </div>
        )}

        {activePanel === 'files' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
            {['src/', 'public/', 'package.json', 'README.md', 'vite.config.js'].map(file => (
              <div key={file} style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 'var(--space-sm)', 
                fontSize: '0.85rem', 
                padding: 'var(--space-xs) var(--space-sm)',
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer'
              }} className="hover-bg">
                <FileText size={14} color="var(--text-tertiary)" />
                {file}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Bottom Actions */}
      <div style={{ padding: 'var(--space-md)', borderTop: '1px solid var(--border-subtle)' }}>
        <button className="btn btn-secondary" style={{ width: '100%', gap: 'var(--space-sm)' }}>
          <Share2 size={16} /> Share Workspace
        </button>
      </div>
    </div>
  );
};

export default RightPanel;
