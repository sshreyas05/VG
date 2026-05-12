import { useEffect, useRef, useCallback } from 'react';
import { useStudio } from '../context/StudioContext';

/**
 * WebSocket hook for live progress streaming from the backend.
 * Messages follow the protocol:
 *   { type: 'job_update', job_id, status, progress, message, result? }
 *   { type: 'job_complete', job_id, target_type, target_id, result }
 *   { type: 'job_error', job_id, target_type, target_id, error }
 */
export function useWebSocket() {
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const { updateJob, updateKeyframe, updateTransition, updateAudioLayer, setWsConnected } = useStudio();

  // Keep a ref to the latest handler so the WS onmessage never goes stale
  const handleMessageRef = useRef(null);

  handleMessageRef.current = (msg) => {
    console.log('[WS] Received:', msg);
    switch (msg.type) {
      case 'job_update':
        updateJob({
          id: msg.job_id,
          status: msg.status || 'running',
          progress: msg.progress ?? undefined,
          message: msg.message ?? undefined,
        });
        break;

      case 'job_complete': {
        let exportResult = {};

        // Update the target resource with the result
        if (msg.result) {
          if (msg.target_type === 'keyframe') {
            updateKeyframe({
              id: msg.target_id,
              imageUrl: msg.result.url,
              status: 'done',
            });
          } else if (msg.target_type === 'transition') {
            updateTransition({
              id: msg.target_id,
              videoUrl: msg.result.url,
              status: 'done',
            });
          } else if (msg.target_type === 'audio') {
            updateAudioLayer({
              id: msg.target_id,
              audioUrl: msg.result.url,
              status: 'done',
            });
          } else if (msg.target_type === 'export' || msg.job_id?.startsWith('exp_')) {
            exportResult = { result: msg.result };
          }
        }

        updateJob({
          id: msg.job_id,
          status: 'done',
          progress: 100,
          message: 'Complete',
          ...exportResult,
        });
        break;
      }

      case 'job_error':
        updateJob({
          id: msg.job_id,
          status: 'error',
          message: msg.error || 'Generation failed',
        });
        if (msg.target_type && msg.target_id) {
          const updater =
            msg.target_type === 'keyframe' ? updateKeyframe :
            msg.target_type === 'transition' ? updateTransition :
            updateAudioLayer;
          updater({ id: msg.target_id, status: 'error' });
        }
        break;

      default:
        break;
    }
  };

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('[WS] Connected');
        setWsConnected(true);
        if (reconnectTimer.current) {
          clearTimeout(reconnectTimer.current);
          reconnectTimer.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          // Always call the latest handler via ref — never stale
          handleMessageRef.current?.(msg);
        } catch (err) {
          console.warn('[WS] Invalid message:', event.data);
        }
      };

      ws.onclose = () => {
        console.log('[WS] Disconnected — reconnecting in 3s');
        setWsConnected(false);
        reconnectTimer.current = setTimeout(connect, 3000);
      };

      ws.onerror = (err) => {
        console.warn('[WS] Error:', err);
        ws.close();
      };

      wsRef.current = ws;
    } catch (err) {
      console.warn('[WS] Connection failed:', err);
      setWsConnected(false);
      reconnectTimer.current = setTimeout(connect, 3000);
    }
  }, [setWsConnected]);

  const sendMessage = useCallback((msg) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  return { sendMessage, ws: wsRef };
}
