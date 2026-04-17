

import React, { useState } from 'react';
import './upload.css';

// SVG Icon Components
const CloudIcon = () => (
  <svg width="60" height="60" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M19 15L12 8L5 15M12 8V22" stroke="#2563eb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M17 10C17.5 10 18.06 9.81 18.5 9.5M17 10C18.66 10 20 8.66 20 7C20 5.34 18.66 4 17 4C16.34 4 15.74 4.22 15.26 4.58M17 10C15.93 10 15 9.07 15 8C15 6.93 15.93 6 17 6" stroke="#2563eb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M10 6C10 3.79 8.21 2 6 2C3.79 2 2 3.79 2 6C2 8.21 3.79 10 6 10M10 6C10.74 6 11.43 6.2 12 6.54M10 6V14M6 10C5.26 10 4.57 9.8 4 9.46" stroke="#2563eb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

function UploadPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [assignmentName, setAssignmentName] = useState("");
  const [showRubric, setShowRubric] = useState(false);
  const [rubricItems, setRubricItems] = useState([{ criteria: "", points: 0 }]);

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const clearSelection = () => {
    setSelectedFile(null);
    setAssignmentName("");
  };

  const addCriteria = () => {
    setRubricItems([...rubricItems, { criteria: "", points: 0 }]);
  };

  // NEW: Consistent function to remove specific criteria row
  const removeCriteria = (index) => {
    if (rubricItems.length > 1) {
      const updatedItems = rubricItems.filter((_, i) => i !== index);
      setRubricItems(updatedItems);
    }
  };

  return (
    <div className="main-content-container">
      <div className="upload-page">
        <div className="upload-header">
          <h1>Upload Exam Papers</h1>
          <p>Please provide the necessary assignment details below and upload the corresponding student submission files for review.</p>
        </div>

        <div className="upload-body">
          <div className="dropzone-section">
            <input type="file" id="fileInput" onChange={handleFileChange} style={{ display: 'none' }} />
            <label htmlFor="fileInput" className={`dropzone ${selectedFile ? 'has-file' : ''}`}>
              <CloudIcon />
              <h2>Drag & drop exam files or click to upload</h2>
              <p>Supported formats: PDF, ZIP, DOCX (Max: 50MB per file)</p>
              {selectedFile && (
                <div className="file-preview">
                  <span className="file-name"><strong>{selectedFile.name}</strong></span>
                  <button onClick={(e) => { e.preventDefault(); clearSelection(); }} className="remove-file-btn">Remove</button>
                </div>
              )}
            </label>
          </div>

          <div className="options-section">
            <div className="option-input">
              <label>Assignment Name</label>
              <input 
                type="text" 
                placeholder="e.g., Final Physics Exam" 
                value={assignmentName}
                onChange={(e) => setAssignmentName(e.target.value)}
              />
            </div>

            <div className="rubric-toggle-container">
               <div className="flex-between">
                  <label className="section-label">Grading Rubric</label>
                  <button className="text-action-btn" onClick={() => setShowRubric(!showRubric)}>
                    {showRubric ? "- Remove Rubric Section" : "+ Define Rubric"}
                  </button>
               </div>

               {showRubric && (
                 <div className="rubric-builder">
                   <p className="helper-text">Define granular criteria for automated/manual grading.</p>
                   {rubricItems.map((item, index) => (
                     <div key={index} className="rubric-row">
                       <input type="text" placeholder="Criteria Name" className="rubric-input-main" />
                       <input type="number" placeholder="Pts" className="rubric-input-pts" />
                       
                       {/* INDIVIDUAL DELETE BUTTON */}
                       {rubricItems.length > 1 && (
                         <button 
                           className="remove-single-btn" 
                           onClick={() => removeCriteria(index)}
                         >✕</button>
                       )}
                     </div>
                   ))}
                   <button className="add-more-btn" onClick={addCriteria}>+ Add Criteria</button>
                 </div>
               )}
            </div>

            <div className="option-row">
              <div className="option-input split">
                <label>Submission Date</label>
                <input type="date" defaultValue={new Date().toISOString().split('T')[0]} />
              </div>
            </div> {/* Fixed: Closing div for option-row */}
          </div>
        </div>

        <div className="upload-footer">
          <button className="clear-btn" onClick={clearSelection}>Clear All</button>
          <button className="primary-btn">Start Processing Submission</button>
        </div>
      </div>
    </div>
  );
}

export default UploadPage;