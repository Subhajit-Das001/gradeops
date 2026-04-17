import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from './component/Navbar'
import Footer from './component/Footer'
import Home from './pages/home'
import Login from './pages/login'


function App() {
  

  return (
   <div>
    
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} /> 
        <Route path="/dashboard" element={<div>Dashboard Page</div>} />
        <Route path="/upload" element={<div>Upload Page</div>} />
        <Route path="/review" element={<div>Review Page</div>} />
      </Routes>
      <Footer />
    </Router>
    
    
   </div> 
    
     

    
  );
}

export default App
