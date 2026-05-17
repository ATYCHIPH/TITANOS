import { lazy, Suspense, useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

const Onboarding = lazy(() => import('./pages/onboarding/Onboarding'));
const Workspace = lazy(() => import('./pages/workspace/Workspace'));
const Settings = lazy(() => import('./pages/settings/Settings'));

function App() {
  const [onboarded, setOnboarded] = useState(() => {
    return localStorage.getItem('titanos_onboarded') === 'true';
  });

  const handleCompleteOnboarding = () => {
    localStorage.setItem('titanos_onboarded', 'true');
    setOnboarded(true);
  };

  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Routes>
        <Route 
          path="/onboarding" 
          element={!onboarded ? <Onboarding onComplete={handleCompleteOnboarding} /> : <Navigate to="/workspace" />} 
        />
        
        <Route 
          path="/workspace/*" 
          element={onboarded ? <Workspace /> : <Navigate to="/onboarding" />} 
        />

        <Route 
          path="/settings/*" 
          element={onboarded ? <Settings /> : <Navigate to="/onboarding" />} 
        />

        <Route path="/" element={<Navigate to={onboarded ? "/workspace" : "/onboarding"} />} />
      </Routes>
    </Suspense>
  );
}

export default App;
