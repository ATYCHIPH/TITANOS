import React, { useState } from 'react';
import { 
  User, Key, Monitor, Shield, 
  Zap, Bell, CreditCard, ChevronRight,
  Plus, Trash2, CheckCircle2, AlertCircle,
  Eye, EyeOff
} from 'lucide-react';
import AppShell from '../../components/layout/AppShell';
import { storageService } from '../../services/storageService';
import { providerService } from '../../services/providerService';

const Settings = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState('providers');
  const [keys, setKeys] = useState(storageService.getKeys());
  const [isAddingKey, setIsAddingKey] = useState(false);
  const [newKeyData, setNewKeyData] = useState({ providerId: 'openai', apiKey: '' });
  const [testingStatus, setTestingStatus] = useState(null); // 'testing', 'success', 'error'

  const handleAddKey = async () => {
    setTestingStatus('testing');
    try {
      await providerService.testConnection(newKeyData.providerId, newKeyData.apiKey);
      await storageService.saveKey(newKeyData.providerId, newKeyData);
      setKeys(storageService.getKeys());
      setIsAddingKey(false);
      setNewKeyData({ providerId: 'openai', apiKey: '' });
      setTestingStatus(null);
    } catch (err) {
      setTestingStatus('error');
    }
  };

  const handleDeleteKey = async (providerId) => {
    await storageService.deleteKey(providerId);
    setKeys(storageService.getKeys());
  };

  const tabs = [
    { id: 'account', name: 'Account', icon: User },
    { id: 'providers', name: 'API Providers', icon: Key },
    { id: 'appearance', name: 'Appearance', icon: Monitor },
    { id: 'security', name: 'Security', icon: Shield },
    { id: 'usage', name: 'Usage & Billing', icon: CreditCard },
  ];

  return (
    <AppShell user={user} onLogout={onLogout}>
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Settings Sidebar */}
        <div style={{ width: '240px', borderRight: '1px solid var(--border-subtle)', padding: 'var(--space-lg)' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: 'var(--space-xl)' }}>Settings</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {tabs.map(tab => (
              <button 
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`btn ${activeTab === tab.id ? 'btn-secondary' : 'btn-ghost'}`}
                style={{ 
                  justifyContent: 'flex-start',
                  background: activeTab === tab.id ? 'rgba(255,255,255,0.05)' : 'transparent',
                  borderColor: activeTab === tab.id ? 'var(--border-strong)' : 'transparent'
                }}
              >
                <tab.icon size={18} color={activeTab === tab.id ? 'var(--accent-primary)' : 'var(--text-secondary)'} />
                {tab.name}
              </button>
            ))}
          </div>
        </div>

        {/* Settings Content */}
        <div style={{ flex: 1, padding: 'var(--space-xl)', overflowY: 'auto' }}>
          {activeTab === 'providers' && (
            <div className="fade-in" style={{ maxWidth: '800px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-xl)' }}>
                <div>
                  <h3 style={{ fontSize: '1.5rem', fontWeight: 600 }}>API Providers</h3>
                  <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>Manage your AI model connections and API keys.</p>
                </div>
                <button className="btn btn-primary" onClick={() => setIsAddingKey(true)}>
                  <Plus size={18} /> Add Provider
                </button>
              </div>

              {isAddingKey && (
                <div className="card" style={{ marginBottom: 'var(--space-xl)', padding: 'var(--space-lg)' }}>
                  <h4 style={{ marginBottom: 'var(--space-md)' }}>Connect New Provider</h4>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-md)', marginBottom: 'var(--space-md)' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Provider</label>
                      <select 
                        className="input" 
                        value={newKeyData.providerId}
                        onChange={(e) => setNewKeyData({...newKeyData, providerId: e.target.value})}
                      >
                        {providerService.getAvailableProviders().map(p => (
                          <option key={p.id} value={p.id}>{p.name}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>API Key</label>
                      <input 
                        className="input" 
                        type="password" 
                        placeholder="sk-..." 
                        value={newKeyData.apiKey}
                        onChange={(e) => setNewKeyData({...newKeyData, apiKey: e.target.value})}
                      />
                    </div>
                  </div>
                  
                  {testingStatus === 'error' && (
                    <div style={{ color: 'var(--error)', fontSize: '0.85rem', marginBottom: 'var(--space-md)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <AlertCircle size={14} /> Connection test failed. Check your key.
                    </div>
                  )}

                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-md)' }}>
                    <button className="btn btn-ghost" onClick={() => setIsAddingKey(false)}>Cancel</button>
                    <button 
                      className="btn btn-primary" 
                      onClick={handleAddKey}
                      disabled={testingStatus === 'testing' || !newKeyData.apiKey}
                    >
                      {testingStatus === 'testing' ? 'Testing...' : 'Test & Save'}
                    </button>
                  </div>
                </div>
              )}

              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
                {keys.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: 'var(--space-xl)', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-lg)', border: '1px dashed var(--border-subtle)' }}>
                    <p style={{ color: 'var(--text-tertiary)' }}>No providers connected yet.</p>
                  </div>
                ) : (
                  keys.map(key => (
                    <div key={key.providerId} className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
                        <div style={{ width: '40px', height: '40px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <Zap size={20} color="var(--accent-primary)" />
                        </div>
                        <div>
                          <div style={{ fontWeight: 600 }}>{key.providerId.charAt(0).toUpperCase() + key.providerId.slice(1)}</div>
                          <div style={{ fontSize: '0.85rem', color: 'var(--text-tertiary)', fontFamily: 'monospace' }}>{key.maskedKey}</div>
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
                        <button className="btn btn-ghost" style={{ padding: '8px' }}><Eye size={16} /></button>
                        <button className="btn btn-ghost" style={{ padding: '8px' }} onClick={() => handleDeleteKey(key.providerId)}><Trash2 size={16} color="var(--error)" /></button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {activeTab === 'account' && (
            <div className="fade-in">
              <h3 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: 'var(--space-xl)' }}>Account Settings</h3>
              <div className="card" style={{ maxWidth: '500px' }}>
                <div style={{ marginBottom: 'var(--space-md)' }}>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Display Name</label>
                  <input className="input" defaultValue={user?.name} />
                </div>
                <div style={{ marginBottom: 'var(--space-lg)' }}>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Email Address</label>
                  <input className="input" defaultValue={user?.email} disabled />
                </div>
                <button className="btn btn-primary">Update Profile</button>
              </div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
};

export default Settings;
