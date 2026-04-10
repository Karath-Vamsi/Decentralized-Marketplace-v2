'use client'

import { useAccount, useConnect } from 'wagmi'
import { injected } from 'wagmi/connectors'
import { motion, useScroll, useTransform } from 'framer-motion'
import { useRouter } from 'next/navigation'
import { useEffect, useRef } from 'react'
import { 
  Zap, Waypoints, Fingerprint, Binary, 
  Activity, Lock, Landmark, Database, ShieldCheck,
  ChevronRight, ArrowUpRight
} from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"

const FEATURES = [
  { title: "Global Registry", icon: <Waypoints />, desc: "A verified network of specialized autonomous agents." },
  { title: "iNFT Identity", icon: <Fingerprint />, desc: "Cryptographically proven agent credentials." },
  { title: "Executive Genome", icon: <Binary />, desc: "Local behavioral modeling and secure state management." },
  { title: "Compute Market", icon: <Activity />, desc: "Peer-to-peer liquidity for high-performance agent tasks." },
  { title: "Smart Escrow", icon: <Lock />, desc: "Financial settlement secured by Ethereum smart contracts." },
  { title: "Sovereign Economy", icon: <Landmark />, desc: "Native ETH transactions with zero platform fees." },
];

export default function AISAASLanding() {
  const { isConnected } = useAccount()
  const { connect } = useConnect()
  const router = useRouter()
  const targetRef = useRef(null)
  
  const { scrollYProgress } = useScroll({
    target: targetRef,
    offset: ["start start", "end start"]
  })

  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0])
  const scale = useTransform(scrollYProgress, [0, 0.5], [1, 0.95])

  // AUTH LOGIC (PRESERVED)
  useEffect(() => {
    if (isConnected) router.push('/terminal')
  }, [isConnected, router])

  return (
    <div ref={targetRef} className="relative min-h-screen selection:bg-brand-accent selection:text-brand-bg">
      
      {/* --- HERO SECTION --- */}
      <section className="relative h-screen flex flex-col items-center justify-center px-6 overflow-hidden">
        <motion.div style={{ opacity, scale }} className="z-20 text-center">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8 inline-flex items-center gap-2 px-3 py-1 rounded-full border border-brand-accent/30 bg-brand-bg-light/40 backdrop-blur-md"
          >
            <span className="w-2 h-2 rounded-full bg-brand-accent animate-pulse" />
            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-brand-accent">System v4.0 Active</span>
          </motion.div>

          <h1 className="text-[12vw] md:text-[9rem] font-black tracking-tighter leading-[0.8] text-brand-accent drop-shadow-[0_0_40px_rgba(247,245,242,0.2)]">
            AISAAS
          </h1>
          
          <p className="mt-10 text-xl md:text-3xl tracking-[0.2em] text-brand-accent uppercase font-bold max-w-4xl mx-auto">
            A Decentralized Marketplace
            <span className="block mt-4 text-3xl md:text-6xl font-black tracking-tighter uppercase text-brand-accent/90">
              for intelligent AI services
            </span>
          </p>
        </motion.div>

        {/* Ambient background glow for Hero */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-brand-bg-light/30 blur-[150px] pointer-events-none rounded-full" />
      </section>

      {/* --- VALUE PROPOSITION (The Three Pillars) --- */}
      <section className="relative z-20 py-32 px-6 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <Card className="glass-forest p-8 group hover:border-brand-accent/40 transition-all duration-500">
            <div className="text-brand-accent mb-6"><Waypoints size={32} /></div>
            <h3 className="text-2xl font-black tracking-tight uppercase text-brand-accent mb-4">The Marketplace</h3>
            <p className="text-brand-accent/70 font-medium leading-relaxed">Discover specialized worker agents for complex task orchestration with peer-to-peer liquidity.</p>
          </Card>
          <Card className="glass-forest p-8 group hover:border-brand-accent/40 transition-all duration-500">
            <div className="text-brand-accent mb-6"><Fingerprint size={32} /></div>
            <h3 className="text-2xl font-black tracking-tight uppercase text-brand-accent mb-4">Sovereign Executive</h3>
            <p className="text-brand-accent/70 font-medium leading-relaxed">A digital twin logic layer that acts as your personal proxy for governance and permissions.</p>
          </Card>
          <Card className="glass-forest p-8 group hover:border-brand-accent/40 transition-all duration-500">
            <div className="text-brand-accent mb-6"><ShieldCheck size={32} /></div>
            <h3 className="text-2xl font-black tracking-tight uppercase text-brand-accent mb-4">Zero-Trust Mesh</h3>
            <p className="text-brand-accent/70 font-medium leading-relaxed">Encrypted agent-to-agent communication protocols running on a decentralized infrastructure.</p>
          </Card>
        </div>
      </section>

      {/* --- FEATURE GRID (Linear Style) --- */}
      <section className="relative z-20 py-32 bg-brand-bg-dark/60 border-y border-brand-accent/10">
        <div className="max-w-7xl mx-auto px-6">
          <div className="mb-20">
            <h2 className="text-4xl md:text-6xl font-black text-brand-accent tracking-tighter uppercase">ENGINEERED FOR <br/>AUTONOMY.</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-px bg-brand-accent/10 border border-brand-accent/10 overflow-hidden rounded-3xl">
            {FEATURES.map((feature, i) => (
              <div key={i} className="bg-brand-bg p-10 hover:bg-brand-bg-light/40 transition-colors group">
                <div className="w-10 h-10 rounded-lg bg-brand-bg-light flex items-center justify-center text-brand-accent mb-6 border border-brand-accent/10 group-hover:scale-110 transition-transform">
                  {feature.icon}
                </div>
                <h4 className="text-xl font-black text-brand-accent mb-3 uppercase tracking-tight">{feature.title}</h4>
                <p className="text-sm font-medium text-brand-accent/70 leading-relaxed">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* --- FINAL CONVERSION CALLOUT --- */}
      <section className="relative py-40 px-6 text-center">
        <h2 className="text-5xl md:text-7xl font-black tracking-tighter uppercase text-brand-accent mb-8">Start your sovereign journey</h2>
        <p className="text-brand-accent/80 max-w-2xl mx-auto mb-12 text-lg font-medium">Initialize your Digital Twin and access a global network of autonomous intelligence today.</p>
        <Button 
          onClick={() => connect({ connector: injected() })}
          className="h-16 px-12 rounded-full text-lg font-black tracking-widest uppercase bg-brand-accent text-brand-bg hover:scale-105 hover:shadow-[0_0_30px_rgba(247,245,242,0.3)] transition-all"
        >
          CONNECT WALLET <ArrowUpRight className="ml-2 w-6 h-6" />
        </Button>
      </section>

      {/* --- STICKY CTA (BOTTOM RIGHT CLUSTER) --- */}
      <div className="fixed bottom-10 right-10 z-[100] flex flex-col items-end gap-4">
        <motion.div 
          initial={{ x: 100, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ delay: 1 }}
        >
          <button 
            onClick={() => connect({ connector: injected() })}
            className="btn-pill-initialize shadow-[0_0_40px_rgba(247,245,242,0.15)] flex items-center gap-3 bg-brand-accent text-brand-bg"
          >
            <span>Get Started</span>
            <Zap size={14} className="fill-current" />
          </button>
        </motion.div>
      </div>

      {/* Footer Branding */}
      <footer className="py-12 px-6 border-t border-brand-accent/10 text-center">
        <p className="text-[10px] font-black uppercase tracking-[1em] text-brand-accent/30">
          AISAAS // SPATIAL OS V4.0
        </p>
      </footer>
    </div>
  )
}