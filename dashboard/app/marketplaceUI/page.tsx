'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  ChevronLeft, 
  Zap, 
  Globe, 
  Activity, 
  Star, 
  Cpu, 
  Search,
  CheckCircle2,
  ArrowUpRight,
  Database,
  ShieldCheck,
  Coins,
  LayoutGrid,
  Lock
} from 'lucide-react'
import { Button } from "@/components/ui/button"
// import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"

// Category Mapping tuned for the Surgical Palette
const getCategoryStyles = (category: string) => {
  const cat = category?.toLowerCase();
  switch (cat) {
    case 'security': 
      return { color: 'text-brand-accent', bg: 'bg-brand-accent/5', border: 'border-brand-accent/20', icon: <ShieldCheck className="w-3.5 h-3.5" /> };
    case 'travel': 
      return { color: 'text-brand-ash', bg: 'bg-brand-ash/5', border: 'border-brand-ash/20', icon: <Globe className="w-3.5 h-3.5" /> };
    case 'utility': 
      return { color: 'text-brand-text', bg: 'bg-brand-text/5', border: 'border-brand-text/20', icon: <Database className="w-3.5 h-3.5" /> };
    default: 
      return { color: 'text-brand-ash', bg: 'bg-white/5', border: 'border-white/10', icon: <Cpu className="w-3.5 h-3.5" /> };
  }
}

export default function MarketplaceDirectory() {
  const [agents, setAgents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const res = await fetch('http://127.0.0.1:8000/agents')
        const data = await res.json()
        setAgents(data.agents || [])
      } catch (err) { 
        console.error("Failed to fetch agents:", err) 
      } finally { 
        setLoading(false) 
      }
    }
    fetchAgents()
  }, [])

  return (
    <main className="min-h-screen bg-transparent text-brand-text selection:bg-brand-accent/20 pb-32">
      
      {/* --- SURGICAL HEADER --- */}
      <header className="h-20 border-b border-white/5 bg-brand-bg/40 backdrop-blur-xl sticky top-0 z-50 flex items-center">
        <div className="max-w-7xl mx-auto w-full px-6 flex justify-between items-center">
          <div className="flex items-center gap-8">
            <Link href="/terminal" className="group flex items-center gap-2 text-brand-ash hover:text-brand-accent transition-colors text-[10px] font-black uppercase tracking-widest">
              <ChevronLeft size={16} className="group-hover:-translate-x-1 transition-transform" />
              Exit to Terminal
            </Link>
            <Separator orientation="vertical" className="h-4 bg-white/10" />
            <h1 className="text-xl font-black tracking-tight text-brand-accent uppercase">
              Agent <span className="text-brand-ash font-medium italic">Registry</span>
            </h1>
          </div>

          <div className="flex items-center gap-4 bg-white/5 border border-white/5 px-4 py-2 rounded-xl backdrop-blur-md">
            <Search className="w-4 h-4 text-brand-ash" />
            <span className="text-[10px] font-bold uppercase tracking-widest text-brand-ash/50 pr-4">Search_Protocol</span>
            <Separator orientation="vertical" className="h-3 bg-white/10" />
            <div className="flex items-center gap-2 ml-2">
               <div className="w-1.5 h-1.5 bg-brand-accent rounded-full animate-pulse" />
               <span className="text-[10px] font-black text-brand-accent uppercase">{agents.length} Nodes</span>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 pt-16">
        {loading ? (
          <div className="h-[60vh] flex flex-col items-center justify-center opacity-20">
            <Activity className="w-12 h-12 animate-pulse mb-6 text-brand-accent" />
            <p className="font-black text-[10px] uppercase tracking-[1em]">Establishing_Ledger_Sync</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            <AnimatePresence>
              {agents.map((agent, index) => {
                const style = getCategoryStyles(agent.category);
                return (
                  <motion.div 
                    key={agent.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="glass-forest group relative flex flex-col p-8 rounded-2xl border border-white/5 hover:border-brand-accent/20 transition-all duration-500"
                  >
                    {/* Top Section: Identity & Status */}
                    <div className="flex justify-between items-start mb-6">
                      <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border ${style.bg} ${style.border} ${style.color}`}>
                        {style.icon}
                        <span className="text-[9px] font-black uppercase tracking-widest">{agent.category}</span>
                      </div>
                      {agent.jobs_done > 0 && (
                        <div className="flex items-center gap-1.5 text-brand-accent/60">
                          <CheckCircle2 size={14} />
                          <span className="text-[9px] font-bold uppercase tracking-tighter">Verified</span>
                        </div>
                      )}
                    </div>

                    {/* Agent Identification */}
                    <h2 className="text-2xl font-bold tracking-tight text-brand-accent mb-2 group-hover:translate-x-1 transition-transform duration-300">
                      {agent.name}
                    </h2>
                    <p className="text-xs text-brand-ash/70 leading-relaxed mb-8 line-clamp-2 italic">
                      "{agent.card.description}"
                    </p>

                    {/* Technical Specs Grid */}
                    <div className="grid grid-cols-2 gap-px bg-white/5 border border-white/5 rounded-xl overflow-hidden mb-8">
                      <div className="bg-brand-bg/40 p-4">
                        <span className="text-[8px] text-brand-ash/40 uppercase block mb-1">Reputation</span>
                        <div className="flex items-center gap-1.5">
                          <Star size={12} className="text-brand-accent fill-brand-accent" />
                          <span className="text-sm font-bold">{agent.rating > 0 ? agent.rating.toFixed(1) : "NEW"}</span>
                        </div>
                      </div>
                      <div className="bg-brand-bg/40 p-4">
                        <span className="text-[8px] text-brand-ash/40 uppercase block mb-1">Total Cycles</span>
                        <div className="flex items-center gap-1.5">
                          <Activity size={12} className="text-brand-text" />
                          <span className="text-sm font-mono font-bold text-brand-text">{agent.jobs_done || 0}</span>
                        </div>
                      </div>
                    </div>

                    {/* Bottom Action Area */}
                    <div className="mt-auto pt-6 border-t border-white/5 flex items-center justify-between">
                      <div className="flex flex-col">
                        <span className="text-[8px] text-brand-ash/50 uppercase font-black tracking-widest">Protocol Fee</span>
                        <div className="flex items-baseline gap-1">
                          <span className="text-xl font-black text-brand-accent">{(Number(agent.fee_wei) / 1e18).toFixed(4)}</span>
                          <span className="text-[9px] font-mono text-brand-ash">ETH</span>
                        </div>
                      </div>
                      <Button asChild variant="outline" className="rounded-xl border-white/10 hover:bg-brand-accent hover:text-brand-bg group/btn px-6 h-12">
                        <Link href="/terminal" className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest">
                          Initialize <ArrowUpRight size={14} className="group-hover/btn:translate-x-0.5 group-hover/btn:-translate-y-0.5 transition-transform" />
                        </Link>
                      </Button>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        )}
      </div>

      {/* --- MARKET FOOTER STRIP --- */}
      <footer className="fixed bottom-0 left-0 w-full h-16 bg-brand-bg-dark/60 backdrop-blur-2xl border-t border-white/5 flex items-center px-8 justify-between z-40">
         <div className="flex items-center gap-4 text-brand-ash/40">
            <div className="flex items-center gap-2">
              <Coins size={14} />
              <span className="text-[9px] font-black uppercase tracking-widest">Liquidity: 0.94 Stable</span>
            </div>
            <Separator orientation="vertical" className="h-3 bg-white/10" />
            <div className="flex items-center gap-2">
              <Lock size={14} />
              <span className="text-[9px] font-black uppercase tracking-widest">EVM_SECURED</span>
            </div>
         </div>
         <p className="text-[8px] font-bold text-brand-ash/20 uppercase tracking-[0.3em]">System v4.0 // Sovereign Collective</p>
      </footer>
    </main>
  )
}