import React, { createContext, useContext, useReducer, useCallback } from 'react';

/* ── Unique ID generator ──────────────────────────────────── */
let _id = 0;
const uid = (prefix = 'id') => `${prefix}_${++_id}_${Date.now().toString(36)}`;

/* ── Initial State ─────────────────────────────────────────── */
const initialState = {
  projectTitle: 'Untitled Film',
  currentView: 'storyboard', // 'storyboard' | 'timeline'
  keyframes: [],
  transitions: [],
  audioLayers: [],
  jobs: [],
  playheadPosition: 0,   // seconds
  isPlaying: false,
  timelineZoom: 1,        // 0.25 – 4
  selectedItemId: null,
  filmIdea: '',
  wsConnected: false,
  exportModalOpen: false,
};

/* ── Action Types ──────────────────────────────────────────── */
const Actions = {
  SET_VIEW: 'SET_VIEW',
  SET_TITLE: 'SET_TITLE',
  SET_FILM_IDEA: 'SET_FILM_IDEA',

  // Keyframes
  ADD_KEYFRAME: 'ADD_KEYFRAME',
  UPDATE_KEYFRAME: 'UPDATE_KEYFRAME',
  REMOVE_KEYFRAME: 'REMOVE_KEYFRAME',
  REORDER_KEYFRAMES: 'REORDER_KEYFRAMES',

  // Transitions
  ADD_TRANSITION: 'ADD_TRANSITION',
  UPDATE_TRANSITION: 'UPDATE_TRANSITION',
  REMOVE_TRANSITION: 'REMOVE_TRANSITION',

  // Audio
  ADD_AUDIO_LAYER: 'ADD_AUDIO_LAYER',
  UPDATE_AUDIO_LAYER: 'UPDATE_AUDIO_LAYER',
  REMOVE_AUDIO_LAYER: 'REMOVE_AUDIO_LAYER',

  // Jobs
  ADD_JOB: 'ADD_JOB',
  UPDATE_JOB: 'UPDATE_JOB',
  REMOVE_JOB: 'REMOVE_JOB',
  CLEAR_DONE_JOBS: 'CLEAR_DONE_JOBS',

  // Timeline
  SET_PLAYHEAD: 'SET_PLAYHEAD',
  SET_PLAYING: 'SET_PLAYING',
  SET_ZOOM: 'SET_ZOOM',
  SET_SELECTED: 'SET_SELECTED',

  // WebSocket
  SET_WS_CONNECTED: 'SET_WS_CONNECTED',

  // Export
  SET_EXPORT_MODAL: 'SET_EXPORT_MODAL',

  // Bulk: load a full script from brain.py
  LOAD_SCRIPT: 'LOAD_SCRIPT',
};

/* ── Reducer ───────────────────────────────────────────────── */
function studioReducer(state, action) {
  switch (action.type) {
    case Actions.SET_VIEW:
      return { ...state, currentView: action.payload };

    case Actions.SET_TITLE:
      return { ...state, projectTitle: action.payload };

    case Actions.SET_FILM_IDEA:
      return { ...state, filmIdea: action.payload };

    /* ── Keyframes ── */
    case Actions.ADD_KEYFRAME: {
      const kf = {
        id: uid('kf'),
        sceneNumber: state.keyframes.length + 1,
        prompt: action.payload?.prompt || '',
        imageUrl: action.payload?.imageUrl || null,
        status: 'idle',
        duration: action.payload?.duration || 4,
        ...action.payload,
      };
      // auto-create transition if there's a previous keyframe
      const newTransitions = [...state.transitions];
      if (state.keyframes.length > 0) {
        const prevKf = state.keyframes[state.keyframes.length - 1];
        newTransitions.push({
          id: uid('tr'),
          fromKeyframeId: prevKf.id,
          toKeyframeId: kf.id,
          prompt: action.payload?.transitionPrompt || '',
          videoUrl: null,
          status: 'idle',
          duration: 2,
        });
      }
      return {
        ...state,
        keyframes: [...state.keyframes, kf],
        transitions: newTransitions,
      };
    }

    case Actions.UPDATE_KEYFRAME:
      return {
        ...state,
        keyframes: state.keyframes.map(kf =>
          kf.id === action.payload.id ? { ...kf, ...action.payload } : kf
        ),
      };

    case Actions.REMOVE_KEYFRAME: {
      const idx = state.keyframes.findIndex(kf => kf.id === action.payload);
      const newKfs = state.keyframes.filter(kf => kf.id !== action.payload);
      // Renumber
      newKfs.forEach((kf, i) => (kf.sceneNumber = i + 1));
      // Remove associated transitions
      const newTrans = state.transitions.filter(
        t => t.fromKeyframeId !== action.payload && t.toKeyframeId !== action.payload
      );
      return { ...state, keyframes: newKfs, transitions: newTrans };
    }

    case Actions.REORDER_KEYFRAMES:
      return { ...state, keyframes: action.payload };

    /* ── Transitions ── */
    case Actions.ADD_TRANSITION:
      return { ...state, transitions: [...state.transitions, { id: uid('tr'), ...action.payload }] };

    case Actions.UPDATE_TRANSITION:
      return {
        ...state,
        transitions: state.transitions.map(t =>
          t.id === action.payload.id ? { ...t, ...action.payload } : t
        ),
      };

    case Actions.REMOVE_TRANSITION:
      return { ...state, transitions: state.transitions.filter(t => t.id !== action.payload) };

    /* ── Audio ── */
    case Actions.ADD_AUDIO_LAYER:
      return {
        ...state,
        audioLayers: [
          ...state.audioLayers,
          { id: uid('aud'), status: 'idle', startTime: 0, ...action.payload },
        ],
      };

    case Actions.UPDATE_AUDIO_LAYER:
      return {
        ...state,
        audioLayers: state.audioLayers.map(a =>
          a.id === action.payload.id ? { ...a, ...action.payload } : a
        ),
      };

    case Actions.REMOVE_AUDIO_LAYER:
      return { ...state, audioLayers: state.audioLayers.filter(a => a.id !== action.payload) };

    /* ── Jobs ── */
    case Actions.ADD_JOB:
      return {
        ...state,
        jobs: [
          ...state.jobs,
          {
            id: uid('job'),
            progress: 0,
            status: 'pending',
            message: 'Queued…',
            createdAt: Date.now(),
            ...action.payload,
          },
        ],
      };

    case Actions.UPDATE_JOB:
      return {
        ...state,
        jobs: state.jobs.map(j =>
          j.id === action.payload.id ? { ...j, ...action.payload } : j
        ),
      };

    case Actions.REMOVE_JOB:
      return { ...state, jobs: state.jobs.filter(j => j.id !== action.payload) };

    case Actions.CLEAR_DONE_JOBS:
      return {
        ...state,
        jobs: state.jobs.filter(j => j.status !== 'done' && j.status !== 'error'),
      };

    /* ── Timeline ── */
    case Actions.SET_PLAYHEAD:
      return { ...state, playheadPosition: action.payload };

    case Actions.SET_PLAYING:
      return { ...state, isPlaying: action.payload };

    case Actions.SET_ZOOM:
      return { ...state, timelineZoom: Math.max(0.25, Math.min(4, action.payload)) };

    case Actions.SET_SELECTED:
      return { ...state, selectedItemId: action.payload };

    /* ── WebSocket ── */
    case Actions.SET_WS_CONNECTED:
      return { ...state, wsConnected: action.payload };

    /* ── Export modal ── */
    case Actions.SET_EXPORT_MODAL:
      return { ...state, exportModalOpen: action.payload };

    /* ── Load full script from Brain AI ── */
    case Actions.LOAD_SCRIPT: {
      const script = action.payload;
      const keyframes = [];
      const transitions = [];
      const audioLayers = [];

      // Build keyframe from main scene
      const mainKf = {
        id: uid('kf'),
        sceneNumber: 1,
        prompt: script.keyframe_prompt || script.description || '',
        imageUrl: null,
        status: 'idle',
        duration: 4,
      };
      keyframes.push(mainKf);

      // Build clips as additional keyframes + transitions
      if (script.clips && Array.isArray(script.clips)) {
        script.clips.forEach((clip, i) => {
          const nextKf = {
            id: uid('kf'),
            sceneNumber: i + 2,
            prompt: clip.transition_prompt || '',
            imageUrl: null,
            status: 'idle',
            duration: 4,
          };
          keyframes.push(nextKf);
          transitions.push({
            id: uid('tr'),
            fromKeyframeId: keyframes[i].id,
            toKeyframeId: nextKf.id,
            prompt: clip.transition_prompt || '',
            videoUrl: null,
            status: 'idle',
            duration: 2,
          });

          // Audio layers from clip
          if (clip.music) {
            audioLayers.push({
              id: uid('aud'),
              type: 'music',
              prompt: clip.music,
              audioUrl: null,
              status: 'idle',
              startTime: i * 6,
              duration: 8,
            });
          }
          if (clip.sound_effect) {
            audioLayers.push({
              id: uid('aud'),
              type: 'sfx',
              prompt: clip.sound_effect,
              audioUrl: null,
              status: 'idle',
              startTime: i * 6 + 1,
              duration: 4,
            });
          }
        });
      }

      // Dialogue layers
      if (script.dialogue_prompt && Array.isArray(script.dialogue_prompt)) {
        script.dialogue_prompt.forEach((dp, i) => {
          audioLayers.push({
            id: uid('aud'),
            type: 'dialogue',
            prompt: dp.dialogue || '',
            audioUrl: null,
            status: 'idle',
            startTime: i * 6 + 2,
            duration: 5,
          });
        });
      }

      return {
        ...state,
        keyframes,
        transitions,
        audioLayers,
        projectTitle: script.description
          ? script.description.substring(0, 40) + '…'
          : state.projectTitle,
      };
    }

    default:
      return state;
  }
}

/* ── Context ───────────────────────────────────────────────── */
const StudioContext = createContext(null);

export function StudioProvider({ children }) {
  const [state, dispatch] = useReducer(studioReducer, initialState);

  /* Convenience dispatchers */
  const actions = {
    setView: useCallback((v) => dispatch({ type: Actions.SET_VIEW, payload: v }), []),
    setTitle: useCallback((t) => dispatch({ type: Actions.SET_TITLE, payload: t }), []),
    setFilmIdea: useCallback((idea) => dispatch({ type: Actions.SET_FILM_IDEA, payload: idea }), []),

    addKeyframe: useCallback((data) => dispatch({ type: Actions.ADD_KEYFRAME, payload: data }), []),
    updateKeyframe: useCallback((data) => dispatch({ type: Actions.UPDATE_KEYFRAME, payload: data }), []),
    removeKeyframe: useCallback((id) => dispatch({ type: Actions.REMOVE_KEYFRAME, payload: id }), []),
    reorderKeyframes: useCallback((kfs) => dispatch({ type: Actions.REORDER_KEYFRAMES, payload: kfs }), []),

    addTransition: useCallback((data) => dispatch({ type: Actions.ADD_TRANSITION, payload: data }), []),
    updateTransition: useCallback((data) => dispatch({ type: Actions.UPDATE_TRANSITION, payload: data }), []),
    removeTransition: useCallback((id) => dispatch({ type: Actions.REMOVE_TRANSITION, payload: id }), []),

    addAudioLayer: useCallback((data) => dispatch({ type: Actions.ADD_AUDIO_LAYER, payload: data }), []),
    updateAudioLayer: useCallback((data) => dispatch({ type: Actions.UPDATE_AUDIO_LAYER, payload: data }), []),
    removeAudioLayer: useCallback((id) => dispatch({ type: Actions.REMOVE_AUDIO_LAYER, payload: id }), []),

    addJob: useCallback((data) => dispatch({ type: Actions.ADD_JOB, payload: data }), []),
    updateJob: useCallback((data) => dispatch({ type: Actions.UPDATE_JOB, payload: data }), []),
    removeJob: useCallback((id) => dispatch({ type: Actions.REMOVE_JOB, payload: id }), []),
    clearDoneJobs: useCallback(() => dispatch({ type: Actions.CLEAR_DONE_JOBS }), []),

    setPlayhead: useCallback((p) => dispatch({ type: Actions.SET_PLAYHEAD, payload: p }), []),
    setPlaying: useCallback((p) => dispatch({ type: Actions.SET_PLAYING, payload: p }), []),
    setZoom: useCallback((z) => dispatch({ type: Actions.SET_ZOOM, payload: z }), []),
    setSelected: useCallback((id) => dispatch({ type: Actions.SET_SELECTED, payload: id }), []),

    setWsConnected: useCallback((c) => dispatch({ type: Actions.SET_WS_CONNECTED, payload: c }), []),
    setExportModal: useCallback((open) => dispatch({ type: Actions.SET_EXPORT_MODAL, payload: open }), []),

    loadScript: useCallback((script) => dispatch({ type: Actions.LOAD_SCRIPT, payload: script }), []),
  };

  return (
    <StudioContext.Provider value={{ state, dispatch, ...actions }}>
      {children}
    </StudioContext.Provider>
  );
}

export function useStudio() {
  const ctx = useContext(StudioContext);
  if (!ctx) throw new Error('useStudio must be used within StudioProvider');
  return ctx;
}

export { Actions };
export default StudioContext;
