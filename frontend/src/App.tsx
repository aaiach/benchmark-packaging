import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Categories, CategoryAnalysis, JobStatus, LandingPage, SingleImageAnalysis, SingleImageResult } from './pages';

import { AmbientBackground } from './components/atoms';

const BackgroundWrapper = () => {
  const location = useLocation();
  const isLanding = location.pathname === '/';
  
  if (isLanding) return null;
  return <AmbientBackground />;
};

/**
 * Main application component with routing.
 *
 * Routes:
 * - / → Landing Page
 * - /categories → Category list + new job form
 * - /category/:categoryId → Category analysis page
 * - /jobs/:jobId → Job progress page
 */
export default function App() {
  return (
    <BrowserRouter>
      <BackgroundWrapper />
      <Routes>
        {/* Landing Page */}
        <Route path="/" element={<LandingPage />} />

        {/* Categories list with new job form */}
        <Route path="/categories" element={<Categories />} />

        {/* Dynamic category analysis */}
        <Route path="/category/:categoryId" element={<CategoryAnalysis />} />

        {/* Job progress page */}
        <Route path="/jobs/:jobId" element={<JobStatus />} />

        {/* Single image analysis */}
        <Route path="/analyze" element={<SingleImageAnalysis />} />
        <Route path="/analyze/:jobId" element={<SingleImageResult />} />

        {/* Catch-all redirect to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
