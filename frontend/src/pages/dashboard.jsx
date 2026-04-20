

import React, { useState, useEffect, useCallback } from 'react';
import './dashboard.css';
 
const API = 'http://127.0.0.1:8000';
 
// ── Helpers ───────────────────────────────────────────────────────────────────
function pct(awarded, max) {
  if (!max) return 0;
  return Math.round((awarded / max) * 100);
}
 
// ── Dashboard ─────────────────────────────────────────────────────────────────
const Dashboard = () => {
  // List view state
  const [scripts, setScripts]       = useState([]);
  const [total, setTotal]           = useState(0);
  const [page, setPage]             = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [loadingList, setLoadingList]   = useState(false);
 
  // Detail / review state
  const [selected, setSelected]     = useState(null);   // full script object
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [overrideScore, setOverrideScore] = useState('');
  const [showSuccess, setShowSuccess]     = useState(false);
  const [isMobile, setIsMobile]           = useState(window.innerWidth <= 768);
 
  useEffect(() => {
    const h = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener('resize', h);
    return () => window.removeEventListener('resize', h);
  }, []);
 
  // ── Fetch script list ──────────────────────────────────────────────────────
  const fetchList = useCallback(async () => {
    setLoadingList(true);
    try {
      const params = new URLSearchParams({ page, page_size: 15 });
      if (statusFilter) params.set('status', statusFilter);
      const res = await fetch(`${API}/api/dashboard?${params}`);
      const data = await res.json();
      setScripts(data.items || []);
      setTotal(data.total || 0);
    } catch {
      // backend offline — keep empty list
    } finally {
      setLoadingList(false);
    }
  }, [page, statusFilter]);
 
  useEffect(() => { fetchList(); }, [fetchList]);
 
  // ── Fetch detail for a selected script ────────────────────────────────────
  const fetchDetail = async (scriptId) => {
    setLoadingDetail(true);
    try {
      const res = await fetch(`${API}/api/scripts/${scriptId}`);
      const data = await res.json();
      setSelected(data);
      setOverrideScore('');
    } catch {
      alert('Failed to load script details.');
    } finally {
      setLoadingDetail(false);
    }
  };
 
  // ── TA Actions ─────────────────────────────────────────────────────────────
  const sendReview = async (action, score) => {
    if (!selected) return;
    const body = { action };
    if (action === 'override') body.override_score = Number(score);
 
    const res = await fetch(`${API}/api/scripts/${selected.id}/review`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
 
    if (res.ok) {
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 1200);
      // Re-fetch detail + list
      await fetchDetail(selected.id);
      fetchList();
    } else {
      const err = await res.json();
      alert(`Action failed: ${err.detail}`);
    }
  };
 
  const handleApprove  = useCallback(() => sendReview('approve'),  [selected]);
  const handleFlag     = useCallback(() => sendReview('flag'),      [selected]);
  const handleOverride = () => {
    if (!overrideScore) return;
    sendReview('override', overrideScore);
  };
 
  // Keyboard shortcuts on detail view
  useEffect(() => {
    if (!selected || isMobile) return;
    const h = (e) => {
      if (['Enter', 'Escape'].includes(e.key)) e.preventDefault();
      if (e.key === 'Enter')  handleApprove();
      if (e.key === 'Escape') handleFlag();
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, [selected, handleApprove, handleFlag, isMobile]);
 
  // ── Compute summary from selected detail ──────────────────────────────────
  const totalAwarded   = selected?.grading_results?.reduce((s, r) => s + r.final_score, 0) ?? 0;
  const totalPossible  = selected?.grading_results?.reduce((s, r) => s + r.max_marks, 0) ?? 0;
  const plagiarism     = selected?.grading_results?.some(r => r.plagiarism_flag) ?? false;
  const justification = selected?.grading_results
  ?.map(gr => `${gr.question_id}: ${gr.overall_justification}`)
  .join('\n\n') ?? '—';
  //const justification  = selected?.grading_results?.[0]?.overall_justification ?? '—';
 
  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="dashboard-root">
 
      {/* ── Left: Script List ── */}
      <aside className="script-list-panel">
        <div className="list-header">
          <h3>Submissions</h3>
          <select
            value={statusFilter}
            onChange={e => { setStatusFilter(e.target.value); setPage(1); }}
            className="status-filter"
          >
            <option value="">All</option>
            <option value="pending">Pending</option>
            <option value="graded">Graded</option>
            <option value="approved">Approved</option>
            <option value="flagged">Flagged</option>
          </select>
        </div>
 
        {loadingList && <p className="list-loading">Loading…</p>}
 
        <ul className="script-list">
          {scripts.map(s => (
            <li
              key={s.id}
              className={`script-item ${selected?.id === s.id ? 'active' : ''} status-${s.status}`}
              onClick={() => fetchDetail(s.id)}
            >
              <div className="script-item-top">
                <span className="script-roll">{s.student_roll}</span>
                <span className={`status-badge badge-${s.status}`}>{s.status}</span>
              </div>
              <div className="script-item-bottom">
                <span className="script-score">
                  {s.total_awarded} / {s.total_possible} ({s.percentage}%)
                </span>
                {s.plagiarism_flagged && <span className="plg-badge">⚠ Plagiarism</span>}
              </div>
            </li>
          ))}
          {!loadingList && scripts.length === 0 && (
            <li className="script-empty">No submissions found.</li>
          )}
        </ul>
 
        {/* Pagination */}
        <div className="pagination">
          <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}>‹</button>
          <span>Page {page}</span>
          <button disabled={scripts.length < 15} onClick={() => setPage(p => p + 1)}>›</button>
        </div>
      </aside>
 
      {/* ── Right: Review Panel ── */}
      <main className={`review-panel ${showSuccess ? 'success-flash' : ''}`}>
        {showSuccess && <div className="approval-overlay">DECISION SAVED ✓</div>}
 
        {!selected && !loadingDetail && (
          <div className="review-empty">
            <p>← Select a submission to review</p>
          </div>
        )}
 
        {loadingDetail && <div className="review-empty"><p>Loading…</p></div>}
 
        {selected && !loadingDetail && (
          <>
            {/* Header */}
            <header className="dashboard-header">
              <div className="status-info">
                <h2>ID: {selected.student_roll}</h2>
                <span className={`status-badge badge-${selected.status}`}>{selected.status}</span>
                {plagiarism && <div className="plagiarism-indicator pulse">⚠️ Plagiarism Detected</div>}
              </div>
              {!isMobile && (
                <div className="shortcut-legend">
                  <span><kbd>Enter</kbd> Approve</span>
                  <span><kbd>Esc</kbd> Flag</span>
                </div>
              )}
            </header>
 
            {/* Split: image + AI evaluation */}
            <div className="split-view">
              <section className="view-panel left-panel">
                <div className="panel-label">Student Submission</div>
                <div className="image-viewport">
                  <img
                    src={`${API}${selected.file_url}`}
                    alt="Student Script"
                    className="student-image"
                    onError={e => { e.target.style.display = 'none'; }}
                  />
                </div>
              </section>
 
              <section className="view-panel right-panel">
                <div className="content-scroll-area">
                  <div className="panel-label">AI Evaluation</div>
 
                  {/* Score widget */}
                  <div className={`score-widget ${pct(totalAwarded, totalPossible) >= 80 ? 'high-score' : ''}`}>
                    <div className="score-main">
                      <span className="score-value">{totalAwarded.toFixed(1)}</span>
                      <span className="score-max">/ {totalPossible}</span>
                    </div>
                    <div className="score-pct">{pct(totalAwarded, totalPossible)}%</div>
                  </div>
 
                  {/* Per-question breakdown */}
                  {selected.grading_results.map(gr => (
                    <details key={gr.id} className="question-block">
                      <summary>
                        {gr.question_id} — {gr.final_score} / {gr.max_marks}
                        {gr.plagiarism_flag && ' ⚠️'}
                      </summary>
                      <p className="justification-text">{gr.overall_justification}</p>
                      {gr.plagiarism_note && (
                        <p className="plagiarism-note">{gr.plagiarism_note}</p>
                      )}
                      <table className="criteria-table">
                        <thead>
                          <tr><th>Criterion</th><th>Awarded</th><th>Justification</th></tr>
                        </thead>
                        <tbody>
                          {gr.criteria_scores.map(cs => (
                            <tr key={cs.criterion_id} className={cs.met ? 'met' : 'partial'}>
                              <td>{cs.criterion_id}</td>
                              <td>{cs.awarded}</td>
                              <td>{cs.justification}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </details>
                  ))}
 
                  {/* AI justification summary */}
                  <div className="feedback-section">
                    <label className="input-label">Overall AI Justification</label>
                   <textarea 
  value={justification} 
  readOnly 
  className="justification-box"
  rows={6}
  style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6' }}
/>
                  </div>
 
                  {/* Score override */}
                  <div className="override-section">
                    <label className="input-label">Override Total Score</label>
                    <div className="override-row">
                      <input
                        type="number"
                        min="0"
                        max={totalPossible}
                        step="0.5"
                        placeholder={`0 – ${totalPossible}`}
                        value={overrideScore}
                        onChange={e => setOverrideScore(e.target.value)}
                        className="override-input"
                      />
                      <button className="override-btn" onClick={handleOverride}>
                        Apply Override
                      </button>
                    </div>
                  </div>
                </div>
 
                {/* TA action buttons */}
                <div className="dashboard-actions">
                  <button className="action-btn flag-btn" onClick={handleFlag}>
                    🚩 {isMobile ? 'Flag' : 'Flag Paper (Esc)'}
                  </button>
                  <button className="action-btn approve-btn" onClick={handleApprove}>
                    {selected.status === 'approved'
                      ? '✓ Approved'
                      : isMobile ? '🚀 Approve' : '🚀 Approve (Enter)'}
                  </button>
                </div>
              </section>
            </div>
          </>
        )}
      </main>
    </div>
  );
};
 
export default Dashboard;