import React from 'react';
import { useStudio } from '../context/StudioContext';

export default function Toolbar() {
  const { state, setView, setExportModal } = useStudio();

  return (
    <header className="toolbar" id="toolbar">
      {/* Brand */}
      <div className="toolbar__brand">
        <div className="toolbar__logo">
          <span className="material-icons-round" style={{ fontSize: 18, color: 'white' }}>
            movie_creation
          </span>
        </div>
        <span className="toolbar__title">AI Film Studio</span>
      </div>

      {/* View Switcher */}
      <nav className="toolbar__center" id="view-switcher">
        <button
          className={`toolbar__view-btn ${state.currentView === 'storyboard' ? 'toolbar__view-btn--active' : ''}`}
          onClick={() => setView('storyboard')}
          id="btn-storyboard-view"
        >
          <span className="material-icons-round" style={{ fontSize: 16 }}>view_comfy</span>
          Storyboard
        </button>
        <button
          className={`toolbar__view-btn ${state.currentView === 'timeline' ? 'toolbar__view-btn--active' : ''}`}
          onClick={() => setView('timeline')}
          id="btn-timeline-view"
        >
          <span className="material-icons-round" style={{ fontSize: 16 }}>timeline</span>
          Timeline
        </button>
      </nav>

      {/* Actions */}
      <div className="toolbar__actions">
        {/* Connection status */}
        <div
          className={`connection-dot ${
            state.wsConnected ? 'connection-dot--connected' : 'connection-dot--disconnected'
          }`}
          data-tooltip={state.wsConnected ? 'Backend Connected' : 'Backend Offline'}
        />

        {/* Export button */}
        <button
          className="btn btn--primary btn--md"
          onClick={() => setExportModal(true)}
          id="btn-export"
          disabled={state.keyframes.length === 0}
        >
          <span className="material-icons-round" style={{ fontSize: 16 }}>file_download</span>
          Export
        </button>
      </div>
    </header>
  );
}
