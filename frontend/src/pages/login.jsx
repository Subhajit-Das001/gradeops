import React from 'react';
import { Link } from 'react-router-dom';
import './login.css';

function Login() {
  return (
    <div className="login-container">
      <div className="login-card">
        {/* Left Side: Branding/Illustration */}
        <div className="left-panel">
          <div className="illustration-content">
            <div className="logo-placeholder"><img src="./src/assets/TA_img.jpg" alt="TA" /></div>
            <h1>GRADEOPS</h1>
            <p>Reduce your academic work with our excellence platform.</p>
            
          </div>
        </div>

        {/* Right Side: Login Form */}
        <div className="right-panel">
          <div className="form-box">
            <h2 className="brand-title">GRADEOPS</h2>
            <form>
              <div className="input-group">
                <label>Username or email</label>
                <input type="text" placeholder="johnsmith007" />
              </div>
              <div className="input-group">
                <label>Password</label>
                <input type="password" placeholder="••••••••••••" />
              </div>
              <div className="form-footer">
                <a href="#" className="forgot-link">Forgot password?</a>
              </div>
              <button type="submit" className="login-btn">Sign In</button>
            </form>

            <div className="divider">
              <span>or</span>
            </div>

            <button className="google-btn">
              <img src="./src/assets/google-logo.png" alt="G" />
              Sign in with Google
            </button>

            <p className="signup-text">
              Are you new? <Link to="/signup">Create an Account</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;