import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './login.css';

function Login() {
  const navigate = useNavigate();
  
  // 1. Unified State for Form Data
  const [role, setRole] = useState('TA');
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    deptKey: ''
  });

  // Handle input changes dynamically
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    
    // Construct payload based on the active role
    const loginData = {
      email: formData.email,
      password: formData.password,
      role: role,
      ...(role === 'Instructor' && { dept_key: formData.deptKey })
    };

    try {
      const response = await fetch("http://localhost:8000/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(loginData),
      });

      const result = await response.json();

      if (response.ok) {
        // Success logic
        navigate(role === 'Instructor' ? '/instructor-admin' : '/review');
      } else {
        alert(result.detail || "Login Failed: Please check your credentials.");
      }
    } catch (error) {
      console.error("Connection Error:", error);
      alert("Could not connect to the GradeOps server. Is your FastAPI backend running?");
    }
  };

  return (
    <div className="login-container">
      <div className={`login-card ${role === 'Instructor' ? 'instructor-active' : ''}`}>
        
        {/* Left Side: Branding */}
        <div className="left-panel">
          <div className="illustration-content">
            <div className="logo-placeholder">
              {/* Local asset path - ensure this file exists in your public/src folder */}
              <img src="/src/assets/TA_img.jpg" alt="GradeOps Branding" />
            </div>
            <h1>GRADEOPS</h1>
            <p>Empowering educators with AI-driven precision grading.</p>
          </div>
        </div>

        {/* Right Side: Form */}
        <div className="right-panel">
          <div className="form-box">
            
            <h2 className="brand-title">GRADEOPS LOGIN</h2>
            
            <div className="role-selector">
              <button 
                type="button"
                className={`role-tab ${role === 'TA' ? 'active' : ''}`}
                onClick={() => setRole('TA')}
              >
                TA Login
              </button>
              <button 
                type="button"
                className={`role-tab ${role === 'Instructor' ? 'active' : ''}`}
                onClick={() => setRole('Instructor')}
              >
                Instructor
              </button>
            </div>

            <form onSubmit={handleLogin}>
              <div className="input-group">
                <label>Institutional Email</label>
                <input 
                  type="email" 
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="test@university.edu" 
                  required 
                />
              </div>
              
              <div className="input-group">
                <label>Password</label>
                <input 
                  type="password" 
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="••••••••••••" 
                  required 
                />
              </div>

              {role === 'Instructor' && (
                <div className="input-group secure-field">
                  <label>Department Access Key 🔐</label>
                  <input 
                    type="password" 
                    name="deptKey"
                    value={formData.deptKey}
                    onChange={handleChange}
                    placeholder="INST-2026-XXXX" 
                    required={role === 'Instructor'} 
                  />
                  <small className="help-text">Instructor-only clearance required.</small>
                </div>
              )}

              <div className="form-footer">
                <a href="#" className="forgot-link">Forgot password?</a>
              </div>

              <button 
                type="submit" 
                className={`login-btn ${role === 'Instructor' ? 'btn-instructor' : 'btn-ta'}`}
              >
                {role === 'Instructor' ? 'Verify & Access Admin' : 'Sign In to Grade'}
              </button>
            </form>

            <div className="divider">
              <span>or secure sign in</span>
            </div>

            <button className="google-btn" type="button" onClick={() => alert("SSO integration coming soon.")}>
              <img src="https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg" alt="Google" />
              Sign in with University SSO
            </button>

            <p className="signup-text">
              Need access? <Link to="/signup">Contact Department Head</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;