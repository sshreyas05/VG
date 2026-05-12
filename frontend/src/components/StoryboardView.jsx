import React, { useState, useCallback } from 'react';
import { useStudio } from '../context/StudioContext';
import KeyframeCard from './KeyframeCard';
import TransitionCard from './TransitionCard';
import { generateFull } from '../utils/api';

export default function StoryboardView() {
  const {
    state,
    setFilmIdea,
    addKeyframe,
    updateKeyframe,
    addJob,
    updateJob,
    loadScript,
  } = useStudio();

  const [isEnhancing, setIsEnhancing] = useState(false);
  const [duration, setDuration] = useState(10);
  const handleGenerateFull = useCallback(async () => {
    if (!state.filmIdea.trim() || isEnhancing) return;
    setIsEnhancing(true);
    try {
      const result = await generateFull(state.filmIdea, duration);
      addJob({
        id: result.job_id,
        type: 'export',
        status: 'running',
        message: 'Running End-to-End Pipeline (Modal.com)'
      });
    } catch (err) {
      console.error('End-to-End failed:', err);
    } finally {
      setIsEnhancing(false);
    }
  }, [state.filmIdea, duration, isEnhancing, addJob]);

  return (
    <div className="storyboard" id="storyboard-view">
      {/* Header */}
      <div className="storyboard__header">
        <h2>
          <span className="material-icons-round" style={{ fontSize: 22, verticalAlign: 'middle', marginRight: 8, color: 'var(--accent-light)' }}>
            auto_stories
          </span>
          Storyboard
        </h2>
        <div className="storyboard__header-actions">
        </div>
      </div>

      {/* Film Idea Input */}
      <div className="storyboard__idea-bar">
        <div className="storyboard__idea-input-wrap">
          <span className="material-icons-round" style={{ color: 'var(--accent-light)', fontSize: 20 }}>
            psychology
          </span>
          <input
            className="storyboard__idea-input"
            type="text"
            placeholder="Describe your film idea… e.g. 'A lone astronaut discovers an ancient temple on Mars'"
            value={state.filmIdea}
            onChange={(e) => setFilmIdea(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleGenerateFull()}
            id="input-film-idea"
            style={{ flex: 1 }}
          />
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, margin: '0 8px' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Length:</span>
            <input 
              type="number" 
              value={duration} 
              onChange={e => setDuration(Number(e.target.value))} 
              style={{ width: 60, padding: '4px 8px', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--bg-card)', color: 'var(--text)' }} 
              min={5} 
              step={5} 
            />
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>s</span>
          </div>
          <button
            className="btn btn--primary btn--md"
            onClick={handleGenerateFull}
            disabled={!state.filmIdea.trim() || isEnhancing}
            id="btn-enhance-idea"
          >
            {isEnhancing ? 'Starting Job…' : 'Generate Full Video'}
          </button>
        </div>
      </div>

    </div>
  );
}
