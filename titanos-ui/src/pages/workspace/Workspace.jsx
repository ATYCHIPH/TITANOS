import React, { useState } from 'react';
import AppShell from '../../components/layout/AppShell';
import AgentCommandCenter from '../../components/workspace/AgentCommandCenter';
import WorkspaceCanvas from '../../components/workspace/WorkspaceCanvas';
import RightPanel from '../../components/workspace/RightPanel';
import ActivityPanel from '../../components/workspace/ActivityPanel';

const Workspace = ({ user, onLogout }) => {
  const [activePanel, setActivePanel] = useState('editor');
  const [isActivityExpanded, setIsActivityExpanded] = useState(false);
  const [conversation, setConversation] = useState([]);
  const [currentTask, setCurrentTask] = useState(null);

  const handleCommand = (command) => {
    // Mock processing
    const newTask = {
      id: Math.random().toString(36).substr(2, 9),
      title: command,
      status: 'running',
      progress: 25,
      startTime: new Date().toISOString()
    };
    setCurrentTask(newTask);
    setConversation([...conversation, { type: 'user', content: command }]);
    
    // Simulate agent response
    setTimeout(() => {
      setConversation(prev => [...prev, { 
        type: 'agent', 
        content: "I've started working on that. I'll need to research some competitors first.",
        plan: [
          { id: 1, title: 'Analyze market trends', status: 'completed' },
          { id: 2, title: 'Identify top 5 competitors', status: 'running' },
          { id: 3, title: 'Synthesize feature comparison', status: 'pending' }
        ]
      }]);
    }, 1000);
  };

  return (
    <AppShell user={user} onLogout={onLogout}>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%' }}>
        {/* Main Split Layout */}
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          {/* Left: Interaction Pane */}
          <div style={{ 
            width: '450px', 
            borderRight: '1px solid var(--border-subtle)', 
            display: 'flex', 
            flexDirection: 'column',
            background: 'rgba(255,255,255,0.01)'
          }}>
            <AgentCommandCenter onCommand={handleCommand} conversation={conversation} />
          </div>

          {/* Middle: Execution Pane (Canvas) */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--bg-primary)' }}>
            <WorkspaceCanvas activePanel={activePanel} currentTask={currentTask} />
          </div>

          {/* Right: Contextual Panel */}
          <div style={{ 
            width: '320px', 
            borderLeft: '1px solid var(--border-subtle)', 
            display: 'flex', 
            flexDirection: 'column',
            background: 'var(--bg-secondary)'
          }}>
            <RightPanel activePanel={activePanel} onPanelChange={setActivePanel} />
          </div>
        </div>

        {/* Bottom: Activity/Logs Panel */}
        <div style={{ 
          height: isActivityExpanded ? '300px' : '40px', 
          borderTop: '1px solid var(--border-subtle)',
          transition: 'height 0.3s ease',
          background: 'var(--bg-secondary)',
          zIndex: 40
        }}>
          <ActivityPanel 
            isExpanded={isActivityExpanded} 
            onToggle={() => setIsActivityExpanded(!isActivityExpanded)} 
          />
        </div>
      </div>
    </AppShell>
  );
};

export default Workspace;
