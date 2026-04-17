import React from 'react';
import './Footer.css';
function Footer(){
    return (
        <footer className="footer-container">
            <div className='footer-content'>
                <div className='webdetails'>
            <img src="src/assets/logo-gradeops.png" alt="GradeOps Logo" className="footer-logo" />
            <p>GradeOps is an innovative platform designed to streamline the grading process for educators and students. Our mission is to provide a user-friendly interface that simplifies grade management, enhances communication, and promotes transparency in education.</p>
            </div>
            <div className='imp-links'>
            <ul className="footer-links">
                <h2>Important Links</h2>
                <li><a href="#">Home</a></li>
                <li><a href="#">About Us</a></li>
                
                <li><a href="#">Privacy Policy</a></li>
                
            </ul></div>
            <ul className='contact-info'>
                <h2>Contact Us</h2>
                <li>Email:gradeops@example.com</li>
                <li>Phone: +1 (123) 456-7890</li>
                <li>Address: khardah, kolkata, West Bengal</li> 
            
            </ul>
            </div>
            <div className='footer-end'>
                <p>&copy; 2026 GradeOps. All rights reserved.</p>
                <p className='developer-info'>Designed and Developed by Subhajit Das</p>
            </div>
            
        </footer>
    );
}
export default Footer;