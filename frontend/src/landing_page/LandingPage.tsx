import React from 'react';
import { AmbientBackground } from './components/AmbientBackground';
import { RunForm } from './components/RunForm';
import { ExampleCards } from './components/ExampleCards';
import { LandingTitle, LandingSubtitle } from './components/Typography';
import { motion } from 'framer-motion';
import { LANDING_CONTENT } from './content';

const LandingPageContent: React.FC = () => {
  return (
    <div className="min-h-screen relative font-sans text-black selection:bg-purple-200 selection:text-purple-900">
      <AmbientBackground />
      
      <main className="relative z-10 flex flex-col items-center justify-center min-h-screen py-20 px-4">
        
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="w-full max-w-4xl mx-auto text-center mb-16"
        >
          <LandingTitle>
            {LANDING_CONTENT.hero.title.part1}
            <span className="block mt-3 text-xl sm:text-2xl font-normal italic text-black/40">
              {LANDING_CONTENT.hero.title.highlight}
            </span>
          </LandingTitle>
          
          <LandingSubtitle>
            {LANDING_CONTENT.hero.subtitle}
          </LandingSubtitle>

          <div className="mb-24">
            <RunForm />
          </div>

          <div className="text-left w-full max-w-6xl mx-auto mb-8 pl-4 border-l-2 border-black/10">
            <h3 className="text-xl font-light text-black/80">{LANDING_CONTENT.recentAnalysis.title}</h3>
            <p className="text-sm text-black/40">{LANDING_CONTENT.recentAnalysis.subtitle}</p>
          </div>
          
          <ExampleCards />
        </motion.div>
        
        <footer className="absolute bottom-4 text-center w-full text-black/20 text-xs font-light">
          {LANDING_CONTENT.footer}
        </footer>
      </main>
    </div>
  );
};

export default LandingPageContent;
