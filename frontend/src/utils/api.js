/* ═══════════════════════════════════════════════════════════════
   API Client — communicates with the FastAPI backend
   ═══════════════════════════════════════════════════════════════ */

const API_BASE = '/api';

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const config = {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  };

  if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData)) {
    config.body = JSON.stringify(config.body);
  }

  if (config.body instanceof FormData) {
    delete config.headers['Content-Type']; // Let browser set multipart boundary
  }

  const res = await fetch(url, config);

  if (!res.ok) {
    const errorBody = await res.text().catch(() => '');
    throw new Error(`API Error ${res.status}: ${errorBody || res.statusText}`);
  }

  const contentType = res.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return res.json();
  }
  return res;
}

/* ── Brain / Script Enhancement ────────────────────────────── */
export async function enhanceIdea(idea, duration = 15) {
  return request('/brain/enhance', {
    method: 'POST',
    body: { idea, duration },
  });
}

export async function generateFull(idea, duration = 15) {
  return request('/generate_full', {
    method: 'POST',
    body: { idea, duration },
  });
}

/* ── Keyframe Generation ───────────────────────────────────── */
export async function generateKeyframe(prompt, options = {}) {
  return request('/keyframes/generate', {
    method: 'POST',
    body: {
      prompt,
      width: options.width || 832,
      height: options.height || 480,
      steps: options.steps || 28,
    },
  });
}

/* ── Transition Video Generation ───────────────────────────── */
export async function generateTransition(id, imageUrl, prompt, options = {}) {
  return request('/transitions/generate', {
    method: 'POST',
    body: {
      target_id: id,
      image_url: imageUrl,
      prompt,
      steps: options.steps || 40,
    },
  });
}

/* ── Audio Generation ──────────────────────────────────────── */
export async function generateAudio(audioParams) {
  return request('/audio/generate', {
    method: 'POST',
    body: {
      dialogue: audioParams.dialogue || '',
      music: audioParams.music || '',
      sfx: audioParams.sfx || '',
      total_duration: audioParams.duration || 30,
      dialogue_start: audioParams.dialogueStart || 2.0,
      music_volume: audioParams.musicVolume || 0.4,
      sfx_volume: audioParams.sfxVolume || 1.0,
    },
  });
}

/* ── Export ─────────────────────────────────────────────────── */
export async function exportFilm(options = {}) {
  return request('/export', {
    method: 'POST',
    body: {
      format: options.format || 'mp4',
      resolution: options.resolution || '1920x1080',
      fps: options.fps || 24,
      clips: options.clips || [],
    },
  });
}

/* ── Job Management ────────────────────────────────────────── */
export async function cancelJob(jobId) {
  return request(`/jobs/${jobId}/cancel`, { method: 'POST' });
}

export async function getJobs() {
  return request('/jobs');
}

/* ── Health Check ──────────────────────────────────────────── */
export async function healthCheck() {
  return request('/health');
}
