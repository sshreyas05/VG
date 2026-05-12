import React, { useMemo, useCallback, useRef, useEffect, useState } from 'react';
import { useStudio } from '../context/StudioContext';

const PIXELS_PER_SECOND = 80;
const TRACK_CONFIG = [
  { id: 'video', label: 'Video', icon: 'movie', iconClass: 'video' },
  { id: 'music', label: 'Music', icon: 'music_note', iconClass: 'music' },
  { id: 'sfx', label: 'Sound FX', icon: 'graphic_eq', iconClass: 'sfx' },
  { id: 'dialogue', label: 'Dialogue', icon: 'record_voice_over', iconClass: 'dialogue' },
];

export default function TimelineView() {
  const {
    state,
    setPlayhead,
    setPlaying,
    setZoom,
    setSelected,
    updateAudioLayer,
  } = useStudio();

  const bodyRef = useRef(null);
  const [isDraggingPlayhead, setIsDraggingPlayhead] = useState(false);
  const playIntervalRef = useRef(null);

  const pps = PIXELS_PER_SECOND * state.timelineZoom;

  /* ── Compute total duration ──────────────────────────────── */
  const totalDuration = useMemo(() => {
    let dur = 0;
    state.keyframes.forEach(kf => (dur += kf.duration));
    state.transitions.forEach(tr => (dur += tr.duration));
    return Math.max(dur, 30); // minimum 30s timeline
  }, [state.keyframes, state.transitions]);

  const totalWidth = totalDuration * pps;

  /* ── Build video clips ───────────────────────────────────── */
  const videoClips = useMemo(() => {
    const clips = [];
    let offset = 0;
    state.keyframes.forEach((kf, idx) => {
      clips.push({
        ...kf,
        clipType: 'keyframe',
        x: offset,
        w: kf.duration * pps,
      });
      offset += kf.duration * pps;

      // Transition after this keyframe
      const tr = state.transitions.find(t => t.fromKeyframeId === kf.id);
      if (tr) {
        clips.push({
          ...tr,
          clipType: 'transition',
          x: offset,
          w: tr.duration * pps,
        });
        offset += tr.duration * pps;
      }
    });
    return clips;
  }, [state.keyframes, state.transitions, pps]);

  /* ── Time ruler marks ────────────────────────────────────── */
  const rulerMarks = useMemo(() => {
    const marks = [];
    const step = state.timelineZoom >= 2 ? 1 : state.timelineZoom >= 1 ? 2 : 5;
    for (let t = 0; t <= totalDuration; t += step) {
      const isMajor = t % (step * 5 === 0 ? step * 5 : step <= 2 ? 10 : 5) === 0 || t === 0;
      marks.push({ time: t, x: t * pps, major: isMajor || t % 10 === 0 });
    }
    return marks;
  }, [totalDuration, pps, state.timelineZoom]);

  /* ── Format timecode ─────────────────────────────────────── */
  const formatTime = (secs) => {
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    const f = Math.floor((secs % 1) * 24);
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}:${String(f).padStart(2, '0')}`;
  };

  /* ── Keep playhead ref in sync ────────────────────────────── */
  const playheadRef = useRef(state.playheadPosition);
  useEffect(() => { playheadRef.current = state.playheadPosition; }, [state.playheadPosition]);

  /* ── Playback simulation ─────────────────────────────────── */
  useEffect(() => {
    if (state.isPlaying) {
      playIntervalRef.current = setInterval(() => {
        playheadRef.current += 0.04;
        if (playheadRef.current >= totalDuration) playheadRef.current = 0;
        setPlayhead(playheadRef.current);
      }, 40);
    }
    return () => {
      if (playIntervalRef.current) clearInterval(playIntervalRef.current);
    };
  }, [state.isPlaying, totalDuration, setPlayhead]);

  /* ── Playhead drag ───────────────────────────────────────── */
  const handleTimelineClick = useCallback((e) => {
    if (!bodyRef.current) return;
    const rect = bodyRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left + bodyRef.current.scrollLeft - 180;
    const time = Math.max(0, x / pps);
    setPlayhead(time);
  }, [pps, setPlayhead]);

  /* ── Audio clips per track ───────────────────────────────── */
  const audioByType = useMemo(() => {
    const map = { music: [], sfx: [], dialogue: [] };
    state.audioLayers.forEach(a => {
      if (map[a.type]) map[a.type].push(a);
    });
    return map;
  }, [state.audioLayers]);

  /* ── Faux waveform bars ──────────────────────────────────── */
  const renderWaveform = (clip, color) => {
    const barCount = Math.max(8, Math.floor((clip.duration * pps) / 4));
    return Array.from({ length: barCount }, (_, i) => {
      const h = 15 + Math.sin(i * 0.7 + clip.startTime) * 30 + Math.random() * 20;
      return (
        <div
          key={i}
          className="timeline-clip__waveform-bar"
          style={{ height: `${h}%`, color }}
        />
      );
    });
  };

  /* ── Transport controls ──────────────────────────────────── */
  const togglePlay = useCallback(() => {
    setPlaying(!state.isPlaying);
  }, [state.isPlaying, setPlaying]);

  const skipBack = useCallback(() => {
    setPlayhead(0);
    setPlaying(false);
  }, [setPlayhead, setPlaying]);

  return (
    <div className="timeline" id="timeline-view">
      {/* Transport & Controls */}
      <div className="timeline__controls">
        <div className="timeline__transport">
          <button
            className="btn btn--icon"
            onClick={skipBack}
            data-tooltip="Go to start"
            id="btn-skip-back"
          >
            <span className="material-icons-round">skip_previous</span>
          </button>
          <button
            className="btn btn--icon btn--play"
            onClick={togglePlay}
            data-tooltip={state.isPlaying ? 'Pause' : 'Play'}
            id="btn-play"
          >
            <span className="material-icons-round">
              {state.isPlaying ? 'pause' : 'play_arrow'}
            </span>
          </button>
          <button
            className="btn btn--icon"
            data-tooltip="Go to end"
            onClick={() => setPlayhead(totalDuration)}
            id="btn-skip-fwd"
          >
            <span className="material-icons-round">skip_next</span>
          </button>
        </div>

        <div className="timeline__timecode" id="timecode">
          {formatTime(state.playheadPosition)}
        </div>

        <div className="timeline__zoom">
          <label>Zoom</label>
          <input
            type="range"
            className="timeline__zoom-slider"
            min="0.25"
            max="4"
            step="0.25"
            value={state.timelineZoom}
            onChange={(e) => setZoom(parseFloat(e.target.value))}
            id="zoom-slider"
          />
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', minWidth: 32 }}>
            {state.timelineZoom}×
          </span>
        </div>
      </div>

      {/* Timeline Body */}
      <div
        className="timeline__body"
        ref={bodyRef}
        onClick={handleTimelineClick}
        id="timeline-body"
      >
        {/* Time Ruler */}
        <div className="time-ruler" style={{ width: totalWidth + 180 }}>
          {rulerMarks.map((mark, i) => (
            <div
              key={i}
              className="time-ruler__mark"
              style={{ left: mark.x + 180 }}
            >
              {mark.major && (
                <span className="time-ruler__label">{formatTime(mark.time)}</span>
              )}
              <div className={`time-ruler__tick ${mark.major ? 'time-ruler__tick--major' : ''}`} />
            </div>
          ))}
        </div>

        {/* Track Lanes */}
        <div className="track-lanes" style={{ width: totalWidth }}>
          {/* Playhead */}
          <div
            className="playhead"
            style={{ left: state.playheadPosition * pps }}
          />

          {TRACK_CONFIG.map(track => (
            <div
              key={track.id}
              className={`track-lane ${track.id === 'video' ? 'track-lane--video' : 'track-lane--audio'}`}
            >
              <div className="track-lane__label">
                <div className={`track-lane__label-icon track-lane__label-icon--${track.iconClass}`}>
                  <span className="material-icons-round">{track.icon}</span>
                </div>
                <span className="track-lane__label-text">{track.label}</span>
              </div>

              <div className="track-lane__content">
                {track.id === 'video' ? (
                  /* Video clips */
                  videoClips.map(clip => (
                    <div
                      key={clip.id}
                      className={`timeline-clip timeline-clip--${clip.clipType} ${
                        state.selectedItemId === clip.id ? 'timeline-clip--selected' : ''
                      }`}
                      style={{ width: clip.w, minWidth: clip.w }}
                      onClick={(e) => { e.stopPropagation(); setSelected(clip.id); }}
                      id={`tclip-${clip.id}`}
                    >
                      {clip.clipType === 'keyframe' && clip.imageUrl && (
                        <img className="timeline-clip__thumb" src={clip.imageUrl} alt="" />
                      )}
                      <span className="timeline-clip__label">
                        {clip.clipType === 'keyframe'
                          ? `S${clip.sceneNumber}`
                          : '↔ Transition'}
                      </span>
                      {(clip.status === 'generating') && (
                        <div className="timeline-clip__generating">
                          <div className="spinner-sm" />
                        </div>
                      )}
                      {/* Resize handles */}
                      <div className="timeline-clip__resize-handle timeline-clip__resize-handle--left" />
                      <div className="timeline-clip__resize-handle timeline-clip__resize-handle--right" />
                    </div>
                  ))
                ) : (
                  /* Audio clips */
                  (audioByType[track.id] || []).map(audio => (
                    <div
                      key={audio.id}
                      className={`timeline-clip timeline-clip--audio timeline-clip--${track.id} ${
                        state.selectedItemId === audio.id ? 'timeline-clip--selected' : ''
                      }`}
                      style={{
                        position: 'absolute',
                        left: audio.startTime * pps,
                        width: audio.duration * pps,
                      }}
                      onClick={(e) => { e.stopPropagation(); setSelected(audio.id); }}
                      id={`tclip-${audio.id}`}
                    >
                      <div className="timeline-clip__waveform">
                        {renderWaveform(audio,
                          track.id === 'music' ? 'var(--accent-cyan)' :
                          track.id === 'sfx' ? 'var(--accent-amber)' :
                          'var(--accent-pink)'
                        )}
                      </div>
                      <span className="timeline-clip__label">
                        {audio.prompt?.substring(0, 20) || track.label}
                      </span>
                      {audio.status === 'generating' && (
                        <div className="timeline-clip__generating">
                          <div className="spinner-sm" />
                        </div>
                      )}
                      <div className="timeline-clip__resize-handle timeline-clip__resize-handle--left" />
                      <div className="timeline-clip__resize-handle timeline-clip__resize-handle--right" />
                    </div>
                  ))
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
