import React from 'react';
import { ArrowRight, Brain, Zap, Shield, Cpu } from 'lucide-react';
import HeroScene from './HeroScene';
import './Home.css';

const Home = ({ setView }) => {
  return (
    <div className="home-wrapper">
      {/* Hero: Text Left, Small 3D Right */}
      <section className="hero-container">
        <div className="hero-content">
          <div className="pill">Human-in-the-Loop Pipeline</div>
          <h1 className="title">Ambition Meets <span>Execution.</span></h1>
          <p className="subtitle">
            A specialized grading pipeline using Vision-Language Models to evaluate 
            handwritten exams with explainable AI justifications[cite: 32, 119].
          </p>
          <button className="cta-button" onClick={() => setView('upload')}>
            Get Started <ArrowRight size={18} />
          </button>
        </div>
        <div className="hero-visual">
          <HeroScene />
        </div>
      </section>

      {/* Bento Grid Features */}
      <section className="bento-grid">
        <div className="bento-item tall gradient">
          <Brain className="icon" size={32} />
          <h3>Agentic Logic</h3>
          <p>Award partial credit based on strict rubrics with textual justifications[cite: 32, 34].</p>
        </div>
        <div className="bento-item wide">
          <Zap className="icon" size={32} />
          <h3>High-Speed Review</h3>
          <p>TAs rapidly approve or override AI-proposed grades via optimized dashboards[cite: 35, 46].</p>
        </div>
        <div className="bento-item">
          <Shield className="icon" size={32} />
          <h3>Integrity</h3>
          <p>Detect high logic similarity to flag potential plagiarism[cite: 44].</p>
        </div>
        <div className="bento-item">
          <Cpu className="icon" size={32} />
          <h3>VLM Core</h3>
          <p>Transcribe messy handwriting using Nougat and Qwen-VL models[cite: 39, 48].</p>
        </div>
      </section>
    </div>
  );
};

export default Home;