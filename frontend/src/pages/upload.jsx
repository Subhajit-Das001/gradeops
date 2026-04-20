


import React, { useState, useEffect } from 'react';
import './upload.css';
 
const API = 'http://127.0.0.1:8000';
 
const CloudIcon = () => (
  <svg width="60" height="60" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M19 15L12 8L5 15M12 8V22" stroke="#2563eb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M17 10C18.66 10 20 8.66 20 7C20 5.34 18.66 4 17 4C16.34 4 15.74 4.22 15.26 4.58" stroke="#2563eb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M10 6C10 3.79 8.21 2 6 2C3.79 2 2 3.79 2 6C2 8.21 3.79 10 6 10" stroke="#2563eb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);
 
function UploadPage() {
  const [selectedFile, setSelectedFile]     = useState(null);
  const [studentRoll, setStudentRoll]       = useState('');
  const [assignmentName, setAssignmentName] = useState('');
  const [rubrics, setRubrics]               = useState([]);        // fetched from backend
  const [selectedRubricId, setSelectedRubricId] = useState('');
  const [showRubric, setShowRubric]         = useState(false);
  const [rubricItems, setRubricItems]       = useState([{ criteria: '', points: '' }]);
  const [isUploading, setIsUploading]       = useState(false);
  const [toast, setToast]                   = useState(null);       // {type, message}
 
  // Fetch existing rubrics on mount
  useEffect(() => {
    fetch(`${API}/api/rubrics`)
      .then(r => r.json())
      .then(setRubrics)
      .catch(() => {/* backend offline */});
  }, []);
 
  const showToast = (type, message) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 3500);
  };
 
  const handleFileChange = (e) => setSelectedFile(e.target.files[0]);
 
  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) setSelectedFile(file);
  };
 
  const clearSelection = () => {
    setSelectedFile(null);
    setAssignmentName('');
    setStudentRoll('');
    setSelectedRubricId('');
    setRubricItems([{ criteria: '', points: '' }]);
    setShowRubric(false);
  };
 
  // Save a new rubric to backend then select it
  const handleSaveRubric = async () => {
    if (!assignmentName) {
      showToast('error', 'Set an Assignment Name before saving a rubric.');
      return;
    }
    const validItems = rubricItems.filter(i => i.criteria && i.points);
    if (validItems.length === 0) {
      showToast('error', 'Add at least one rubric criterion.');
      return;
    }
 
    const totalMarks = validItems.reduce((s, i) => s + Number(i.points), 0);
    const criteria = validItems.map((item, idx) => ({
      criterion_id: `C${idx + 1}`,
      question_id: 'Q1',
      question_text: assignmentName,
      description: item.criteria,
      max_marks: Number(item.points),
      keywords: [],
    }));
 
    try {
      const res = await fetch(`${API}/api/rubrics`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: assignmentName,
          total_marks: totalMarks,
          criteria,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      showToast('success', `Rubric saved (ID: ${data.rubric_id})`);
      setSelectedRubricId(String(data.rubric_id));
      // Refresh rubric list
      fetch(`${API}/api/rubrics`).then(r => r.json()).then(setRubrics);
      setShowRubric(false);
    } catch (err) {
      showToast('error', `Failed to save rubric: ${err.message}`);
    }
  };
 
  const handleProcessSubmission = async () => {
    if (!selectedFile || !studentRoll) {
      showToast('error', 'Please enter a Student Roll Number and select a file.');
      return;
    }
 
    setIsUploading(true);
    const formData = new FormData();
    formData.append('student_roll', studentRoll);
    formData.append('assignment_name', assignmentName);
    formData.append('file', selectedFile);
    if (selectedRubricId) formData.append('rubric_id', selectedRubricId);
 
    try {
      const response = await fetch(`${API}/api/upload-script`, {
        method: 'POST',
        body: formData,
      });
      const result = await response.json();
      if (response.ok) {
        showToast('success', `✓ ${result.filename} uploaded. ${result.message}`);
        clearSelection();
      } else {
        showToast('error', `Upload failed: ${result.detail}`);
      }
    } catch {
      showToast('error', "Backend offline. Run 'python main.py' first.");
    } finally {
      setIsUploading(false);
    }
  };
 
  return (
    <div className="main-content-container">
      {toast && (
        <div className={`toast toast-${toast.type}`}>{toast.message}</div>
      )}
 
      <div className="upload-page">
        <div className="upload-header">
          <h1>Upload Exam Papers</h1>
          <p>Provide details and upload student answer scripts for AI review.</p>
        </div>
 
        <div className="upload-body">
          {/* ── Drop zone ── */}
          <div className="dropzone-section">
            <input
              type="file"
              id="fileInput"
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />
            <label
              htmlFor="fileInput"
              className={`dropzone ${selectedFile ? 'has-file' : ''}`}
              onDragOver={e => e.preventDefault()}
              onDrop={handleDrop}
            >
              <CloudIcon />
              <h2>{selectedFile ? 'File Selected' : 'Drag & drop exam files or click to upload'}</h2>
              <p>Supported: PDF, JPG, PNG (Max: 50 MB)</p>
              {selectedFile && (
                <div className="file-preview">
                  <span className="file-name"><strong>{selectedFile.name}</strong></span>
                  <button
                    onClick={e => { e.preventDefault(); e.stopPropagation(); setSelectedFile(null); }}
                    className="remove-file-btn"
                  >
                    Remove
                  </button>
                </div>
              )}
            </label>
          </div>
 
          {/* ── Options ── */}
          <div className="options-section">
            <div className="option-input">
              <label>Student Roll Number *</label>
              <input
                type="text"
                placeholder="e.g., 240107087"
                value={studentRoll}
                onChange={e => setStudentRoll(e.target.value)}
              />
            </div>
 
            <div className="option-input">
              <label>Assignment Name</label>
              <input
                type="text"
                placeholder="e.g., Final Physics Exam"
                value={assignmentName}
                onChange={e => setAssignmentName(e.target.value)}
              />
            </div>
 
            {/* Rubric selector: pick existing OR define inline */}
            <div className="rubric-toggle-container">
              <div className="flex-between">
                <label className="section-label">Grading Rubric</label>
                <button className="text-action-btn" onClick={() => setShowRubric(!showRubric)}>
                  {showRubric ? '− Hide Builder' : '+ Define New Rubric'}
                </button>
              </div>
 
              {/* Existing rubrics dropdown */}
              {rubrics.length > 0 && !showRubric && (
                <select
                  className="rubric-select"
                  value={selectedRubricId}
                  onChange={e => setSelectedRubricId(e.target.value)}
                >
                  <option value="">— Select existing rubric —</option>
                  {rubrics.map(r => (
                    <option key={r.id} value={r.id}>
                      {r.name} ({r.total_marks} marks, {r.criteria_count} criteria)
                    </option>
                  ))}
                </select>
              )}
 
              {/* Inline rubric builder */}
              {showRubric && (
                <div className="rubric-builder">
                  {rubricItems.map((item, index) => (
                    <div key={index} className="rubric-row">
                      <input
                        type="text"
                        placeholder="Criteria description"
                        className="rubric-input-main"
                        value={item.criteria}
                        onChange={e => {
                          const updated = [...rubricItems];
                          updated[index].criteria = e.target.value;
                          setRubricItems(updated);
                        }}
                      />
                      <input
                        type="number"
                        placeholder="Pts"
                        className="rubric-input-pts"
                        value={item.points}
                        onChange={e => {
                          const updated = [...rubricItems];
                          updated[index].points = e.target.value;
                          setRubricItems(updated);
                        }}
                      />
                      {rubricItems.length > 1 && (
                        <button
                          className="remove-single-btn"
                          onClick={() => setRubricItems(rubricItems.filter((_, i) => i !== index))}
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  ))}
                  <div className="rubric-builder-actions">
                    <button
                      className="add-more-btn"
                      onClick={() => setRubricItems([...rubricItems, { criteria: '', points: '' }])}
                    >
                      + Add Criteria
                    </button>
                    <button className="save-rubric-btn" onClick={handleSaveRubric}>
                      Save & Use Rubric
                    </button>
                  </div>
                </div>
              )}
 
              {selectedRubricId && !showRubric && (
                <p className="rubric-selected-note">
                  ✓ Rubric ID {selectedRubricId} will be used for AI grading.
                </p>
              )}
            </div>
          </div>
        </div>
 
        <div className="upload-footer">
          <button className="clear-btn" onClick={clearSelection}>Clear All</button>
          <button className="primary-btn" onClick={handleProcessSubmission} disabled={isUploading}>
            {isUploading ? 'Uploading…' : 'Start Processing Submission'}
          </button>
        </div>
      </div>
    </div>
  );
}
 
export default UploadPage;