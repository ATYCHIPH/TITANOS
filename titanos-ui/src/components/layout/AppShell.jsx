import React, { useState } from 'react';
import { 
  Layout, 
  Search, 
  Bell, 
  Settings as SettingsIcon, 
  Menu, 
  ChevronLeft, 
  Plus,
  Command,
  User,
  LogOut,
  Sparkles,
  Zap,
  Terminal,
  Activity,
  Box,
  FileText,
  Globe,
  CheckSquare
} from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import Logo from '../shared/Logo';

const AppShell = ({ children, user, onLogout }) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [activeWorkspace, setActiveWorkspace] = useState('universal');
  const location = useLocation();

  const workspaces = [
    { id: 'universal', name: 'Universal', icon: Sparkles },
    { id: 'coding', name: 'Coding', icon: Terminal },
    { id: 'business', name: 'Business', icon: Box },
    { id: 'content', name: 'Content', icon: FileText },
    { id: 'research', name: 'Research', icon: Globe },
    { id: 'data', name: 'Data', icon: Activity },
    { id: 'daily', name: 'Workflow', icon: CheckSquare },
  ];

  const isActive = (path) => location.pathname.startsWith(path);

  return (
    <div style={{ display: 'flex', height: '100vh', background: 'var(--bg-primary)' }}>
      {/* Sidebar */}
      <aside className="glass" style={{
        width: sidebarCollapsed ? '64px' : '260px',
        borderRight: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        transition: 'width 0.3s ease',
        zIndex: 100
      }}>
        {/* Header / Brand */}
        <div style={{ 
          padding: 'var(--space-md)', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: sidebarCollapsed ? 'center' : 'space-between',
          borderBottom: '1px solid var(--border-subtle)'
        }}>
          {!sidebarCollapsed ? (
            <Logo size={24} />
          ) : (
            <Logo size={24} showText={false} />
          )}
          <button className="btn btn-ghost" style={{ padding: '4px' }} onClick={() => setSidebarCollapsed(!sidebarCollapsed)}>
            <Menu size={18} />
          </button>
        </div>

        {/* Workspace Switcher */}
        <div style={{ padding: 'var(--space-sm)', flex: 1, overflowY: 'auto' }}>
          {!sidebarCollapsed && <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', padding: 'var(--space-sm)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Workspaces</div>}
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
            {workspaces.map(ws => (
              <button 
                key={ws.id} 
                onClick={() => setActiveWorkspace(ws.id)}
                className={`btn ${activeWorkspace === ws.id ? 'btn-secondary' : 'btn-ghost'}`}
                style={{ 
                  justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
                  background: activeWorkspace === ws.id ? 'rgba(255,255,255,0.05)' : 'transparent',
                  borderColor: activeWorkspace === ws.id ? 'var(--border-strong)' : 'transparent',
                  padding: sidebarCollapsed ? 'var(--space-sm)' : 'var(--space-sm) var(--space-md)',
                  width: '100%'
                }}
              >
                <ws.icon size={18} color={activeWorkspace === ws.id ? 'var(--accent-primary)' : 'var(--text-secondary)'} />
                {!sidebarCollapsed && <span>{ws.name}</span>}
              </button>
            ))}
          </div>

          <div style={{ margin: 'var(--space-md) 0', borderTop: '1px solid var(--border-subtle)' }} />
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
            <Link to="/workspace/tasks" className="btn btn-ghost" style={{ justifyContent: sidebarCollapsed ? 'center' : 'flex-start', width: '100%', textDecoration: 'none' }}>
              <CheckSquare size={18} />
              {!sidebarCollapsed && <span>Tasks</span>}
            </Link>
            <Link to="/workspace/files" className="btn btn-ghost" style={{ justifyContent: sidebarCollapsed ? 'center' : 'flex-start', width: '100%', textDecoration: 'none' }}>
              <FileText size={18} />
              {!sidebarCollapsed && <span>Documents</span>}
            </Link>
          </div>
        </div>

        {/* User / Settings */}
        <div style={{ padding: 'var(--space-sm)', borderTop: '1px solid var(--border-subtle)' }}>
          <Link to="/settings" className="btn btn-ghost" style={{ justifyContent: sidebarCollapsed ? 'center' : 'flex-start', width: '100%', textDecoration: 'none' }}>
            <SettingsIcon size={18} />
            {!sidebarCollapsed && <span>Settings</span>}
          </Link>
          <div style={{ padding: 'var(--space-sm)', display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', marginTop: '4px' }}>
            <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'var(--bg-tertiary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <User size={16} />
            </div>
            {!sidebarCollapsed && (
              <div style={{ flex: 1, overflow: 'hidden' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{user?.name || 'User'}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)' }}>Pro Plan</div>
              </div>
            )}
            {!sidebarCollapsed && (
              <button className="btn btn-ghost" style={{ padding: '4px' }} onClick={onLogout}>
                <LogOut size={16} color="var(--error)" />
              </button>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', position: 'relative' }}>
        {/* Top Navbar */}
        <header className="glass" style={{ 
          height: '56px', 
          borderBottom: '1px solid var(--border-subtle)', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          padding: '0 var(--space-lg)',
          zIndex: 50
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)', flex: 1 }}>
            <div style={{ position: 'relative', width: '100%', maxWidth: '400px' }}>
              <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
              <input 
                className="input" 
                placeholder="Global Search (Ctrl+K)" 
                style={{ height: '32px', background: 'rgba(255,255,255,0.03)', paddingLeft: '36px', fontSize: '0.8rem' }}
              />
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
            <button className="btn btn-ghost" style={{ padding: '8px' }}>
              <Bell size={18} />
            </button>
            <div style={{ width: '1px', height: '24px', background: 'var(--border-subtle)' }} />
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--success)' }} />
              Agent Ready
            </div>
          </div>
        </header>

        {/* Content Area */}
        <div style={{ flex: 1, overflow: 'hidden', display: 'flex' }}>
          {children}
        </div>
      </main>
    </div>
  );
};

export default AppShell;
