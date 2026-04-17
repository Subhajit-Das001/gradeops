import React from 'react';
import './signUp.css';

const SignUp = () => {
  return (
    <div className="auth-wrapper">
      <div className="auth-container">
        <div className="auth-card">
          
          {/* Left Panel: Branding & Illustration */}
          <div className="auth-left">
            <div className="illustration-box">
              <div className="blue-rect">
                {/* <span>Join us</span> */}
                <div className="icon-placeholder"><img src="./src/assets/TA_img2.jpg" alt="TA" /></div>
              </div>
              <h2>JOIN GRADEOPS </h2>
              <p>Create an account to start your journey toward academic freedom.</p>
              
            </div>
          </div>

          {/* Right Panel: Form */}
          <div className="auth-right">
            <div className="auth-form-container">
              <h2 className="auth-title">CREATE ACCOUNT</h2>
              
              <button className="google-auth-btn">
                <img src="./src/assets/google-logo.png" alt="Google" />
                Sign up with Google
              </button>

              <div className="auth-divider">
                <span>or</span>
              </div>

              <form className="auth-form">
                <div className="auth-input-group">
                  <label>Full Name</label>
                  <input type="text" placeholder="John Smith" />
                </div>

                <div className="auth-input-group">
                  <label>Email Address</label>
                  <input type="email" placeholder="john@example.com" />
                </div>

                <div className="auth-input-row">
                  <div className="auth-input-group">
                    <label>Password</label>
                    <input type="password" placeholder="••••••••" />
                  </div>
                  <div className="auth-input-group">
                    <label>Confirm</label>
                    <input type="password" placeholder="••••••••" />
                  </div>
                </div>

                <button type="submit" className="auth-submit-btn">
                  Create Account
                </button>
              </form>

              <p className="auth-footer-text">
                Already have an account? <a href="/login">Sign In</a>
              </p>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default SignUp;