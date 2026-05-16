import React from 'react';
import { FileCode, Globe, Terminal, Activity, Layers, Play, Save, RefreshCw } from 'lucide-react';

const WorkspaceCanvas = ({ activePanel, currentTask }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Canvas Header */}
      <div style={{ 
        height: '48px', 
        borderBottom: '1px solid var(--border-subtle)', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        padding: '0 var(--space-lg)',
        background: 'var(--bg-secondary)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', color: 'var(--text-secondary)' }}>
            <FileCode size={16} />
            <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>index.js</span>
          </div>
          <div style={{ width: '1px', height: '16px', background: 'var(--border-subtle)' }} />
          <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>TITANOS / projects / website</div>
        </div>
        
        <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
          <button className="btn btn-ghost" style={{ padding: '4px 8px', fontSize: '0.75rem' }}><Save size={14} /> Save</button>
          <button className="btn btn-primary" style={{ padding: '4px 12px', fontSize: '0.75rem' }}><Play size={14} /> Run</button>
        </div>
      </div>

      {/* Main Content View */}
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {activePanel === 'editor' && (
          <div style={{ 
            flex: 1, 
            padding: 'var(--space-lg)', 
            fontFamily: 'monospace', 
            fontSize: '0.9rem', 
            lineHeight: '1.6',
            color: '#d4d4d4',
            background: '#0e0e0e',
            overflow: 'auto'
          }}>
            <div><span style={{ color: '#569cd6' }}>import</span> React <span style={{ color: '#569cd6' }}>from</span> <span style={{ color: '#ce9178' }}>'react'</span>;</div>
            <div><span style={{ color: '#569cd6' }}>import</span> {'{'} useState, useEffect {'}'} <span style={{ color: '#569cd6' }}>from</span> <span style={{ color: '#ce9178' }}>'react'</span>;</div>
            <br />
            <div><span style={{ color: '#569cd6' }}>const</span> <span style={{ color: '#4fc1ff' }}>WorkspaceCanvas</span> = ({'{'} activePanel, currentTask {'}'}) ={'>'} {'{'}</div>
            <div style={{ paddingLeft: '20px' }}><span style={{ color: '#569cd6' }}>return</span> (</div>
            <div style={{ paddingLeft: '40px' }}>{'<'}div className=<span style={{ color: '#ce9178' }}>"canvas-container"</span>{'>'}</div>
            <div style={{ paddingLeft: '60px' }}>{'{'}/* Dynamic Canvas Implementation */{'}'}</div>
            <div style={{ paddingLeft: '40px' }}>{'<'}/div{'>'}</div>
            <div style={{ paddingLeft: '20px' }}>);</div>
            <div>{'}'};</div>
          </div>
        )}

        {activePanel === 'browser' && (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: 'white' }}>
            <div style={{ height: '32px', background: '#f0f0f0', display: 'flex', alignItems: 'center', padding: '0 12px', gap: '8px', borderBottom: '1px solid #ddd' }}>
              <div style={{ display: 'flex', gap: '4px' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ff5f56' }} />
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ffbd2e' }} />
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#27c93f' }} />
              </div>
              <div style={{ flex: 1, height: '20px', background: 'white', borderRadius: '4px', fontSize: '10px', display: 'flex', alignItems: 'center', padding: '0 8px', color: '#666' }}>
                https://titanos.ai/research/competitors
              </div>
            </div>
            <div style={{ flex: 1, padding: '40px', color: '#333', textAlign: 'center' }}>
              <Globe size={48} color="#ccc" style={{ marginBottom: '16px' }} />
              <h2 style={{ fontSize: '24px', marginBottom: '8px' }}>Competitor Analysis</h2>
              <p style={{ color: '#666' }}>Simulated Browser View for Research</p>
            </div>
          </div>
        )}

        {activePanel === 'data' && (
          <div style={{ flex: 1, padding: '20px', background: '#f8f9fa', color: '#333' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
              <thead>
                <tr style={{ background: '#eee' }}>
                  {['ID', 'Name', 'Value', 'Status'].map(h => (
                    <th key={h} style={{ textAlign: 'left', padding: '12px', border: '1px solid #ddd' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[1, 2, 3, 4, 5].map(i => (
                  <tr key={i}>
                    <td style={{ padding: '12px', border: '1px solid #ddd' }}>#00{i}</td>
                    <td style={{ padding: '12px', border: '1px solid #ddd' }}>Dataset Entry {i}</td>
                    <td style={{ padding: '12px', border: '1px solid #ddd' }}>{(Math.random() * 100).toFixed(2)}%</td>
                    <td style={{ padding: '12px', border: '1px solid #ddd' }}><span style={{ color: 'green' }}>Active</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Floating Task Progress Indicator */}
        {currentTask && (
          <div className="glass" style={{
            position: 'absolute',
            bottom: 'var(--space-lg)',
            right: 'var(--space-lg)',
            width: '300px',
            padding: 'var(--space-md)',
            borderRadius: 'var(--radius-lg)',
            boxShadow: 'var(--shadow-lg)'
          }}>
            <div style={{ display: 'flex', justifyItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-sm)' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Executing Task</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--accent-primary)' }}>{currentTask.progress}%</div>
            </div>
            <div style={{ width: '100%', height: '4px', background: 'var(--bg-tertiary)', borderRadius: '2px', overflow: 'hidden', marginBottom: 'var(--space-sm)' }}>
              <div style={{ width: `${currentTask.progress}%`, height: '100%', background: 'var(--accent-primary)' }} />
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 'var(--space-xs)' }}>
              <RefreshCw size={12} className="spin" />
              {currentTask.title}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkspaceCanvas;
