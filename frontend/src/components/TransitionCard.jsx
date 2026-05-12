import React, { useCallback } from 'react';
import { useStudio } from '../context/StudioContext';
import { generateTransition } from '../utils/api';

export default function TransitionCard({ transition }) {
  const { updateTransition, addJob, updateJob, state } = useStudio();

  const handlePromptChange = useCallback((e) => {
    updateTransition({ id: transition.id, prompt: e.target.value });
  }, [transition.id, updateTransition]);

  const handleGenerate = useCallback(async () => {
    // Find the source keyframe's image
    const fromKf = state.keyframes.find(k => k.id === transition.fromKeyframeId);
    if (!fromKf?.imageUrl) {
      alert('Generate the source keyframe image first!');
      return;
    }
    if (!transition.prompt.trim()) return;

    updateTransition({ id: transition.id, status: 'generating' });

    try {
      const result = await generateTransition(transition.id, fromKf.imageUrl, transition.prompt);
      // Use the backend's job_id so WebSocket updates match
      const backendJobId = result.job_id;
      addJob({
        id: backendJobId,
        type: 'transition',
        targetId: transition.id,
        message: 'Rendering transition video…',
        status: 'running',
      });
      // The WebSocket will update this job when the background task finishes
    } catch (err) {
      updateTransition({ id: transition.id, status: 'error' });
    }
  }, [transition, state.keyframes, updateTransition, addJob, updateJob]);

  return (
    <div className="transition-card" id={`transition-${transition.id}`}>
      <div className="transition-card__line" />
      <div className="transition-card__content">
        <span className="material-icons-round transition-card__icon">
          {transition.status === 'done' ? 'check_circle' : 'swap_horiz'}
        </span>
        <textarea
          className="transition-card__prompt"
          value={transition.prompt}
          onChange={handlePromptChange}
          placeholder="Transition prompt…"
          rows={2}
        />
        <div className="transition-card__actions">
          <button
            className="btn btn--secondary btn--sm"
            onClick={handleGenerate}
            disabled={transition.status === 'generating' || !transition.prompt.trim()}
            style={{ fontSize: '0.65rem', padding: '4px 8px' }}
          >
            {transition.status === 'generating' ? (
              <div className="spinner" style={{ width: 10, height: 10, borderWidth: 1.5 }} />
            ) : (
              <span className="material-icons-round" style={{ fontSize: 12 }}>videocam</span>
            )}
            {transition.status === 'done' ? 'Regen' : 'Render'}
          </button>
        </div>
        {transition.status === 'done' && (
          <div className="transition-card__status">
            <span className="material-icons-round">check</span>
            Video ready
          </div>
        )}
      </div>
    </div>
  );
}
