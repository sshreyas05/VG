import React from 'react';
import { useStudio } from './context/StudioContext';
import { useWebSocket } from './hooks/useWebSocket';
import Toolbar from './components/Toolbar';
import StoryboardView from './components/StoryboardView';
import TimelineView from './components/TimelineView';
import JobMonitor from './components/JobMonitor';
import ExportModal from './components/ExportModal';

export default function App() {
  const { state } = useStudio();

  // Initialize WebSocket connection
  useWebSocket();

  return (
    <>
      <Toolbar />
      <main className="main-content">
        {state.currentView === 'storyboard' ? (
          <StoryboardView />
        ) : (
          <TimelineView />
        )}
      </main>

      {/* Floating job monitor */}
      {state.jobs.length > 0 && <JobMonitor />}

      {/* Export modal */}
      {state.exportModalOpen && <ExportModal />}
    </>
  );
}
