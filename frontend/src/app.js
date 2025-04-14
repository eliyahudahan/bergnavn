import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import CruisePage from './pages/cruise_page';
import Home from './pages/home';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/cruise" element={<CruisePage />} />
      </Routes>
    </Router>
  );
}

export default App;
