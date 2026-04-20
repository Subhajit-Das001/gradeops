import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './signUp.css';

const SignUp = () => {
  const [role, setRole] = useState('TA');
  const navigate = useNavigate();

  const handleSignUp = (e) => {
    e.preventDefault();
    // Logic to register user in PostgreSQL via FastAPI
    console.log(`Registering as ${role}`);
    navigate('/login');
  };

  return (
    <div className="auth-wrapper">
      <div className={`auth-container ${role === 'Instructor' ? 'instructor-theme' : ''}`}>
        <div className="auth-card">
          
          {/* Left Panel: Branding & Illustration */}
          <div className="auth-left">
            <div className="illustration-box">
              <div className="blue-rect">
                <div className="icon-placeholder">
                  <img src="./src/assets/TA_img2.jpg" alt="Join GradeOps" />
                </div>
              </div>
              <h2>JOIN GRADEOPS</h2>
              <p>
                {role === 'Instructor' 
                  ? "Lead your department with AI-integrated academic oversight." 
                  : "Start your journey toward faster, more precise grading."}
              </p>
            </div>
          </div>

          {/* Right Panel: Form */}
          <div className="auth-right">
            <div className="auth-form-container">
              <h2 className="auth-title">CREATE ACCOUNT</h2>

              {/* Unique Role Selection */}
              <div className="role-selector">
                <button 
                  type="button"
                  className={`role-tab ${role === 'TA' ? 'active' : ''}`}
                  onClick={() => setRole('TA')}
                >TA Account</button>
                <button 
                  type="button"
                  className={`role-tab ${role === 'Instructor' ? 'active' : ''}`}
                  onClick={() => setRole('Instructor')}
                >Instructor</button>
              </div>
              
              <button className="google-auth-btn">
                <img src="https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg" alt="G" />
                Sign up with Google
              </button>

              <div className="auth-divider">
                <span>or use email</span>
              </div>

              <form className="auth-form" onSubmit={handleSignUp}>
                <div className="auth-input-group">
                  <label>Full Name</label>
                  <input type="text" placeholder="Subhajit Das" required />
                </div>

                <div className="auth-input-group">
                  <label>Institutional Email</label>
                  <input type="email" placeholder="name@university.edu" required />
                </div>

                <div className="auth-input-row">
                  <div className="auth-input-group">
                    <label>Password</label>
                    <input type="password" placeholder="••••••••" required />
                  </div>
                  <div className="auth-input-group">
                    <label>Confirm</label>
                    <input type="password" placeholder="••••••••" required />
                  </div>
                </div>

                {/* Unique Distinction: Instructor Verification Code */}
                {role === 'Instructor' && (
                  <div className="secure-verify-field">
                    <label>Departmental Admin Code 🔑</label>
                    <input 
                      type="password" 
                      placeholder="Enter Admin Auth Code" 
                      required={role === 'Instructor'}
                    />
                    <small>Required for instructor-level privileges.</small>
                  </div>
                )}

                <button 
                  type="submit" 
                  className={`auth-submit-btn ${role === 'Instructor' ? 'btn-ins' : 'btn-ta'}`}
                >
                  {role === 'Instructor' ? 'Register as Instructor' : 'Create TA Account'}
                </button>
              </form>

              <p className="auth-footer-text">
                Already have an account? <Link to="/login">Sign In</Link>
              </p>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default SignUp;