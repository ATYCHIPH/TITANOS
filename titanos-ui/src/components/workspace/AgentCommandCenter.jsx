import { useEffect, useRef, useState } from 'react';
import {
  Bot,
  CheckCircle2,
  Circle,
  Mic,
  Paperclip,
  Search,
  Send,
  Sparkles
} from 'lucide-react';

const starterPrompts = [
  'hello',
  'what did I say before?',
  'route this to memory',
  'check provider health'
];

const AgentCommandCenter = ({ onCommand, conversation }) => {
  const [input, setInput] = useState('');
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [conversation]);

  const submit = (value = input) => {
    if (!value.trim()) return;
    onCommand(value.trim());
    setInput('');
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    submit();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minWidth: 0 }}>
      <div className="panel-header">
        <div>
          <div className="eyebrow">Agent</div>
          <div style={{ fontWeight: 700, marginTop: 2 }}>New chat</div>
        </div>
        <div className="status-pill"><span className="status-dot" /> Brain linked</div>
      </div>

      <div style={{ padding: 14, borderBottom: '1px solid var(--border-subtle)' }}>
        <div className="glass-tile" style={{ display: 'flex', alignItems: 'center', gap: 10, height: 38, padding: '0 12px' }}>
          <Search size={15} color="var(--text-tertiary)" />
          <span style={{ color: 'var(--text-tertiary)', fontSize: '0.82rem' }}>Search current conversation</span>
        </div>
      </div>

      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: 16,
          display: 'flex',
          flexDirection: 'column',
          gap: 14
        }}
      >
        {conversation.length === 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div className="glass-tile" style={{ padding: 18 }}>
              <div style={{
                width: 42,
                height: 42,
                borderRadius: 10,
                display: 'grid',
                placeItems: 'center',
                background: 'linear-gradient(135deg, rgba(35,211,238,0.22), rgba(124,92,255,0.24))',
                color: 'var(--accent-cyan)',
                marginBottom: 14
              }}>
                <Sparkles size={22} />
              </div>
              <h3 style={{ fontSize: '1.1rem', marginBottom: 8 }}>Plan, search, build anything</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.86rem', lineHeight: 1.55 }}>
                TITANOS now sends this pane through the backend brain, keeps a scoped session, and routes conversation separately from work commands.
              </p>
            </div>
            <div style={{ display: 'grid', gap: 8 }}>
              {starterPrompts.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => submit(prompt)}
                  style={{ justifyContent: 'space-between', fontSize: '0.82rem' }}
                >
                  {prompt}
                  <Send size={13} />
                </button>
              ))}
            </div>
          </div>
        ) : (
          conversation.map((msg, idx) => (
            <div key={`${msg.type}-${idx}`} style={{
              alignSelf: msg.type === 'user' ? 'flex-end' : 'stretch',
              maxWidth: msg.type === 'user' ? '84%' : '100%'
            }}>
              <div className={msg.type === 'user' ? '' : 'glass-tile'} style={{
                background: msg.type === 'user'
                  ? 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))'
                  : undefined,
                color: 'var(--text-primary)',
                padding: msg.type === 'user' ? '12px 14px' : 14,
                borderRadius: msg.type === 'user' ? '14px 14px 4px 14px' : 12,
                fontSize: '0.9rem',
                lineHeight: 1.5,
                boxShadow: msg.type === 'user' ? '0 12px 26px rgba(79,140,255,0.2)' : undefined
              }}>
                {msg.type === 'agent' && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                    <Bot size={15} color="var(--accent-cyan)" />
                    <span className="eyebrow">{msg.system || 'TITANOS'}</span>
                    {msg.status && <span className="status-pill" style={{ height: 22 }}>{msg.status}</span>}
                  </div>
                )}
                {msg.content}
              </div>

              {msg.plan && (
                <div style={{ marginTop: 8, display: 'grid', gap: 6 }}>
                  {msg.plan.map((step) => (
                    <div key={step.id} style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-secondary)', fontSize: '0.78rem' }}>
                      {step.status === 'completed'
                        ? <CheckCircle2 size={14} color="var(--success)" />
                        : step.status === 'running'
                          ? <span className="spinner-small" />
                          : <Circle size={14} color="var(--text-tertiary)" />}
                      {step.title}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      <div style={{ padding: 16, borderTop: '1px solid var(--border-subtle)' }}>
        <form onSubmit={handleSubmit} className="glass-tile" style={{ padding: 8 }}>
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask TITANOS..."
            style={{
              width: '100%',
              minHeight: 78,
              resize: 'none',
              border: 'none',
              outline: 'none',
              background: 'transparent',
              color: 'var(--text-primary)',
              padding: 10,
              fontFamily: 'inherit',
              fontSize: '0.9rem'
            }}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                submit();
              }
            }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', gap: 6 }}>
              <button type="button" className="btn btn-ghost" style={{ padding: 7 }} title="Attach context"><Paperclip size={17} /></button>
              <button type="button" className="btn btn-ghost" style={{ padding: 7 }} title="Voice input"><Mic size={17} /></button>
            </div>
            <button type="submit" className="btn btn-primary neon-button" style={{ padding: '8px 12px', borderRadius: 10 }} title="Send">
              <Send size={17} />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AgentCommandCenter;
