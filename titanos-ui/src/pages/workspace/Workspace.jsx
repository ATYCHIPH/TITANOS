import { useState } from 'react';
import AppShell from '../../components/layout/AppShell';
import AgentCommandCenter from '../../components/workspace/AgentCommandCenter';
import WorkspaceCanvas from '../../components/workspace/WorkspaceCanvas';
import RightPanel from '../../components/workspace/RightPanel';
import ActivityPanel from '../../components/workspace/ActivityPanel';
import { apiService } from '../../services/apiService';

const WorkspaceContent = ({ activeWorkspace = 'universal' }) => {
  const [activePanel, setActivePanel] = useState('status');
  const [isActivityExpanded, setIsActivityExpanded] = useState(false);
  const [conversation, setConversation] = useState([]);
  const [currentTask, setCurrentTask] = useState(null);
  const [sessionId, setSessionId] = useState(null);

  const handleCommand = async (command) => {
    const newTask = {
      id: Math.random().toString(36).substr(2, 9),
      title: command,
      status: 'running',
      progress: 25,
      startTime: new Date().toISOString()
    };
    setCurrentTask(newTask);
    setConversation(prev => [...prev, { type: 'user', content: command }]);

    try {
      const result = await apiService.chat({
        goal: command,
        session_id: sessionId,
        context: conversation.slice(-8).map((msg) => `${msg.type}: ${msg.content}`)
      });
      if (result.session_id) {
        setSessionId(result.session_id);
      }
      setConversation(prev => [...prev, {
        type: 'agent',
        content: result.response,
        system: result.system,
        status: result.status,
        plan: [
          { id: 1, title: `Routed to ${result.system}`, status: 'completed' },
          { id: 2, title: result.status === 'success' ? 'Response synthesized' : 'Needs operator attention', status: result.status === 'success' ? 'completed' : 'running' }
        ]
      }]);
      setCurrentTask(prev => prev ? { ...prev, status: result.status, progress: 100 } : prev);
    } catch (error) {
      setConversation(prev => [...prev, {
        type: 'agent',
        content: `I could not reach the TITANOS brain: ${error.message}`,
        system: 'runtime',
        status: 'error'
      }]);
      setCurrentTask(prev => prev ? { ...prev, status: 'error', progress: 100 } : prev);
    }
  };

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', minWidth: 0 }}>
      <div className="workspace-dashboard" style={{ flex: 1 }}>
        <div className="workspace-pane" style={{ display: 'flex', flexDirection: 'column' }}>
          <AgentCommandCenter onCommand={handleCommand} conversation={conversation} />
        </div>

        <div className="workspace-pane" style={{ position: 'relative', minWidth: 0 }}>
          <WorkspaceCanvas activeWorkspace={activeWorkspace} currentTask={currentTask} />
        </div>

        <div className="workspace-pane" style={{ display: 'flex', flexDirection: 'column' }}>
          <RightPanel activePanel={activePanel} onPanelChange={setActivePanel} />
        </div>
      </div>

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
  );
};

const Workspace = () => (
  <AppShell>
    <WorkspaceContent />
  </AppShell>
);

export default Workspace;
