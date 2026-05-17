import { cloneElement, isValidElement, useEffect, useState } from 'react';
import { 
  Search, 
  Bell, 
  Settings as SettingsIcon, 
  Menu, 
  User,
  Sparkles,
  Terminal,
  Activity,
  Box,
  FileText,
  Globe,
  CheckSquare,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import Logo from '../shared/Logo';
import { apiService } from '../../services/apiService';

const AppShell = ({ children }) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [runtimeInfo, setRuntimeInfo] = useState(null);
  const [isRetrying, setIsRetrying] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [providerWarning, setProviderWarning] = useState(false);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    if (window.titanosDesktop) {
      const refreshDesktopRuntime = async () => {
        try {
          const info = await window.titanosDesktop.getRuntimeInfo();
          try {
            await apiService.getRuntimeStatus();
            setRuntimeInfo({
              ...info,
              backend: {
                ...(info.backend || {}),
                state: info.backend?.state === 'external' ? 'external' : 'ready',
                message: info.backend?.message || 'Connected to packaged TITANOS backend.',
              },
            });
          } catch {
            setRuntimeInfo(info);
          }
        } catch (err) {
          console.error("Failed to read desktop runtime:", err);
        }
      };
      refreshDesktopRuntime();
      const unsubscribe = window.titanosDesktop.onBackendStatus((info) => {
        setRuntimeInfo(info);
      });
      const interval = setInterval(refreshDesktopRuntime, 3000);
      return () => {
        window.removeEventListener('online', handleOnline);
        window.removeEventListener('offline', handleOffline);
        clearInterval(interval);
        unsubscribe();
      };
    } else {
      const checkStatus = () => {
        apiService.getRuntimeStatus()
          .then(() => {
            setRuntimeInfo({
              apiBase: '',
              backend: { state: 'ready', message: 'Connected to web endpoint.' },
              packaged: false,
              platform: 'web',
              version: '1.0.0-web'
            });
          })
          .catch(() => {
            setRuntimeInfo({
              apiBase: '',
              backend: { state: 'crashed', message: 'Web endpoint is offline.' },
              packaged: false,
              platform: 'web',
              version: '1.0.0-web'
            });
          });
      };
      checkStatus();
      const interval = setInterval(checkStatus, 5000);
      return () => {
        window.removeEventListener('online', handleOnline);
        window.removeEventListener('offline', handleOffline);
        clearInterval(interval);
      };
    }
  }, []);

  useEffect(() => {
    if (['ready', 'external'].includes(runtimeInfo?.backend?.state)) {
      apiService.getProvidersHealth()
        .then(data => {
          const providers = data.providers || [];
          const anyAvailable = providers.some(p => ['online', 'healthy', 'saved'].includes(p.status));
          setProviderWarning(!anyAvailable);
        })
        .catch(() => {
          apiService.getProviderConfigs().then(config => {
            const hasKey = (config.providers || []).some(p => Boolean(p.secret_ref || p.masked_key));
            setProviderWarning(!hasKey);
          }).catch(() => {});
        });
    }
  }, [runtimeInfo]);

  const handleReconnect = async () => {
    setIsRetrying(true);
    if (window.titanosDesktop) {
      try {
        const info = await window.titanosDesktop.restartBackend();
        setRuntimeInfo(info);
      } catch (err) {
        console.error("Failed to restart backend:", err);
      }
    } else {
      try {
        await apiService.getRuntimeStatus();
      } catch (err) {
        console.error("Retry failed:", err);
      }
    }
    setIsRetrying(false);
  };
  const [activeWorkspace, setActiveWorkspace] = useState('universal');
  useLocation();

  const workspaces = [
    { id: 'universal', name: 'Universal', icon: Sparkles },
    { id: 'coding', name: 'Coding', icon: Terminal },
    { id: 'business', name: 'Business', icon: Box },
    { id: 'content', name: 'Content', icon: FileText },
    { id: 'research', name: 'Research', icon: Globe },
    { id: 'data', name: 'Data', icon: Activity },
    { id: 'daily', name: 'Workflow', icon: CheckSquare },
  ];

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
                <div style={{ fontSize: '0.85rem', fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>Operator Workspace</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)' }}>Local Mode</div>
              </div>
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
            
            {/* Backend Status UX */}
            {(() => {
              const state = runtimeInfo?.backend?.state || 'starting';
              const message = runtimeInfo?.backend?.message || 'Initializing...';
              
              let statusText = 'Starting...';
              let dotColor = 'orange';
              let showRetry = false;

              if (state === 'ready' || state === 'external') {
                statusText = state === 'external' ? 'Connected (Ext)' : 'Connected';
                dotColor = 'var(--success)';
              } else if (state === 'crashed' || state === 'timeout' || state === 'missing' || state === 'disabled') {
                statusText = 'Backend Offline';
                dotColor = 'var(--error)';
                showRetry = true;
              } else if (state === 'starting' || state === 'restarting') {
                statusText = 'Connecting...';
                dotColor = 'orange';
              }

              return (
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
                  <div 
                    title={message}
                    style={{ 
                      fontSize: '0.8rem', 
                      color: 'var(--text-secondary)', 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '6px',
                      background: 'rgba(255,255,255,0.02)',
                      padding: '4px 10px',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border-subtle)'
                    }}
                  >
                    <div style={{ 
                      width: '8px', 
                      height: '8px', 
                      borderRadius: '50%', 
                      background: dotColor,
                      boxShadow: `0 0 8px ${dotColor}`
                    }} />
                    <span>{statusText}</span>
                  </div>
                  {showRetry && (
                    <button 
                      className="btn btn-primary"
                      onClick={handleReconnect}
                      disabled={isRetrying}
                      style={{ 
                        padding: '2px 8px', 
                        fontSize: '0.75rem',
                        height: '24px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                    >
                      <RefreshCw size={12} className={isRetrying ? "spin" : ""} />
                      {isRetrying ? 'Retrying...' : 'Retry'}
                    </button>
                  )}
                </div>
              );
            })()}
          </div>
        </header>

        {/* Premium Degraded UX Banners */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '12px 24px 0 24px' }}>
          {!isOnline && (
            <div className="fade-in" style={{
              background: 'rgba(239, 68, 68, 0.08)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: 'var(--radius-md)',
              padding: '10px 16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              color: '#fca5a5',
              fontSize: '0.85rem'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertCircle size={16} />
                <span><strong>No Network Connection.</strong> Universal tools and external API providers are running in degraded offline fallback mode.</span>
              </div>
            </div>
          )}

          {isOnline && runtimeInfo?.backend?.state && ['crashed', 'timeout', 'missing', 'disabled'].includes(runtimeInfo.backend.state) && (
            <div className="fade-in" style={{
              background: 'rgba(245, 158, 11, 0.08)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              borderRadius: 'var(--radius-md)',
              padding: '10px 16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              color: '#fde047',
              fontSize: '0.85rem'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertCircle size={16} />
                <span><strong>TITANOS Backend Offline.</strong> The operator workspace is running in degraded local-only mode. All file and execution tasks are mocked.</span>
              </div>
              <button className="btn btn-primary" onClick={handleReconnect} disabled={isRetrying} style={{ padding: '4px 10px', fontSize: '0.75rem', height: '24px' }}>
                {isRetrying ? 'Starting...' : 'Restart Backend'}
              </button>
            </div>
          )}

          {isOnline && runtimeInfo?.backend?.state === 'ready' && providerWarning && (
            <div className="fade-in" style={{
              background: 'rgba(59, 130, 246, 0.08)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              borderRadius: 'var(--radius-md)',
              padding: '10px 16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              color: '#93c5fd',
              fontSize: '0.85rem'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={16} />
                <span><strong>Missing API Credentials.</strong> No active AI provider API key is set. Go to settings to authorize OpenAI/Anthropic models.</span>
              </div>
              <Link to="/settings" className="btn btn-ghost" style={{ padding: '4px 10px', fontSize: '0.75rem', height: '24px', textDecoration: 'none', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
                Configure Keys
              </Link>
            </div>
          )}
        </div>

        {/* Content Area */}
        <div style={{ flex: 1, overflow: 'hidden', display: 'flex' }}>
          {isValidElement(children) ? cloneElement(children, { activeWorkspace }) : children}
        </div>
      </main>
    </div>
  );
};

export default AppShell;
