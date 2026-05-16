import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Paperclip, Mic, ShieldAlert, CheckCircle2, Circle } from 'lucide-react';

const AgentCommandCenter = ({ onCommand, conversation }) => {
  const [input, setInput] = useState('');
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [conversation]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    onCommand(input);
    setInput('');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Messages Area */}
      <div 
        ref={scrollRef}
        style={{ 
          flex: 1, 
          overflowY: 'auto', 
          padding: 'var(--space-lg)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-lg)'
        }}
      >
        {conversation.length === 0 ? (
          <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
            <div style={{ width: '80px', height: '80px', background: 'var(--bg-tertiary)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 'var(--space-md)' }}>
              <Sparkles size={40} color="var(--accent-primary)" />
            </div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: 'var(--space-sm)' }}>How can I help today?</h3>
            <p style={{ color: 'var(--text-tertiary)', fontSize: '0.9rem', maxWidth: '280px' }}>
              Try: "Analyze the current repo and suggest improvements" or "Build a landing page for my new product".
            </p>
          </div>
        ) : (
          conversation.map((msg, idx) => (
            <div key={idx} style={{ 
              alignSelf: msg.type === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '85%'
            }}>
              <div style={{ 
                background: msg.type === 'user' ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
                color: 'white',
                padding: 'var(--space-md)',
                borderRadius: 'var(--radius-lg)',
                borderBottomRightRadius: msg.type === 'user' ? '0' : 'var(--radius-lg)',
                borderBottomLeftRadius: msg.type === 'agent' ? '0' : 'var(--radius-lg)',
                fontSize: '0.95rem',
                lineHeight: '1.5',
                boxShadow: 'var(--shadow-sm)'
              }}>
                {msg.content}
              </div>
              
              {msg.plan && (
                <div className="card" style={{ marginTop: 'var(--space-md)', padding: 'var(--space-sm)', background: 'rgba(255,255,255,0.02)' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-tertiary)', marginBottom: 'var(--space-sm)', textTransform: 'uppercase' }}>Current Plan</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xs)' }}>
                    {msg.plan.map(step => (
                      <div key={step.id} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', fontSize: '0.85rem' }}>
                        {step.status === 'completed' ? <CheckCircle2 size={14} color="var(--success)" /> : 
                         step.status === 'running' ? <div className="spinner-small" /> : <Circle size={14} color="var(--text-tertiary)" />}
                        <span style={{ color: step.status === 'pending' ? 'var(--text-tertiary)' : 'var(--text-primary)' }}>{step.title}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Input Area */}
      <div style={{ padding: 'var(--space-lg)', borderTop: '1px solid var(--border-subtle)' }}>
        <form 
          onSubmit={handleSubmit}
          style={{ 
            background: 'var(--bg-tertiary)', 
            borderRadius: 'var(--radius-xl)', 
            padding: 'var(--space-xs)',
            display: 'flex',
            flexDirection: 'column',
            border: '1px solid var(--border-subtle)',
            boxShadow: 'var(--shadow-md)'
          }}
        >
          <textarea 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a command..."
            style={{ 
              background: 'transparent',
              border: 'none',
              color: 'var(--text-primary)',
              padding: 'var(--space-md)',
              resize: 'none',
              minHeight: '80px',
              fontFamily: 'inherit',
              fontSize: '0.95rem',
              outline: 'none'
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 'var(--space-xs) var(--space-sm)' }}>
            <div style={{ display: 'flex', gap: 'var(--space-xs)' }}>
              <button type="button" className="btn btn-ghost" style={{ padding: '6px' }}><Paperclip size={18} /></button>
              <button type="button" className="btn btn-ghost" style={{ padding: '6px' }}><Mic size={18} /></button>
            </div>
            <button type="submit" className="btn btn-primary" style={{ padding: '6px 16px', borderRadius: 'var(--radius-lg)' }}>
              <Send size={18} />
            </button>
          </div>
        </form>
        <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textAlign: 'center', marginTop: 'var(--space-sm)' }}>
          Press Enter to send, Shift+Enter for new line
        </div>
      </div>
    </div>
  );
};

export default AgentCommandCenter;
