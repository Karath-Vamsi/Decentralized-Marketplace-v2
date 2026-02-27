'use client'

import { useState, useEffect } from 'react'

// Helper to assign specific colors based on the agent's category
const getCategoryStyles = (category: string) => {
  switch (category.toLowerCase()) {
    case 'security': return 'bg-red-500/10 text-red-400 border-red-500/30 shadow-[0_0_15px_rgba(239,68,68,0.1)]';
    case 'utility': return 'bg-purple-500/10 text-purple-400 border-purple-500/30 shadow-[0_0_15px_rgba(168,85,247,0.1)]';
    case 'travel': return 'bg-blue-500/10 text-blue-400 border-blue-500/30 shadow-[0_0_15px_rgba(59,130,246,0.1)]';
    case 'writing': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.1)]';
    default: return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
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
        console.error("Failed to load marketplace:", err)
      } finally {
        setLoading(false)
      }
    }
    fetchAgents()
  }, [])

  return (
    <main className="min-h-screen p-8 bg-slate-950 text-slate-100 font-sans selection:bg-blue-500/30">
      <div className="max-w-6xl mx-auto space-y-12">
        
        {/* Header */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-slate-800 pb-8 gap-4">
          <div>
            <h1 className="text-4xl font-black tracking-tight">
              AISAAS <span className="bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">Marketplace</span>
            </h1>
            <p className="text-slate-400 mt-2 text-sm font-medium">Decentralized Autonomous Agent Directory</p>
          </div>
          <div className="flex items-center gap-3 bg-slate-900 border border-slate-800 px-4 py-2 rounded-full shadow-inner">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
            <span className="text-xs font-bold text-emerald-400 tracking-widest uppercase">Network Live</span>
          </div>
        </header>

        {/* Grid Layout */}
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-pulse text-slate-500 tracking-widest text-sm font-bold">SYNCING WITH BLOCKCHAIN...</div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-8">
            {agents.map((agent) => {
              const category = agent.card.category || 'general'
              const colorStyles = getCategoryStyles(category)
              // Convert Wei to ETH manually to avoid needing ethers.js in this file
              const feeInEth = (Number(agent.fee_wei) / 1e18).toFixed(4)

              return (
                <div 
                  key={agent.id} 
                  className="group relative bg-slate-900/40 backdrop-blur-sm border border-slate-800 rounded-2xl p-6 hover:border-slate-600 transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl"
                >
                  {/* Top Bar: Name & Category */}
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h2 className="text-2xl font-bold text-white group-hover:text-blue-400 transition-colors">
                        {agent.name}
                      </h2>
                      <p className="text-xs text-slate-500 font-mono mt-1">ID: #{agent.id} • DEV: {agent.card.developer}</p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border ${colorStyles}`}>
                      {category}
                    </span>
                  </div>

                  {/* Description */}
                  <p className="text-sm text-slate-300 mb-6 leading-relaxed min-h-[60px]">
                    {agent.card.description}
                  </p>

                  {/* Tags */}
                  <div className="flex flex-wrap gap-2 mb-6">
                    {agent.card.tags?.map((tag: string) => (
                      <span key={tag} className="text-[10px] bg-slate-950 text-slate-400 px-2 py-1 rounded border border-slate-800">
                        #{tag}
                      </span>
                    ))}
                  </div>

                  {/* Footer: Price & Status */}
                  <div className="flex justify-between items-center pt-4 border-t border-slate-800/50">
                    <div className="flex flex-col">
                      <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Base Fee</span>
                      <span className="font-mono text-emerald-400 font-bold">{feeInEth} ETH</span>
                    </div>
                    <button className="bg-slate-800 hover:bg-blue-600 text-white text-xs font-bold py-2 px-6 rounded-lg transition-colors border border-slate-700 hover:border-blue-500">
                      VIEW CONTRACT
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </main>
  )
}