import { motion } from 'framer-motion';

export const AmbientBackground = () => {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none bg-[#fafafa]">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_120%,rgba(120,119,198,0.05),rgba(255,255,255,0))]" />
      
      {/* Orb 1 - Pastel Blue */}
      <motion.div 
        animate={{ 
          x: [0, 100, 0], 
          y: [0, -50, 0],
          scale: [1, 1.2, 1]
        }}
        transition={{ 
          duration: 20, 
          repeat: Infinity, 
          ease: "easeInOut" 
        }}
        className="absolute top-[-10%] left-[-10%] w-[50vw] h-[50vw] bg-[#a8edea]/30 rounded-full blur-[120px]"
      />

      {/* Orb 2 - Pastel Pink */}
      <motion.div 
        animate={{ 
          x: [0, -70, 0], 
          y: [0, 100, 0],
          scale: [1, 1.1, 1]
        }}
        transition={{ 
          duration: 25, 
          repeat: Infinity, 
          ease: "easeInOut",
          delay: 2
        }}
        className="absolute top-[20%] right-[-10%] w-[40vw] h-[40vw] bg-[#fed6e3]/30 rounded-full blur-[120px]"
      />

      {/* Orb 3 - Pastel Purple */}
      <motion.div 
        animate={{ 
          x: [0, 50, 0], 
          y: [0, 50, 0],
          scale: [1, 1.3, 1]
        }}
        transition={{ 
          duration: 30, 
          repeat: Infinity, 
          ease: "easeInOut",
          delay: 5
        }}
        className="absolute bottom-[-10%] left-[20%] w-[45vw] h-[45vw] bg-[#d299c2]/30 rounded-full blur-[120px]"
      />

       {/* Orb 4 - Pastel Yellow */}
       <motion.div 
        animate={{ 
          x: [0, -30, 0], 
          y: [0, -40, 0],
        }}
        transition={{ 
          duration: 22, 
          repeat: Infinity, 
          ease: "easeInOut",
          delay: 8
        }}
        className="absolute bottom-[10%] right-[10%] w-[35vw] h-[35vw] bg-[#fef9d7]/40 rounded-full blur-[100px]"
      />
    </div>
  );
};
