'use client'

import { useState, useEffect } from 'react'

const getCategoryStyles = (category: string) => {
  switch (category.toLowerCase()) {
    case 'security': return 'bg-red-500/10 text-red-400 border-red-500/30';
    case 'travel': return 'bg-blue-500/10 text-blue-400 border-blue-500/30';
    case 'writing': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
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
      } catch (err) { console.error(err) } finally { setLoading(false) }
    }
    fetchAgents()
  }, [])

  return (
    <main className="min-h-screen p-8 bg-slate-950 text-slate-100 font-sans">
      <div className="max-w-6xl mx-auto space-y-12">
        <header className="flex justify-between items-center border-b border-slate-800 pb-8">
            <h1 className="text-4xl font-black tracking-tight">
              AISAAS <span className="bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">Marketplace</span>
            </h1>
            <Link href="/" className="text-sm font-bold bg-slate-900 px-6 py-2 rounded-full border border-slate-800">BACK TO TERMINAL</Link>
        </header>

        {loading ? (
          <div className="text-center py-20 animate-pulse font-bold text-slate-600">SYNCING AGENTS...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-8">
            {agents.map((agent) => (
              <div key={agent.id} className="bg-slate-900/40 border border-slate-800 rounded-3xl p-8">
                <div className="flex justify-between items-start mb-6">
                  <h2 className="text-2xl font-bold text-white">{agent.name}</h2>
                  <span className={`px-4 py-1 rounded-full text-[10px] font-black uppercase border ${getCategoryStyles(agent.card.category)}`}>
                    {agent.card.category}
                  </span>
                </div>
                <p className="text-sm text-slate-400 mb-8 leading-relaxed">{agent.card.description}</p>
                <div className="pt-6 border-t border-slate-800/50 flex justify-between items-center">
                  <span className="font-mono text-emerald-400 font-bold">{(Number(agent.fee_wei) / 1e18).toFixed(4)} ETH</span>
                  <span className="text-[10px] text-slate-500 uppercase font-bold">Verified Agent #{agent.id}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  )
}

import Link from 'next/link'