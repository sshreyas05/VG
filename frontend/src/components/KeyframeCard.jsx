import React, { useState, useCallback } from 'react';
import { useStudio } from '../context/StudioContext';

export default function KeyframeCard({ keyframe, onGenerate }) {
  const { updateKeyframe, removeKeyframe, setSelected, state } = useStudio();
  const [isEditing, setIsEditing] = useState(false);
  const isSelected = state.selectedItemId === keyframe.id;

  const handlePromptChange = useCallback((e) => {
    updateKeyframe({ id: keyframe.id, prompt: e.target.value });
  }, [keyframe.id, updateKeyframe]);

  const handleDurationChange = useCallback((e) => {
    const val = parseFloat(e.target.value);
    if (!isNaN(val) && val > 0) {
      updateKeyframe({ id: keyframe.id, duration: val });
    }
  }, [keyframe.id, updateKeyframe]);

  const handleDelete = useCallback(() => {
    if (window.confirm(`Delete Scene ${keyframe.sceneNumber}?`)) {
      removeKeyframe(keyframe.id);
    }
  }, [keyframe.id, keyframe.sceneNumber, removeKeyframe]);

  return (
    <div
      className={`keyframe-card ${isSelected ? 'keyframe-card--selected' : ''}`}
      onClick={() => setSelected(keyframe.id)}
      id={`keyframe-${keyframe.id}`}
    >
      {/* Scene Badge */}
      <div className="keyframe-card__scene-badge">
        Scene {keyframe.sceneNumber}
      </div>

      {/* Preview Area */}
      <div className="keyframe-card__preview">
        {keyframe.imageUrl ? (
          <img src={keyframe.imageUrl} alt={`Scene ${keyframe.sceneNumber}`} />
        ) : (
          <div className="keyframe-card__preview-placeholder">
            <span className="material-icons-round">image</span>
            <span>No image yet</span>
          </div>
        )}

        {/* Generating overlay */}
        {keyframe.status === 'generating' && (
          <div className="keyframe-card__generating">
            <div className="spinner" />
            <span>Generating…</span>
          </div>
        )}
      </div>

      {/* Body */}
      <div className="keyframe-card__body">
        <div className="keyframe-card__prompt-label">Keyframe Prompt</div>
        <textarea
          className="keyframe-card__prompt"
          value={keyframe.prompt}
          onChange={handlePromptChange}
          placeholder="Describe this scene…"
          rows={3}
          id={`prompt-${keyframe.id}`}
        />

        {/* Action buttons */}
        <div className="keyframe-card__actions">
          <button
            className="btn btn--primary btn--sm"
            onClick={(e) => { e.stopPropagation(); onGenerate(); }}
            disabled={!keyframe.prompt.trim() || keyframe.status === 'generating'}
            id={`gen-${keyframe.id}`}
          >
            <span className="material-icons-round" style={{ fontSize: 14 }}>
              {keyframe.status === 'done' ? 'refresh' : 'auto_fix_high'}
            </span>
            {keyframe.status === 'done' ? 'Regen' : 'Generate'}
          </button>
          <button
            className="btn btn--danger btn--sm"
            onClick={(e) => { e.stopPropagation(); handleDelete(); }}
            id={`del-${keyframe.id}`}
          >
            <span className="material-icons-round" style={{ fontSize: 14 }}>delete</span>
          </button>
        </div>

        {/* Duration */}
        <div className="keyframe-card__duration">
          <label>Duration</label>
          <input
            type="number"
            value={keyframe.duration}
            onChange={handleDurationChange}
            min="1"
            max="30"
            step="0.5"
          />
          <span>sec</span>

          {/* Status badge */}
          {keyframe.status !== 'idle' && (
            <span
              className={`status-badge status-badge--${keyframe.status}`}
              style={{ marginLeft: 'auto' }}
            >
              {keyframe.status === 'done' && <span className="material-icons-round" style={{ fontSize: 10 }}>check_circle</span>}
              {keyframe.status === 'error' && <span className="material-icons-round" style={{ fontSize: 10 }}>error</span>}
              {keyframe.status === 'generating' && <span className="material-icons-round" style={{ fontSize: 10 }}>hourglass_top</span>}
              {keyframe.status}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
