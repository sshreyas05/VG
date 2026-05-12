import React, { useRef, useEffect } from 'react';
import { useStudio } from '../context/StudioContext';
import { cancelJob } from '../utils/api';

export default function JobMonitor() {
  const { state, removeJob, clearDoneJobs, updateJob } = useStudio();
  const activeJobs = state.jobs.filter(j => j.status !== 'cancelled');
  
  const openedExportsRef = useRef(new Set());

  useEffect(() => {
    activeJobs.forEach(job => {
      if (job.type === 'export' && job.status === 'done' && job.result?.download_url) {
        if (!openedExportsRef.current.has(job.id)) {
           // Force download instead of opening in a new tab
           const link = document.createElement('a');
           link.href = job.result.download_url;
           link.setAttribute('download', `Final_Film_${job.id}.mp4`);
           document.body.appendChild(link);
           link.click();
           document.body.removeChild(link);
           
           openedExportsRef.current.add(job.id);
        }
      }
    });
  }, [activeJobs]);

  if (activeJobs.length === 0) return null;

  const runningCount = activeJobs.filter(j => j.status === 'pending' || j.status === 'running').length;

  const handleCancel = async (jobId) => {
    try {
      await cancelJob(jobId);
    } catch {
      // Backend may not be running, just update locally
    }
    updateJob({ id: jobId, status: 'cancelled', message: 'Cancelled' });
    setTimeout(() => removeJob(jobId), 1500);
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'keyframe': return 'var(--accent-light)';
      case 'transition': return 'var(--accent-cyan)';
      case 'audio': return 'var(--accent-pink)';
      case 'export': return 'var(--accent-emerald)';
      default: return 'var(--text-secondary)';
    }
  };

  return (
    <div className="job-monitor" id="job-monitor">
      <div className="job-monitor__header">
        <div className="job-monitor__title">
          <span className="material-icons-round" style={{ fontSize: 18, color: 'var(--accent-light)' }}>
            pending_actions
          </span>
          Jobs
          {runningCount > 0 && (
            <span className="job-monitor__count">{runningCount}</span>
          )}
        </div>
        {activeJobs.some(j => j.status === 'done' || j.status === 'error') && (
          <button
            className="btn btn--ghost btn--sm"
            onClick={clearDoneJobs}
            style={{ fontSize: '0.7rem' }}
          >
            Clear Done
          </button>
        )}
      </div>

      <div className="job-monitor__list">
        {activeJobs.map(job => (
          <div
            key={job.id}
            className={`job-item ${job.status === 'done' ? 'job-item--done' : ''} ${
              job.status === 'error' ? 'job-item--error' : ''
            }`}
          >
            <div className="job-item__top">
              <span
                className={`job-item__type job-item__type--${job.type}`}
                style={{ color: getTypeColor(job.type) }}
              >
                {job.type}
              </span>
              {(job.status === 'pending' || job.status === 'running') && (
                <button
                  className="job-item__cancel"
                  onClick={() => handleCancel(job.id)}
                  data-tooltip="Cancel"
                >
                  <span className="material-icons-round" style={{ fontSize: 16 }}>close</span>
                </button>
              )}
              {job.status === 'done' && (
                <span className="material-icons-round" style={{ fontSize: 16, color: 'var(--accent-emerald)' }}>
                  check_circle
                </span>
              )}
              {job.status === 'error' && (
                <span className="material-icons-round" style={{ fontSize: 16, color: 'var(--accent-rose)' }}>
                  error
                </span>
              )}
            </div>
            <div className="job-item__message">{job.message}</div>
            {job.type === 'export' && job.status === 'done' && job.result?.download_url && (
              <a
                href={job.result.download_url}
                target="_blank"
                rel="noreferrer"
                className="btn btn--primary btn--sm job-item__download"
                style={{ marginTop: 8, fontSize: '0.65rem', padding: '4px 10px', height: 'auto' }}
              >
                <span className="material-icons-round" style={{ fontSize: 14 }}>download</span>
                Download Film
              </a>
            )}
            <div className="job-item__progress">
              <div
                className="job-item__progress-bar"
                style={{ width: `${job.progress || 0}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
