import React from 'react';
import { motion } from 'framer-motion';

const ORBS = [
  { color: '#ffb07a', width: '40vw', height: '40vw', top: '-10%', left: '-10%', delay: 0 },
  { color: '#1feeff', width: '35vw', height: '35vw', top: '10%', right: '-5%', delay: 2 },
  { color: '#ffdbde', width: '30vw', height: '30vw', bottom: '20%', left: '10%', delay: 4 },
  { color: '#ff85b3', width: '25vw', height: '25vw', bottom: '-5%', right: '10%', delay: 1 },
  { color: '#ff8a52', width: '20vw', height: '20vw', top: '40%', left: '40%', delay: 3 },
  { color: '#6666ff', width: '28vw', height: '28vw', top: '20%', right: '30%', delay: 5 },
  { color: '#ff85a3', width: '22vw', height: '22vw', bottom: '30%', right: '40%', delay: 2.5 },
];

export const AmbientBackground: React.FC = () => {
  return (
    <div className="fixed inset-0 z-0 overflow-hidden bg-[#c3dafe]">
      <div className="absolute inset-0 bg-white/30 backdrop-blur-3xl" />
      
      {ORBS.map((orb, index) => (
        <motion.div
          key={index}
          className="absolute rounded-full blur-[80px] opacity-60 mix-blend-multiply"
          style={{
            backgroundColor: orb.color,
            width: orb.width,
            height: orb.height,
            top: orb.top,
            left: orb.left,
            right: orb.right,
            bottom: orb.bottom,
          }}
          animate={{
            x: [0, 30, -30, 0],
            y: [0, -30, 30, 0],
            scale: [1, 1.1, 0.9, 1],
          }}
          transition={{
            duration: 15 + index * 2,
            repeat: Infinity,
            ease: "easeInOut",
            delay: orb.delay,
          }}
        />
      ))}
      
      <div className="absolute inset-0 bg-white/20 backdrop-blur-[100px]" />
    </div>
  );
};
