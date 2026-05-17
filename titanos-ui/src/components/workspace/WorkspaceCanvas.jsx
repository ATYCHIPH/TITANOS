import {
  Activity,
  BarChart3,
  Brain,
  CheckCircle2,
  Database,
  FileCode,
  FileText,
  GitBranch,
  Globe,
  Layers,
  Play,
  RefreshCw,
  Route,
  Save,
  Search,
  ShieldCheck,
  Table2,
  Workflow,
  Zap
} from 'lucide-react';

const workspaceMeta = {
  universal: {
    label: 'Universal',
    eyebrow: 'Live agent graph',
    title: 'Body-System Orchestration',
    subtitle: 'Conversations, memory, execution, code work, and provider routing are connected through one runtime session.',
    path: 'Universal / orchestration',
    metrics: [['Body Links', '7'], ['Provider Presets', '22'], ['Mode', 'Desktop'], ['Session', 'Scoped']],
  },
  coding: {
    label: 'Coding',
    eyebrow: 'Code workspace',
    title: 'Repo Execution Console',
    subtitle: 'Plan code changes, inspect files, run tests, and keep command approvals visible in one engineering surface.',
    path: 'Coding / repo',
    metrics: [['Files', '128'], ['Tests', '22'], ['Approvals', '0'], ['Branch', 'master']],
  },
  business: {
    label: 'Business',
    eyebrow: 'Operations cockpit',
    title: 'Business Continuity Monitor',
    subtitle: 'Track execution health, approvals, risks, and provider failover for operational workflows.',
    path: 'Business / operations',
    metrics: [['Tasks', '14'], ['Risks', '2'], ['SLA', '99%'], ['Reports', '6']],
  },
  content: {
    label: 'Content',
    eyebrow: 'Publishing studio',
    title: 'Content Production Board',
    subtitle: 'Draft, review, enrich, and publish multi-format assets with memory-backed brand context.',
    path: 'Content / publishing',
    metrics: [['Drafts', '8'], ['Assets', '31'], ['Review', '3'], ['Ready', '5']],
  },
  research: {
    label: 'Research',
    eyebrow: 'Source synthesis',
    title: 'Research Intelligence Desk',
    subtitle: 'Collect sources, compare claims, extract notes, and turn citations into durable project memory.',
    path: 'Research / sources',
    metrics: [['Sources', '18'], ['Notes', '44'], ['Claims', '12'], ['Gaps', '3']],
  },
  data: {
    label: 'Data',
    eyebrow: 'Data workspace',
    title: 'Dataset Analysis Console',
    subtitle: 'Inspect tables, validate flows, visualize signals, and route anomalies into tasks.',
    path: 'Data / analytics',
    metrics: [['Rows', '40k'], ['Tables', '7'], ['Signals', '9'], ['Errors', '0']],
  },
  daily: {
    label: 'Workflow',
    eyebrow: 'Automation builder',
    title: 'Workflow Orchestration Canvas',
    subtitle: 'Design trigger chains, provider handoffs, fallbacks, and versioned automations from one canvas.',
    path: 'Workflow / builder',
    metrics: [['Nodes', '11'], ['Runs', '187'], ['Versions', '4'], ['Alerts', '1']],
  },
};

const commonNodes = [
  { id: 'voice', name: 'Voice', role: 'conversation', color: 'var(--accent-cyan)' },
  { id: 'memory', name: 'Memory', role: 'recall + session', color: 'var(--success)' },
  { id: 'cortex', name: 'Cortex', role: 'reasoning', color: 'var(--accent-violet)' },
  { id: 'hands', name: 'Hands', role: 'safe execution', color: 'var(--warning)' },
  { id: 'craft', name: 'Craft', role: 'code workflows', color: 'var(--accent-primary)' },
  { id: 'lab', name: 'Lab', role: 'experiments', color: '#f472b6' },
];

const codeRows = [
  ['TITANOS-core/titanos/brain.py', 'modified', 'Voice routing'],
  ['titanos-ui/src/pages/workspace/Workspace.jsx', 'modified', 'Workspace layout'],
  ['titanos-ui/src/components/workspace/WorkspaceCanvas.jsx', 'modified', 'Canvas variants'],
  ['tests/test_brain_lifecycle.py', 'passed', '22 tests'],
];

const contentRows = [
  ['Draft', 'Product launch notes', 'Review'],
  ['Asset', 'Glass dashboard hero', 'Ready'],
  ['Campaign', 'Provider routing explainer', 'Writing'],
  ['Brief', 'Desktop install flow', 'Approved'],
];

const researchRows = [
  ['Source', 'Provider APIs', 'verified'],
  ['Claim', 'Ollama-compatible routing', 'needs citation'],
  ['Note', 'Session memory behavior', 'accepted'],
  ['Gap', 'Long context synthesis', 'open'],
];

const dataRows = [
  ['provider_health', '22', 'healthy'],
  ['sessions', '104', 'active'],
  ['run_records', '187', 'stable'],
  ['audit_events', '1.2k', 'indexed'],
];

const WorkspaceCanvas = ({ activeWorkspace = 'universal', currentTask }) => {
  const meta = workspaceMeta[activeWorkspace] || workspaceMeta.universal;
  const progress = Math.max(8, Math.min(100, currentTask?.progress || 68));
  const status = currentTask?.status || 'ready';

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', minWidth: 0 }}>
      <div className="panel-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
          <div className="status-pill">
            <GitBranch size={14} />
            {meta.path}
          </div>
          <span className="eyebrow">{meta.eyebrow}</span>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-ghost" style={{ padding: '6px 10px', fontSize: '0.78rem' }}>
            <Save size={14} /> Save
          </button>
          <button className="btn btn-primary neon-button" style={{ padding: '6px 12px', fontSize: '0.78rem' }}>
            <Play size={14} /> Run
          </button>
        </div>
      </div>

      <div style={{
        flex: 1,
        overflow: 'auto',
        padding: 18,
        display: 'grid',
        gridTemplateRows: 'auto 1fr',
        gap: 14,
        minHeight: 0
      }}>
        <Hero meta={meta} />
        {activeWorkspace === 'coding' && <CodingWorkspace currentTask={currentTask} progress={progress} status={status} />}
        {activeWorkspace === 'business' && <BusinessWorkspace currentTask={currentTask} progress={progress} status={status} />}
        {activeWorkspace === 'content' && <TableWorkspace rows={contentRows} kind="content" currentTask={currentTask} progress={progress} status={status} />}
        {activeWorkspace === 'research' && <ResearchWorkspace currentTask={currentTask} progress={progress} status={status} />}
        {activeWorkspace === 'data' && <DataWorkspace currentTask={currentTask} progress={progress} status={status} />}
        {activeWorkspace === 'daily' && <WorkflowWorkspace currentTask={currentTask} progress={progress} status={status} />}
        {activeWorkspace === 'universal' && <UniversalWorkspace currentTask={currentTask} progress={progress} status={status} />}
      </div>
    </div>
  );
};

const Hero = ({ meta }) => (
  <section className="glass-tile" style={{
    padding: 18,
    display: 'grid',
    gridTemplateColumns: '1.2fr 0.8fr',
    gap: 16
  }}>
    <div>
      <div className="eyebrow">TITANOS {meta.label}</div>
      <h2 style={{ fontSize: '1.6rem', margin: '8px 0 8px', letterSpacing: 0 }}>{meta.title}</h2>
      <p style={{ color: 'var(--text-secondary)', lineHeight: 1.5, fontSize: '0.9rem', maxWidth: 620 }}>
        {meta.subtitle}
      </p>
    </div>
    <div className="metric-grid">
      {meta.metrics.map(([label, value]) => (
        <div className="metric-card" key={label}>
          <span className="eyebrow">{label}</span>
          <strong style={{ fontSize: value.length > 4 ? '1rem' : '1.35rem' }}>{value}</strong>
        </div>
      ))}
    </div>
  </section>
);

const UniversalWorkspace = ({ currentTask, progress, status }) => (
  <section style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 260px', gap: 14, minHeight: 0 }}>
    <div className="glass-tile" style={{ padding: 18, position: 'relative', overflow: 'hidden' }}>
      <SectionTitle icon={Route} label="Routing Graph" title="Intent to body-system flow" />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(130px, 1fr))', gap: 18 }}>
        {commonNodes.map((node) => <WorkflowNode key={node.id} node={node} />)}
      </div>
    </div>
    <TaskCard currentTask={currentTask} progress={progress} status={status} />
  </section>
);

const CodingWorkspace = ({ currentTask, progress, status }) => (
  <section style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.25fr) minmax(240px, 0.75fr)', gap: 14, minHeight: 0 }}>
    <div className="glass-tile" style={{ display: 'grid', gridTemplateRows: '44px 1fr', overflow: 'hidden' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '0 14px', borderBottom: '1px solid var(--border-subtle)' }}>
        <FileCode size={16} color="var(--accent-cyan)" />
        <span className="eyebrow">Editor + Diff</span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '220px 1fr', minHeight: 0 }}>
        <div style={{ borderRight: '1px solid var(--border-subtle)', padding: 12, display: 'grid', gap: 8, alignContent: 'start' }}>
          {codeRows.map(([file, state]) => (
            <div key={file} style={{ display: 'flex', justifyContent: 'space-between', gap: 8, fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{file}</span>
              <span style={{ color: state === 'passed' ? 'var(--success)' : 'var(--warning)' }}>{state}</span>
            </div>
          ))}
        </div>
        <pre style={{ margin: 0, padding: 16, overflow: 'auto', color: '#d8e3ff', fontSize: '0.82rem', lineHeight: 1.55 }}>{`const routeIntent = (message) => {
  if (isConversation(message)) return "voice";
  if (isMemoryCommand(message)) return "memory";
  return "cortex";
};

await titanos.chat({
  sessionId,
  workspace: "coding",
  context: recentTurns
});`}</pre>
      </div>
    </div>
    <TaskCard currentTask={currentTask} progress={progress} status={status} />
  </section>
);

const BusinessWorkspace = ({ currentTask, progress, status }) => (
  <section style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 260px', gap: 14 }}>
    <div className="glass-tile" style={{ padding: 18, display: 'grid', gap: 14 }}>
      <SectionTitle icon={BarChart3} label="Continuity" title="Operations health and failover" />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
        {['Provider SLA', 'Approval Load', 'Run Success'].map((label, index) => (
          <div className="metric-card" key={label}>
            <span className="eyebrow">{label}</span>
            <strong>{['99%', '2', '96%'][index]}</strong>
          </div>
        ))}
      </div>
      <SignalChart />
    </div>
    <TaskCard currentTask={currentTask} progress={progress} status={status} />
  </section>
);

const ResearchWorkspace = ({ currentTask, progress, status }) => (
  <section style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 260px', gap: 14 }}>
    <div className="glass-tile" style={{ padding: 18 }}>
      <SectionTitle icon={Search} label="Research Board" title="Sources, claims, and synthesis queue" />
      <WorkspaceTable headers={['Type', 'Item', 'Status']} rows={researchRows} />
    </div>
    <TaskCard currentTask={currentTask} progress={progress} status={status} />
  </section>
);

const DataWorkspace = ({ currentTask, progress, status }) => (
  <section style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 260px', gap: 14 }}>
    <div className="glass-tile" style={{ padding: 18 }}>
      <SectionTitle icon={Table2} label="Data Console" title="Tables, signals, and pipeline health" />
      <WorkspaceTable headers={['Dataset', 'Rows', 'State']} rows={dataRows} />
      <SignalChart compact />
    </div>
    <TaskCard currentTask={currentTask} progress={progress} status={status} />
  </section>
);

const WorkflowWorkspace = ({ currentTask, progress, status }) => (
  <section style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 260px', gap: 14 }}>
    <div className="glass-tile" style={{ padding: 18 }}>
      <SectionTitle icon={Workflow} label="Builder" title="Trigger to provider handoff graph" />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(120px, 1fr))', gap: 18, marginTop: 16 }}>
        {[
          { name: 'Cron Trigger', role: 'schedule', color: 'var(--accent-violet)' },
          { name: 'Context Load', role: 'memory', color: 'var(--success)' },
          { name: 'Routing Agent', role: 'model pick', color: 'var(--accent-cyan)' },
          { name: 'Fallback Alert', role: 'notify', color: 'var(--warning)' },
        ].map((node) => <WorkflowNode key={node.name} node={node} />)}
      </div>
    </div>
    <TaskCard currentTask={currentTask} progress={progress} status={status} />
  </section>
);

const TableWorkspace = ({ rows, currentTask, progress, status }) => (
  <section style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 260px', gap: 14 }}>
    <div className="glass-tile" style={{ padding: 18 }}>
      <SectionTitle icon={FileText} label="Production Board" title="Drafts, assets, and approvals" />
      <WorkspaceTable headers={['Kind', 'Name', 'State']} rows={rows} />
    </div>
    <TaskCard currentTask={currentTask} progress={progress} status={status} />
  </section>
);

const SectionTitle = ({ icon: Icon, label, title }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
    <div>
      <div className="eyebrow" style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Icon size={14} /> {label}</div>
      <h3 style={{ fontSize: '1rem', marginTop: 5 }}>{title}</h3>
    </div>
    <div className="status-pill"><span className="status-dot" /> Connected</div>
  </div>
);

const WorkflowNode = ({ node }) => (
  <div className="workflow-node" style={{ borderColor: `${node.color}66` }}>
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
      <div style={{ width: 34, height: 34, borderRadius: 8, display: 'grid', placeItems: 'center', background: `${node.color}22`, color: node.color }}>
        {node.name === 'Cortex' ? <Brain size={18} /> : node.name === 'Hands' ? <ShieldCheck size={18} /> : <Route size={18} />}
      </div>
      <CheckCircle2 size={15} color="var(--success)" />
    </div>
    <div style={{ fontWeight: 700 }}>{node.name}</div>
    <div style={{ color: 'var(--text-tertiary)', fontSize: '0.76rem', marginTop: 4 }}>{node.role}</div>
  </div>
);

const TaskCard = ({ currentTask, progress, status }) => (
  <div className="glass-tile" style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
    <div>
      <div className="eyebrow">Current Task</div>
      <h3 style={{ fontSize: '1rem', marginTop: 5 }}>{currentTask?.title || 'Waiting for command'}</h3>
    </div>
    <div style={{ height: 7, borderRadius: 999, background: 'rgba(255,255,255,0.07)', overflow: 'hidden' }}>
      <div style={{ width: `${progress}%`, height: '100%', background: 'linear-gradient(90deg, var(--accent-cyan), var(--accent-primary), var(--accent-violet))' }} />
    </div>
    <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
      <span>{status}</span>
      <span>{progress}%</span>
    </div>
    <div style={{ marginTop: 'auto', display: 'grid', gap: 8 }}>
      {['Conversation classified', 'Session context attached', 'Provider route ready'].map((item) => (
        <div key={item} style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
          <Zap size={14} color="var(--accent-cyan)" /> {item}
        </div>
      ))}
    </div>
  </div>
);

const WorkspaceTable = ({ headers, rows }) => (
  <div style={{ display: 'grid', gap: 8 }}>
    <div style={{ display: 'grid', gridTemplateColumns: `repeat(${headers.length}, minmax(0, 1fr))`, gap: 8, color: 'var(--text-tertiary)', fontSize: '0.72rem', textTransform: 'uppercase' }}>
      {headers.map((header) => <div key={header}>{header}</div>)}
    </div>
    {rows.map((row) => (
      <div key={row.join('-')} className="metric-card" style={{ display: 'grid', gridTemplateColumns: `repeat(${row.length}, minmax(0, 1fr))`, gap: 8, fontSize: '0.82rem' }}>
        {row.map((cell, index) => <div key={`${cell}-${index}`} style={{ color: index === row.length - 1 ? 'var(--accent-cyan)' : 'var(--text-secondary)' }}>{cell}</div>)}
      </div>
    ))}
  </div>
);

const SignalChart = ({ compact = false }) => (
  <div style={{ height: compact ? 120 : 180, display: 'flex', alignItems: 'end', gap: 8, padding: '12px 0 0' }}>
    {[42, 58, 36, 77, 64, 88, 51, 72, 94, 67, 80, 74].map((value, index) => (
      <div key={index} style={{ flex: 1, height: `${value}%`, borderRadius: '8px 8px 2px 2px', background: 'linear-gradient(180deg, var(--accent-cyan), rgba(79,140,255,0.22))' }} />
    ))}
  </div>
);

export default WorkspaceCanvas;
