import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import './assets/css/style.css';

// Import pages
import ParentsPage from './pages/ParentsPage';
import KidsPage from './pages/KidsPage';
import ThankYouPage from './pages/ThankYouPage';

function App() {
  return (
    <Router basename="/roblox">
      <div className="App">
        <Routes>
          <Route path="/parent" element={<ParentsPage />} />
          <Route path="/child" element={<KidsPage />} />
          <Route path="/thank-you" element={<ThankYouPage />} />
          <Route path="/" element={<Navigate to="/parent" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
