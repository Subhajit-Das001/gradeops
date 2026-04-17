import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from './component/Navbar'
import Footer from './component/Footer'
import Home from './pages/home'
import Login from './pages/login'
import SignUp from './pages/signUp'
import Upload from './pages/upload';
import Dashboard from './pages/dashboard';
import Review from './pages/review';


function App() {
  

  return (
   <div>
    
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} /> 
        <Route path="/upload" element={<Upload/>} />
        <Route path="/review" element={<Review />} />
        <Route path="/signup" element={<SignUp />} />
        <Route path="/dashboard" element={<Dashboard />} />
        
      </Routes>
      <Footer />
    </Router>
    
    
   </div> 
    
     

    
  );
}

export default App
