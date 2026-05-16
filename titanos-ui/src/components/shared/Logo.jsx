import React from 'react';
import { Zap } from 'lucide-react';

const Logo = ({ size = 24, showText = true }) => {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
      <div style={{ 
        width: size, 
        height: size, 
        background: 'var(--accent-primary)', 
        borderRadius: size * 0.2, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        boxShadow: '0 0 15px var(--accent-glow)'
      }}>
        <Zap size={size * 0.6} color="white" fill="white" />
      </div>
      {showText && (
        <span style={{ 
          fontWeight: 800, 
          fontSize: size * 0.75, 
          letterSpacing: '-0.04em',
          background: 'linear-gradient(to bottom, #fff, #888)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          TITANOS
        </span>
      )}
    </div>
  );
};

export default Logo;
