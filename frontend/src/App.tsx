import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { 
  Categories, 
  CategoryAnalysis, 
  JobStatus, 
  LandingPage, 
  SingleImageAnalysis, 
  SingleImageProgress,
  SingleImageResult, 
  Rebrand, 
  RebrandProgress,
  RebrandResult,
  RebrandsList,
  AnalysesList 
} from './pages';

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
 * - /analyses → List of completed image analyses
 * - /analyze → Single image upload form
 * - /analyze/:jobId → Image analysis job progress (redirects to /analysis/:analysisId when complete)
 * - /analysis/:analysisId → Image analysis result page
 * - /rebrands → List of all rebrand jobs
 * - /rebrand → Rebrand form
 * - /rebrand/:jobId → Rebrand job progress (redirects to /rebrand/result/:rebrandId when complete)
 * - /rebrand/result/:rebrandId → Rebrand result page
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
        <Route path="/analyses" element={<AnalysesList />} />
        <Route path="/analyze" element={<SingleImageAnalysis />} />
        <Route path="/analyze/:jobId" element={<SingleImageProgress />} />
        <Route path="/analysis/:analysisId" element={<SingleImageResult />} />

        {/* Rebrand pipeline */}
        <Route path="/rebrands" element={<RebrandsList />} />
        <Route path="/rebrand" element={<Rebrand />} />
        <Route path="/rebrand/:jobId" element={<RebrandProgress />} />
        <Route path="/rebrand/result/:rebrandId" element={<RebrandResult />} />

        {/* Catch-all redirect to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
