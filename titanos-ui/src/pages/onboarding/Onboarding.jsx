import React, { useState } from 'react';
import { 
  Briefcase, Code, PenTool, Search, 
  Clock, Database, Users, Settings, 
  CheckCircle, ChevronRight, ChevronLeft,
  Terminal, Monitor, Zap, Layout
} from 'lucide-react';
import { providerService } from '../../services/providerService';

const Onboarding = ({ user, onComplete }) => {
  const [step, setStep] = useState(1);
  const [selections, setSelections] = useState({
    useCase: 'universal',
    techLevel: 'standard',
    tools: ['agent', 'tasks', 'files', 'browser'],
    provider: null
  });

  const useCases = [
    { id: 'universal', name: 'Universal Workspace', icon: Layout, desc: 'General purpose AI assistance' },
    { id: 'coding', name: 'Coding & Software', icon: Code, desc: 'Deep technical workflows' },
    { id: 'business', name: 'Business Operations', icon: Briefcase, desc: 'Strategic planning & ops' },
    { id: 'content', name: 'Content Creation', icon: PenTool, desc: 'Writing and creative work' },
    { id: 'research', name: 'Research & Analysis', icon: Search, desc: 'Information synthesis' },
    { id: 'daily', name: 'Daily Workflow', icon: Clock, desc: 'Personal productivity' },
    { id: 'data', name: 'Data Analysis', icon: Database, desc: 'Insights from numbers' },
    { id: 'sales', name: 'Sales & Support', icon: Users, desc: 'Customer relations' }
  ];

  const techLevels = [
    { id: 'simple', name: 'Simple', desc: 'Minimalist UI, hidden advanced tools' },
    { id: 'standard', name: 'Standard', desc: 'Balanced experience for professionals' },
    { id: 'power', name: 'Power User', desc: 'Full control and automation' },
    { id: 'developer', name: 'Developer', desc: 'Terminal, Git, and system logs' }
  ];

  const nextStep = () => setStep(s => s + 1);
  const prevStep = () => setStep(s => s - 1);

  const renderStep = () => {
    switch(step) {
      case 1:
        return (
          <div className="fade-in">
            <h2 style={{ fontSize: '1.5rem', marginBottom: 'var(--space-md)' }}>What are you here to do?</h2>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-md)' }}>
              {useCases.map(item => (
                <div 
                  key={item.id} 
                  className={`card ${selections.useCase === item.id ? 'active' : ''}`}
                  onClick={() => setSelections({...selections, useCase: item.id})}
                  style={{ 
                    cursor: 'pointer', 
                    borderColor: selections.useCase === item.id ? 'var(--accent-primary)' : 'var(--border-subtle)',
                    background: selections.useCase === item.id ? 'rgba(59, 130, 246, 0.05)' : 'var(--bg-secondary)',
                    padding: 'var(--space-md)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--space-md)'
                  }}
                >
                  <div style={{ 
                    background: selections.useCase === item.id ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
                    padding: 'var(--space-sm)',
                    borderRadius: 'var(--radius-md)',
                    color: selections.useCase === item.id ? 'white' : 'var(--text-secondary)'
                  }}>
                    <item.icon size={24} />
                  </div>
                  <div style={{ textAlign: 'left' }}>
                    <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{item.name}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>{item.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      case 2:
        return (
          <div className="fade-in">
            <h2 style={{ fontSize: '1.5rem', marginBottom: 'var(--space-md)' }}>Technical Experience</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
              {techLevels.map(item => (
                <div 
                  key={item.id} 
                  className={`card ${selections.techLevel === item.id ? 'active' : ''}`}
                  onClick={() => setSelections({...selections, techLevel: item.id})}
                  style={{ 
                    cursor: 'pointer', 
                    borderColor: selections.techLevel === item.id ? 'var(--accent-primary)' : 'var(--border-subtle)',
                    background: selections.techLevel === item.id ? 'rgba(59, 130, 246, 0.05)' : 'var(--bg-secondary)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <div style={{ textAlign: 'left' }}>
                    <div style={{ fontWeight: 600 }}>{item.name}</div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{item.desc}</div>
                  </div>
                  {selections.techLevel === item.id && <CheckCircle size={20} color="var(--accent-primary)" />}
                </div>
              ))}
            </div>
          </div>
        );
      case 3:
        return (
          <div className="fade-in">
            <h2 style={{ fontSize: '1.5rem', marginBottom: 'var(--space-md)' }}>Connect AI Provider</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: 'var(--space-lg)' }}>
              You can connect a provider now or skip this step.
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-md)' }}>
              {providerService.getAvailableProviders().slice(0, 4).map(p => (
                <div key={p.id} className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-sm)', padding: 'var(--space-lg)' }}>
                  <div style={{ padding: 'var(--space-md)', background: 'var(--bg-tertiary)', borderRadius: '50%' }}>
                    <Zap size={32} color="var(--text-secondary)" />
                  </div>
                  <div style={{ fontWeight: 600 }}>{p.name}</div>
                  <button className="btn btn-secondary" style={{ fontSize: '0.8rem' }}>Connect</button>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 'var(--space-xl)' }}>
              <button className="btn btn-ghost" onClick={onComplete}>Skip for now</button>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--bg-primary)',
      padding: 'var(--space-md)'
    }}>
      <div style={{ width: '100%', maxWidth: '700px', textAlign: 'center' }}>
        <div style={{ marginBottom: 'var(--space-xl)' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginBottom: 'var(--space-sm)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
            Step {step} of 3
          </div>
          <div style={{ width: '100%', height: '4px', background: 'var(--bg-tertiary)', borderRadius: '2px', overflow: 'hidden' }}>
            <div style={{ width: `${(step / 3) * 100}%`, height: '100%', background: 'var(--accent-primary)', transition: 'all 0.3s ease' }} />
          </div>
        </div>

        <div style={{ minHeight: '400px' }}>
          {renderStep()}
        </div>

        <div style={{ 
          marginTop: 'var(--space-xl)', 
          display: 'flex', 
          justifyContent: step > 1 ? 'space-between' : 'flex-end',
          borderTop: '1px solid var(--border-subtle)',
          paddingTop: 'var(--space-lg)'
        }}>
          {step > 1 && (
            <button className="btn btn-secondary" onClick={prevStep}>
              <ChevronLeft size={18} /> Back
            </button>
          )}
          
          {step < 3 ? (
            <button className="btn btn-primary" onClick={nextStep}>
              Next <ChevronRight size={18} />
            </button>
          ) : (
            <button className="btn btn-primary" onClick={onComplete}>
              Complete Setup <CheckCircle size={18} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Onboarding;
