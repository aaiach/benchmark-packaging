import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Categories, CategoryAnalysis, JobStatus } from './pages';

import { AmbientBackground } from './components/atoms';

/**
 * Main application component with routing.
 *
 * Routes:
 * - / → Redirects to default "lait d'avoine" analysis (or first available)
 * - /categories → Category list + new job form
 * - /category/:categoryId → Category analysis page
 * - /jobs/:jobId → Job progress page
 */
export default function App() {
  return (
    <BrowserRouter>
      <AmbientBackground />
      <Routes>
        {/* Default route - shows lait d'avoine analysis */}
        <Route path="/" element={<CategoryAnalysis />} />

        {/* Categories list with new job form */}
        <Route path="/categories" element={<Categories />} />

        {/* Dynamic category analysis */}
        <Route path="/category/:categoryId" element={<CategoryAnalysis />} />

        {/* Job progress page */}
        <Route path="/jobs/:jobId" element={<JobStatus />} />

        {/* Catch-all redirect to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
