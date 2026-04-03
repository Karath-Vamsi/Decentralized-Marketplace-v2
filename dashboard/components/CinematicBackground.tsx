'use client'

import { motion } from 'framer-motion'
import { useEffect, useState, useMemo } from 'react'

interface Particle {
  id: number;
  size: number;
  x: number;
  y: number;
  duration: number;
  delay: number;
  color: string;
}

export default function CinematicBackground() {
  const [mounted, setMounted] = useState(false)

  // Use useMemo to ensure particles are only generated once and don't trigger re-renders
  const particles = useMemo(() => {
    return Array.from({ length: 20 }).map((_, i) => ({
      id: i,
      size: Math.random() * 2 + 1,
      x: Math.random() * 100,
      y: Math.random() * 100,
      duration: Math.random() * 20 + 20,
      delay: Math.random() * -20, // Negative delay starts them mid-animation
      color: Math.random() > 0.5 ? '#A3B8AE' : '#D6EDE6',
    }))
  }, [])

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) return <div className="fixed inset-0 bg-brand-bg z-0" />

  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-0 bg-brand-bg">
      
      {/* LAYER 1: ATMOSPHERIC DEPTH (Surgical Gradients) */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_-20%,_var(--brand-bg-light)_0%,_transparent_70%)] opacity-40" />
      
      {/* LAYER 2: THE "LUMINOUS FOREST" GLOWS (Optimized Blur) */}
      <motion.div 
        animate={{ 
          opacity: [0.05, 0.1, 0.05],
          scale: [1, 1.05, 1],
        }}
        transition={{ duration: 15, repeat: Infinity, ease: "easeInOut" }}
        className="absolute top-[-10%] left-[-10%] w-[70%] h-[70%] bg-brand-bg-light/20 blur-[120px] rounded-full"
      />
      
      <motion.div 
        animate={{ 
          opacity: [0.03, 0.08, 0.03],
          scale: [1.1, 1, 1.1],
        }}
        transition={{ duration: 20, repeat: Infinity, ease: "easeInOut" }}
        className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] bg-white/5 blur-[140px] rounded-full"
      />

      {/* LAYER 3: FLOATING LIGHT MOTES (Performance Optimized) */}
      {particles.map((p) => (
        <motion.div
          key={p.id}
          initial={{ opacity: 0, x: `${p.x}%`, y: `${p.y}%` }}
          animate={{ 
            y: [`${p.y}%`, `${p.y - 5}%`, `${p.y}%`],
            opacity: [0, 0.2, 0],
          }}
          transition={{
            duration: p.duration,
            repeat: Infinity,
            delay: p.delay,
            ease: "linear"
          }}
          style={{ 
            width: p.size, 
            height: p.size,
            backgroundColor: p.color,
            boxShadow: `0 0 8px ${p.color}30` 
          }}
          className="absolute rounded-full"
        />
      ))}

      {/* LAYER 4: VIGNETTE */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_transparent_40%,_rgba(5,20,13,0.4)_100%)]" />
    </div>
  )
}