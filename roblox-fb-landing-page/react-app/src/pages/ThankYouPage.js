import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const ThankYouPage = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Simple confetti animation
    const confettiContainer = document.querySelector('.confetti');
    const colors = ['#ffecb3', '#ffd54f', '#ff8a65', '#81d4fa', '#b39ddb', '#a5d6a7'];
    const count = 40;

    // Clear any existing confetti
    if (confettiContainer) {
      confettiContainer.innerHTML = '';
      
      for (let i = 0; i < count; i++) {
        const piece = document.createElement('div');
        piece.classList.add('confetti-piece');
        piece.style.background = colors[Math.floor(Math.random() * colors.length)];
        piece.style.left = Math.random() * 100 + '%';
        piece.style.animationDelay = (Math.random() * 2) + 's';
        piece.style.animationDuration = (2 + Math.random() * 2) + 's';
        piece.style.transform = `scale(${0.7 + Math.random() * 0.6})`;
        confettiContainer.appendChild(piece);
      }
    }
  }, []);

  const handleGetMoreInfo = () => {
    navigate('/parent');
  };

  return (
    <div style={{ 
      margin: 0,
      fontFamily: '"Poppins", system-ui, -apple-system, BlinkMacSystemFont, sans-serif',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 60%)',
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: '#2d2d44'
    }}>
      <div style={{
        margin: '0 auto',
        background: 'rgba(255, 255, 255, 0.95)',
        padding: '2.5rem 2rem',
        borderRadius: '18px',
        boxShadow: '0 30px 60px -10px rgba(0, 0, 0, 0.25)',
        width: '80%',
        height: '500px',
        textAlign: 'center',
        position: 'relative',
        overflow: 'hidden',
        animation: 'fadeIn 0.8s ease-out'
      }}>
        <div style={{
          width: '80px',
          height: '80px',
          margin: '0 auto 1rem',
          background: 'radial-gradient(circle at 30% 30%, #ffffff, #f0f4ff)',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 12px 30px -5px rgba(102, 126, 234, 0.6)'
        }}>
          <svg viewBox="0 0 24 24" style={{
            width: '40px',
            height: '40px',
            stroke: '#667eea',
            strokeWidth: '3',
            strokeLinecap: 'round',
            strokeLinejoin: 'round',
            fill: 'none'
          }}>
            <path d="M5 13l4 4L19 7" />
          </svg>
        </div>

        <div className="confetti" style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: 0,
          pointerEvents: 'none',
          zIndex: 9999
        }}></div>
        
        <h1 style={{
          margin: '0.25rem 0',
          fontSize: '2.2rem',
          fontWeight: '700',
          lineHeight: '1.1',
          color: '#2d2d44'
        }}>Thank You!</h1>
        
        <p style={{
          margin: '0.75rem 0 1.75rem',
          fontSize: '1rem',
          fontWeight: '500',
          color: '#555a7b'
        }}>Your Request Has Been Received</p>
        
        <p style={{
          margin: '0.75rem 0 1.75rem',
          fontSize: '1rem',
          fontWeight: '500',
          color: '#555a7b'
        }}>
          We've received your details and our team will review your concern.
          In the meantime, here's important information that can help you right now.
        </p>
        
        <button 
          onClick={handleGetMoreInfo}
          style={{
            textDecoration: 'none',
            fontSize: '1.2rem',
            background: 'linear-gradient(270deg, #64FFDA, #02e0e0, #64FFDA)',
            border: '1px solid #64FFDA',
            color: '#000000',
            fontWeight: '600',
            padding: '12px 40px',
            borderRadius: '30px',
            backgroundSize: '400% 400%',
            boxShadow: 'inset 0px 0px 0px 5px rgba(255, 255, 255, 1)',
            cursor: 'pointer',
            transition: 'all 0.3s ease'
          }}
          onMouseEnter={(e) => {
            e.target.style.animation = 'gradientShift 3s linear infinite';
          }}
          onMouseLeave={(e) => {
            e.target.style.animation = 'none';
          }}
        >
          Get more information
        </button>
      </div>
      
      <div style={{ position: 'absolute', bottom: '20px', width: '100%' }}>
        <p style={{
          fontSize: '0.85rem',
          color: '#d3d3d3',
          margin: '1rem',
          textAlign: 'center'
        }}>
          Note: The guide contains detailed legal and safety information for parents and guardians.
          We recommend reviewing it together as a family.
        </p>
      </div>

      <style jsx>{`
        .confetti-piece {
          position: absolute;
          width: 10px;
          height: 10px;
          opacity: 0.9;
          border-radius: 50%;
          animation-name: fall;
          animation-timing-function: linear;
          animation-iteration-count: infinite;
        }

        @keyframes fall {
          0% {
            transform: translateY(-100px) rotate(0deg);
            opacity: 1;
          }
          100% {
            transform: translateY(100vh) rotate(360deg);
            opacity: 0;
          }
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(12px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes gradientShift {
          0% {
            background-position: 0% 50%;
          }
          50% {
            background-position: 100% 50%;
          }
          100% {
            background-position: 0% 50%;
          }
        }

        @media screen and (max-width: 768px) {
          .card {
            padding: 1.5rem 1rem;
            width: 95%;
          }
          h1 {
            font-size: 1.8rem;
          }
          p {
            font-size: 0.9rem;
          }
        }

        @media (prefers-reduced-motion: reduce) {
          .card {
            animation: none;
          }
          .confetti-piece {
            animation: none;
          }
        }
      `}</style>
    </div>
  );
};

export default ThankYouPage;
