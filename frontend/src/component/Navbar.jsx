import React from 'react';
import { Shield, Bell, User, LayoutDashboard, UploadCloud } from 'lucide-react';
import './Navbar.css';
import { Link } from 'react-router-dom';
const Navbar = ({ role, activeView, setView }) => {
    
  return (

    <nav className="navbar">
        <div className="navbar-logo">
  <Link to="/">
    <img src="src/assets/logo-gradeops.png" alt="GradeOps Logo" />
  </Link>
</div>
        <ul className="navbar-menu">
            <li className='nav-item'><Link to="/dashboard">Dashboard</Link></li>
            <li className='nav-item'><Link to="/upload">Upload</Link></li>
        
            <li className='nav-item'><Link to="/review">Review</Link></li>
            <li className='nav-item'><Link to="/login">User login</Link></li>
            
        </ul>
    </nav>
  );
};

export default Navbar;