import React, { useState, useCallback } from 'react';
import { useStudio } from '../context/StudioContext';
import { exportFilm } from '../utils/api';

export default function ExportModal() {
  const { setExportModal, addJob, updateJob, state } = useStudio();
  const [format, setFormat] = useState('mp4');
  const [resolution, setResolution] = useState('1920x1080');
  const [fps, setFps] = useState(24);
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = useCallback(async () => {
    setIsExporting(true);
    try {
      const clips = state.transitions.map(t => t.videoUrl).filter(Boolean);
      const result = await exportFilm({ format, resolution, fps, clips });
      // Use the job_id from the backend
      addJob({
        id: result.job_id,
        type: 'export',
        message: 'Preparing export…',
        status: 'running',
        ...result
      });
    } catch (err) {
      console.error('Export failed:', err);
    } finally {
      setIsExporting(false);
      setExportModal(false);
    }
  }, [format, resolution, fps, state.transitions, addJob, updateJob, setExportModal]);

  // Calculate film stats
  const totalScenes = state.keyframes.length;
  const totalDuration = state.keyframes.reduce((s, k) => s + k.duration, 0)
    + state.transitions.reduce((s, t) => s + t.duration, 0);
  const audioTracks = state.audioLayers.length;

  return (
    <div className="modal-overlay" onClick={() => !isExporting && setExportModal(false)}>
      <div className="modal" onClick={(e) => e.stopPropagation()} id="export-modal">
        <div className="modal__header">
          <h3 className="modal__title">
            <span className="material-icons-round">movie_creation</span>
            Export Film
          </h3>
          {!isExporting && (
            <button
              className="btn btn--icon"
              onClick={() => setExportModal(false)}
            >
              <span className="material-icons-round">close</span>
            </button>
          )}
        </div>

        <div className="modal__body">
          {/* Stats summary */}
          <div style={{
            display: 'flex',
            gap: 16,
            marginBottom: 24,
            padding: '14px 16px',
            background: 'var(--bg-glass)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border)',
          }}>
            <div style={{ textAlign: 'center', flex: 1 }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-display)', color: 'var(--accent-light)' }}>
                {totalScenes}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Scenes
              </div>
            </div>
            <div style={{ width: 1, background: 'var(--border)' }} />
            <div style={{ textAlign: 'center', flex: 1 }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-display)', color: 'var(--accent-cyan)' }}>
                {totalDuration.toFixed(1)}s
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Duration
              </div>
            </div>
            <div style={{ width: 1, background: 'var(--border)' }} />
            <div style={{ textAlign: 'center', flex: 1 }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-display)', color: 'var(--accent-pink)' }}>
                {audioTracks}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Audio
              </div>
            </div>
          </div>

          {/* Format */}
          <div className="modal__field">
            <label>Format</label>
            <select value={format} onChange={(e) => setFormat(e.target.value)} id="export-format">
              <option value="mp4">MP4 (H.264)</option>
              <option value="webm">WebM (VP9)</option>
              <option value="mov">MOV (ProRes)</option>
            </select>
          </div>

          {/* Resolution */}
          <div className="modal__field">
            <label>Resolution</label>
            <select value={resolution} onChange={(e) => setResolution(e.target.value)} id="export-resolution">
              <option value="3840x2160">4K (3840×2160)</option>
              <option value="1920x1080">Full HD (1920×1080)</option>
              <option value="1280x720">HD (1280×720)</option>
              <option value="854x480">SD (854×480)</option>
            </select>
          </div>

          {/* FPS */}
          <div className="modal__field">
            <label>Frame Rate</label>
            <select value={fps} onChange={(e) => setFps(parseInt(e.target.value))} id="export-fps">
              <option value={60}>60 fps</option>
              <option value={30}>30 fps</option>
              <option value={24}>24 fps (Cinematic)</option>
            </select>
          </div>
        </div>

        <div className="modal__footer">
          <button
            className="btn btn--secondary btn--md"
            onClick={() => setExportModal(false)}
            disabled={isExporting}
          >
            Cancel
          </button>
          <button
            className="btn btn--primary btn--md"
            onClick={handleExport}
            disabled={isExporting || totalScenes === 0}
            id="btn-start-export"
          >
            {isExporting ? (
              <>
                <div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
                Exporting…
              </>
            ) : (
              <>
                <span className="material-icons-round" style={{ fontSize: 16 }}>file_download</span>
                Start Export
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
