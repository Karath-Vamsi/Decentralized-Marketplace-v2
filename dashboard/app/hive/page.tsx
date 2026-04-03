'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'
import { 
  ChevronLeft, Zap, Activity, Cpu, Radio, 
  ShieldCheck, Globe, Star, Binary, Network,
  Orbit, Scan
} from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"

export default function NeuralHive() {
  const [agents, setAgents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [hoveredAgent, setHoveredAgent] = useState<any>(null)

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const res = await fetch('http://127.0.0.1:8000/agents')
        const data = await res.json()
        setAgents(data.agents || [])
      } catch (err) { console.error(err) }
      finally { setLoading(false) }
    }
    fetchAgents()
  }, [])

  return (
    <main className="min-h-screen bg-transparent text-brand-text overflow-hidden relative selection:bg-brand-accent/20">
      
      {/* --- SURGICAL NAVIGATION HUB --- */}
      <nav className="absolute top-0 w-full p-8 flex justify-between items-start z-50 pointer-events-none">
        <div className="flex flex-col pointer-events-auto">
          <Link href="/terminal" className="flex items-center gap-2 text-brand-ash hover:text-brand-accent transition-colors text-[10px] font-black uppercase tracking-[0.4em] mb-4 group">
            <ChevronLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" /> Exit to Terminal
          </Link>
          <h1 className="text-5xl font-black tracking-tighter uppercase leading-none text-brand-accent">
            Mesh <span className="text-brand-ash font-medium italic">Topology</span>
          </h1>
          <div className="flex items-center gap-3 mt-4">
             <div className="w-1 h-1 bg-brand-accent rounded-full animate-ping" />
             <p className="text-[9px] font-bold text-brand-ash/60 uppercase tracking-[0.3em]">Mapping sovereign distribution // active_mesh_v4.0</p>
          </div>
        </div>
        
        <div className="flex items-center gap-6 bg-brand-bg/40 border border-white/5 p-5 rounded-2xl backdrop-blur-xl shadow-2xl pointer-events-auto">
           <div className="flex flex-col items-end">
              <span className="text-[8px] font-black text-brand-ash/40 uppercase tracking-[0.3em]">Network_Sync</span>
              <span className="text-[10px] font-mono font-bold text-brand-accent tracking-widest uppercase">Synchronized_Encrypted</span>
           </div>
           <Separator orientation="vertical" className="h-8 bg-white/5" />
           <div className="w-10 h-10 rounded-xl bg-brand-accent/10 flex items-center justify-center border border-brand-accent/20">
              <Radio className="w-5 h-5 text-brand-accent animate-pulse" />
           </div>
        </div>
      </nav>

      {/* --- TOPOLOGY VISUALIZATION AREA --- */}
      <div className="relative w-full h-screen flex items-center justify-center">
        
        {/* NEURAL FILAMENTS (LUMINOUS GRADIENTS) */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none">
          <defs>
            <linearGradient id="neuralFade" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="var(--brand-accent)" stopOpacity="0.2" />
              <stop offset="80%" stopColor="var(--brand-accent)" stopOpacity="0" />
            </linearGradient>
            <linearGradient id="activePulse" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="var(--brand-accent)" stopOpacity="0.6" />
              <stop offset="80%" stopColor="var(--brand-accent)" stopOpacity="0" />
            </linearGradient>
          </defs>

          {!loading && agents.map((agent, i) => {
            const angle = (i / agents.length) * 2 * Math.PI
            const hasHistory = agent.jobs_done > 0;
            const x2 = 50 + Math.cos(angle) * 30 
            const y2 = 50 + Math.sin(angle) * 30
            
            return (
              <g key={`filament-${agent.id}`}>
                <motion.line 
                  x1="50%" y1="50%" x2={`${x2}%`} y2={`${y2}%`} 
                  stroke={hasHistory ? "url(#activePulse)" : "url(#neuralFade)"} 
                  strokeWidth="1.5" 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: hasHistory ? 0.8 : 0.2 }}
                  strokeDasharray={hasHistory ? "none" : "4 4"}
                />

                {hasHistory && (
                  <motion.circle
                    r="1.5" fill="var(--brand-accent)"
                    animate={{ offsetDistance: ["0%", "100%"], opacity: [0, 1, 0] }}
                    transition={{ duration: 4, repeat: Infinity, ease: "linear", delay: i * 0.3 }}
                    style={{ 
                        offsetPath: `path('M ${typeof window !== 'undefined' ? window.innerWidth/2 : 0} ${typeof window !== 'undefined' ? window.innerHeight/2 : 0} L ${typeof window !== 'undefined' ? (x2/100)*window.innerWidth : 0} ${typeof window !== 'undefined' ? (y2/100)*window.innerHeight : 0}')`,
                        filter: 'drop-shadow(0 0 4px var(--brand-accent))'
                    }}
                  />
                )}
              </g>
            )
          })}
        </svg>

        {/* --- CENTER CORE: EXECUTIVE AUTHORITY --- */}
        <motion.div 
          animate={{ scale: [1, 1.05, 1] }} 
          transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }} 
          className="relative z-20 w-44 h-44 flex items-center justify-center"
        >
          <div className="absolute inset-0 bg-brand-accent/5 rounded-full blur-[80px] animate-pulse" />
          <div className="w-24 h-24 bg-brand-accent text-brand-bg rounded-full flex items-center justify-center shadow-[0_0_50px_rgba(247,245,242,0.2)] border border-white/20">
            <Cpu className="w-10 h-10" />
          </div>
          <div className="absolute -bottom-12 whitespace-nowrap">
            <span className="text-[10px] font-black uppercase tracking-[0.6em] text-brand-accent">Executive_Root</span>
          </div>
        </motion.div>

        {/* --- SATELLITE NODES --- */}
        {!loading && agents.map((agent, i) => {
          const angle = (i / agents.length) * 2 * Math.PI
          const radius = 320 
          const x = Math.cos(angle) * radius
          const y = Math.sin(angle) * radius
          const isBottom = y > 50; const isRight = x > 0;
          const hasHistory = agent.jobs_done > 0;

          return (
            <motion.div
              key={agent.id}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1, x, y }}
              onMouseEnter={() => setHoveredAgent(agent)}
              onMouseLeave={() => setHoveredAgent(null)}
              className="absolute cursor-crosshair"
              style={{ zIndex: hoveredAgent?.id === agent.id ? 100 : 30 }}
            >
              <div className={`w-12 h-12 rounded-xl border flex items-center justify-center transition-all duration-500 relative backdrop-blur-md
                ${hasHistory ? 'border-brand-accent/40 bg-brand-accent/10' : 'border-white/5 bg-white/5'}
                ${hoveredAgent?.id === agent.id ? 'scale-125 border-brand-accent bg-brand-accent text-brand-bg shadow-[0_0_30px_rgba(247,245,242,0.3)]' : 'text-brand-ash'}`}
              >
                {hasHistory && !hoveredAgent && (
                    <div className="absolute inset-0 border border-brand-accent/30 rounded-xl animate-ping opacity-20" />
                )}
                <Zap className={`w-5 h-5 ${hoveredAgent?.id === agent.id ? 'text-brand-bg' : hasHistory ? 'text-brand-accent' : 'text-brand-ash/40'}`} />
              </div>

              {/* SURGICAL HUD POPUP */}
              <AnimatePresence>
                {hoveredAgent?.id === agent.id && (
                  <motion.div 
                    initial={{ opacity: 0, y: isBottom ? -10 : 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: isBottom ? -45 : 45, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className={`absolute whitespace-nowrap glass-forest p-6 rounded-2xl border-brand-accent/20 z-[100] shadow-2xl min-w-[240px]
                        ${isBottom ? 'bottom-full mb-4' : 'top-full mt-4'} 
                        ${isRight ? 'right-0' : 'left-0'}
                    `}
                  >
                    <div className="flex items-center justify-between mb-3">
                       <span className="text-[9px] font-black text-brand-accent uppercase tracking-widest">{agent.category}</span>
                       <Badge variant="outline" className="text-[7px] border-brand-accent/20 text-brand-accent h-4">ID: 0x{agent.id}</Badge>
                    </div>
                    
                    <p className="text-2xl font-bold tracking-tight text-brand-text mb-4">{agent.name}</p>
                    
                    <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/5 font-mono">
                        <div className="flex flex-col">
                            <span className="text-[7px] text-brand-ash uppercase tracking-widest">Throughput</span>
                            <span className="text-[10px] font-bold text-brand-accent">{agent.jobs_done} CYCLES</span>
                        </div>
                        <div className="flex flex-col border-l border-white/5 pl-4">
                            <span className="text-[7px] text-brand-ash uppercase tracking-widest">Reputation</span>
                            <div className="flex items-center gap-1">
                                <Star className="w-2.5 h-2.5 fill-brand-accent text-brand-accent" />
                                <span className="text-[10px] font-bold text-brand-text">{agent.rating.toFixed(1)}</span>
                            </div>
                        </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )
        })}
      </div>

      {/* --- FOOTER DATA STREAM --- */}
      <div className="absolute bottom-10 w-full px-10 flex justify-between items-end">
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-3">
               <div className="w-8 h-[1px] bg-brand-accent/20" />
               <span className="text-[9px] font-bold text-brand-ash/40 uppercase tracking-widest">Protocol_Link: Sovereign_A2A_Mesh</span>
            </div>
            <div className="flex items-center gap-2">
               <Scan className="w-3 h-3 text-brand-accent animate-pulse" />
               <p className="text-[9px] font-black text-brand-accent uppercase tracking-[0.4em]">Live_Topology_Scan_Active</p>
            </div>
          </div>
          
          <div className="text-right space-y-2">
            <div className="flex items-center gap-4 justify-end">
                <Network className="w-5 h-5 text-brand-ash/40" />
                <span className="text-4xl font-black text-brand-accent tracking-tighter">{agents.length}</span>
            </div>
            <p className="text-[9px] font-black text-brand-ash/30 uppercase tracking-[0.2em]">Active_Specialist_Nodes</p>
          </div>
      </div>
    </main>
  )
}