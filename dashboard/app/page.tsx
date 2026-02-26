'use client'

import { useState, useEffect } from 'react'
import { useAccount, useConnect, useDisconnect } from 'wagmi'
import { injected } from 'wagmi/connectors'

export default function Dashboard() {
  const { address, isConnected } = useAccount()
  const { connect } = useConnect()
  const { disconnect } = useDisconnect()
  
  const [prompt, setPrompt] = useState('')
  const [chatResponse, setChatResponse] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [mounted, setMounted] = useState(false)

  // Evolution States
  const [identityText, setIdentityText] = useState('')
  const [docTitle, setDocTitle] = useState('')
  const [docContent, setDocContent] = useState('')
  const [isEvolving, setIsEvolving] = useState(false)
  
  // Knowledge Base View States
  const [knowledgeFiles, setKnowledgeFiles] = useState<string[]>([])
  const [viewingKB, setViewingKB] = useState(false)

  useEffect(() => { setMounted(true) }, [])

  const askAI = async () => {
    if (!address || !prompt || isLoading) return
    setIsLoading(true); setChatResponse('')
    try {
      const res = await fetch('http://127.0.0.1:8000/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, wallet_address: address })
      })
      const data = await res.json()
      setChatResponse(res.ok ? data.answer : `Error: ${data.detail}`)
    } catch { setChatResponse("Server offline.") }
    finally { setIsLoading(false); setPrompt('') }
  }

  const handleEvolution = async (type: 'identity' | 'knowledge') => {
    setIsEvolving(true)
    const endpoint = type === 'identity' ? '/update-identity' : '/add-knowledge'
    const payload = type === 'identity' 
      ? { content: identityText, wallet_address: address }
      : { filename: docTitle, content: docContent, wallet_address: address }

    try {
      const res = await fetch(`http://127.0.0.1:8000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (res.ok) {
        alert("Evolution Successful!");
        setIdentityText(''); setDocTitle(''); setDocContent('');
        fetchKnowledgeList(); // Refresh the list automatically
      }
    } catch { alert("Evolution failed.") }
    finally { setIsEvolving(false) }
  }

  const fetchKnowledgeList = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/list-knowledge')
      const data = await res.json()
      setKnowledgeFiles(data.files)
      setViewingKB(true)
    } catch { alert("Could not fetch knowledge base list.") }
  }

  if (!mounted) return null

  return (
    <main className="min-h-screen p-8 bg-slate-950 text-slate-100 font-sans">
      <div className="max-w-4xl mx-auto space-y-12">
        
        {/* HEADER */}
        <header className="flex justify-between items-center border-b border-slate-800 pb-8">
          <h1 className="text-3xl font-black bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">AISAAS 2.0</h1>
          {!isConnected ? (
            <button onClick={() => connect({ connector: injected() })} className="px-6 py-2 bg-blue-600 rounded-full font-bold">Connect Wallet</button>
          ) : (
            <div className="flex items-center gap-4 bg-slate-900 p-2 px-4 rounded-full border border-slate-800 text-xs">
              {address?.slice(0,6)}...{address?.slice(-4)}
              <button onClick={() => disconnect()} className="text-red-400 font-bold ml-2">EXIT</button>
            </div>
          )}
        </header>

        {isConnected ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            
            {/* LEFT: CHAT INTERFACE */}
            <section className="space-y-6">
              <h2 className="text-xl font-bold text-blue-400 uppercase tracking-widest">Digital Twin Terminal</h2>
              <div className={`p-6 rounded-2xl border min-h-[300px] ${isLoading ? 'bg-slate-900 animate-pulse border-blue-500/50' : 'bg-slate-900 border-slate-800'}`}>
                <div className="prose prose-invert max-w-none">
                  {isLoading ? "Consulting knowledge base..." : chatResponse || "Awaiting command..."}
                </div>
              </div>
              <div className="flex gap-2">
                <input value={prompt} onChange={(e)=>setPrompt(e.target.value)} onKeyDown={(e)=>e.key==='Enter'&&askAI()} className="flex-1 bg-slate-900 border border-slate-700 p-4 rounded-xl outline-none" placeholder="Ask anything..." />
                <button onClick={askAI} disabled={isLoading} className="px-8 bg-blue-600 rounded-xl font-bold transition-all active:scale-95">SEND</button>
              </div>
            </section>

            {/* RIGHT: EVOLUTION TOOLS */}
            <section className="space-y-8 bg-slate-900/50 p-8 rounded-3xl border border-slate-800">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold text-emerald-400 uppercase tracking-widest">Evolution</h2>
                <button 
                  onClick={fetchKnowledgeList} 
                  className="text-[10px] bg-slate-800 hover:bg-slate-700 px-3 py-1 rounded-full text-slate-300 font-bold border border-slate-700 transition-all"
                >
                  VIEW MEMORY BANK
                </button>
              </div>

              {/* Memory Bank List (Conditionally shown) */}
              {viewingKB && (
                <div className="bg-slate-950 border border-emerald-500/30 p-4 rounded-xl space-y-2">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-[10px] font-bold text-emerald-500">STORED MEMORIES:</span>
                    <button onClick={() => setViewingKB(false)} className="text-[10px] text-slate-500 hover:text-white">HIDE</button>
                  </div>
                  <div className="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto pr-2 custom-scrollbar">
                    {knowledgeFiles.length > 0 ? knowledgeFiles.map(file => (
                      <div key={file} className="text-[10px] font-mono bg-slate-900 p-2 rounded border border-slate-800 text-slate-400 truncate">
                        📄 {file}
                      </div>
                    )) : <p className="text-[10px] text-slate-600">No files found.</p>}
                  </div>
                </div>
              )}
              
              {/* Identity Update */}
              <div className="space-y-3">
                <label className="text-xs font-bold text-slate-500 italic">APPEND TO CORE PERSONA</label>
                <textarea value={identityText} onChange={(e)=>setIdentityText(e.target.value)} className="w-full bg-slate-950 border border-slate-800 p-3 rounded-xl h-24 text-sm focus:border-emerald-500 transition-all outline-none" placeholder="Describe new traits or preferences..." />
                <button onClick={()=>handleEvolution('identity')} disabled={isEvolving || !identityText} className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-sm font-bold transition-all active:scale-[0.98]">APPEND IDENTITY</button>
              </div>

              {/* Document Upload */}
              <div className="space-y-3 pt-4 border-t border-slate-800">
                <label className="text-xs font-bold text-slate-500 italic">ADD NEW KNOWLEDGE FILE</label>
                <input value={docTitle} onChange={(e)=>setDocTitle(e.target.value)} className="w-full bg-slate-950 border border-slate-800 p-3 rounded-xl text-sm outline-none focus:border-blue-500" placeholder="Topic Title (e.g. market_strategy)" />
                <textarea value={docContent} onChange={(e)=>setDocContent(e.target.value)} className="w-full bg-slate-950 border border-slate-800 p-3 rounded-xl h-24 text-sm outline-none focus:border-blue-500" placeholder="Enter content to be indexed..." />
                <button onClick={()=>handleEvolution('knowledge')} disabled={isEvolving || !docContent} className="w-full py-2 bg-slate-800 hover:bg-blue-900/30 hover:text-blue-400 border border-slate-700 rounded-lg text-sm font-bold transition-all active:scale-[0.98]">STORE IN MEMORY</button>
              </div>
            </section>

          </div>
        ) : (
          <div className="text-center py-20 italic text-slate-500">Authenticate via Web3 to access Sovereign Executive.</div>
        )}
      </div>
    </main>
  )
}