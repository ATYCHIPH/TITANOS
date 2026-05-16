import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { authService } from './services/authService';

// Pages (to be created)
const Login = React.lazy(() => import('./pages/auth/Login'));
const Signup = React.lazy(() => import('./pages/auth/Signup'));
const Onboarding = React.lazy(() => import('./pages/onboarding/Onboarding'));
const Workspace = React.lazy(() => import('./pages/workspace/Workspace'));
const Settings = React.lazy(() => import('./pages/settings/Settings'));

function App() {
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Check initial auth state
    const currentUser = authService.getCurrentUser();
    setUser(currentUser);
    setLoading(false);
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    if (userData.onboarded) {
      navigate('/workspace');
    } else {
      navigate('/onboarding');
    }
  };

  const handleLogout = () => {
    authService.logout();
    setUser(null);
    navigate('/login');
  };

  if (loading) {
    return (
      <div style={{ 
        height: '100vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        background: 'var(--bg-primary)',
        color: 'var(--text-primary)'
      }}>
        <div className="loader">Loading TITANOS...</div>
      </div>
    );
  }

  return (
    <React.Suspense fallback={<div>Loading...</div>}>
      <Routes>
        <Route path="/login" element={!user ? <Login onLogin={handleLogin} /> : <Navigate to="/workspace" />} />
        <Route path="/signup" element={!user ? <Signup onLogin={handleLogin} /> : <Navigate to="/workspace" />} />
        
        <Route 
          path="/onboarding" 
          element={user ? <Onboarding user={user} onComplete={() => {
            authService.completeOnboarding();
            setUser({...user, onboarded: true});
            navigate('/workspace');
          }} /> : <Navigate to="/login" />} 
        />
        
        <Route 
          path="/workspace/*" 
          element={user ? (
            user.onboarded ? <Workspace user={user} onLogout={handleLogout} /> : <Navigate to="/onboarding" />
          ) : <Navigate to="/login" />} 
        />

        <Route 
          path="/settings/*" 
          element={user ? <Settings user={user} /> : <Navigate to="/login" />} 
        />

        <Route path="/" element={<Navigate to={user ? "/workspace" : "/login"} />} />
      </Routes>
    </React.Suspense>
  );
}

export default App;
