'use client'

import { useState, useEffect } from 'react'
import { useAccount, useConnect, useDisconnect, useWriteContract } from 'wagmi'
import { injected } from 'wagmi/connectors'
import { parseAbi } from 'viem'
import Link from 'next/link';

// Phase 4 Constants
const MARKETPLACE_ABI = parseAbi(['function releasePayment(uint256 _jobId) public'])
const MARKETPLACE_ADDRESS = "0xa513E6E4b8f2a923D98304ec87F64353C4D5C853"

export default function Dashboard() {
  const { address, isConnected } = useAccount()
  const { connect } = useConnect()
  const { disconnect } = useDisconnect()
  const { writeContractAsync } = useWriteContract()
  
  const [prompt, setPrompt] = useState('')
  const [chatResponse, setChatResponse] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [mounted, setMounted] = useState(false)
  
  // Phase 4 State
  const [activeJob, setActiveJob] = useState<number | null>(null)

  // Evolution States
  const [identityText, setIdentityText] = useState('')
  const [docTitle, setDocTitle] = useState('')
  const [docContent, setDocContent] = useState('')
  const [isEvolving, setIsEvolving] = useState(false)
  const [knowledgeFiles, setKnowledgeFiles] = useState<string[]>([])
  const [viewingKB, setViewingKB] = useState(false)

  useEffect(() => { setMounted(true) }, [])

  // --- UNIFIED ASK LOGIC ---
  const askAI = async () => {
    if (!address || !prompt || isLoading) return
    setIsLoading(true); 
    setChatResponse('');
    setActiveJob(null); // Clear previous jobs

    try {
      const res = await fetch('http://127.0.0.1:8000/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, wallet_address: address })
      })
      const data = await res.json()
      
      if (res.ok) {
        setChatResponse(data.answer)
        // CHECK FOR PENDING PAYMENT
        if (data.job_id) {
          console.log("💰 Escrow Job Detected:", data.job_id)
          setActiveJob(Number(data.job_id))
        }
      } else {
        setChatResponse(`Error: ${data.detail}`)
      }
    } catch { 
      setChatResponse("Server offline.") 
    } finally { 
      setIsLoading(false); 
      setPrompt('') 
    }
  }

  // --- PHASE 4 RELEASE LOGIC ---
  const handleApprovePayment = async (jobId: number) => {
    try {
      await writeContractAsync({
        address: MARKETPLACE_ADDRESS as `0x${string}`,
        abi: MARKETPLACE_ABI,
        functionName: 'releasePayment',
        args: [BigInt(jobId)],
      })
      alert(`✅ Payment for Job #${jobId} released!`)
      setActiveJob(null)
    } catch (err) {
      console.error("Release failed", err)
      alert("Transaction failed. Check MetaMask Nonce/Reset.")
    }
  }

  const handleEvolution = async (type: 'identity' | 'knowledge') => {
    setIsEvolving(true)
    const endpoint = type === 'identity' ? '/update-identity' : '/add-knowledge'
    const payload = type === 'identity' 
      ? { content: identityText, wallet_address: address }
      : { filename: docTitle, content: docContent, wallet_address: address }

    try {
      const res = await fetch(`http://127.0.0.1:8000${endpoint}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (res.ok) {
        alert("Evolution Successful!");
        setIdentityText(''); setDocTitle(''); setDocContent('');
        fetchKnowledgeList(); 
      }
    } catch { alert("Evolution failed.") }
    finally { setIsEvolving(false) }
  }

  const fetchKnowledgeList = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/list-knowledge')
      const data = await res.json()
      setKnowledgeFiles(data.files); setViewingKB(true)
    } catch { alert("Could not fetch knowledge base list.") }
  }

  if (!mounted) return null

  return (
    <main className="min-h-screen p-8 bg-slate-950 text-slate-100 font-sans">
      <div className="max-w-4xl mx-auto space-y-12">
        
        {/* HEADER */}
        <header className="flex justify-between items-center border-b border-slate-800 pb-8">
          <div className="flex items-center gap-8">
            <h1 className="text-3xl font-black bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
              AISAAS 2.0
            </h1>
            <nav className="hidden md:flex gap-4">
              <Link href="/" className="text-sm font-bold text-white">Twin Terminal</Link>
              <Link href="/marketplaceUI" className="text-sm font-bold text-slate-500 hover:text-emerald-400">Marketplace</Link>
            </nav>
          </div>

          {!isConnected ? (
            <button onClick={() => connect({ connector: injected() })} className="px-6 py-2 bg-blue-600 rounded-full font-bold">Connect Wallet</button>
          ) : (
            <div className="flex items-center gap-4 bg-slate-900 p-2 px-4 rounded-full border border-slate-800 text-xs text-slate-400">
              {address?.slice(0,6)}...{address?.slice(-4)}
              <button onClick={() => disconnect()} className="text-red-400 font-bold ml-2">EXIT</button>
            </div>
          )}
        </header>

        {isConnected ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            
            {/* LEFT: UNIFIED TERMINAL */}
            <section className="space-y-6">
              <h2 className="text-xl font-bold text-blue-400 uppercase tracking-widest">Digital Twin Terminal</h2>
              
              {/* Added 'overflow-hidden' to the main container */}
              <div className={`relative p-6 rounded-2xl border min-h-[300px] flex flex-col justify-between overflow-hidden ${isLoading ? 'bg-slate-900 border-blue-500/50' : 'bg-slate-900 border-slate-800'}`}>
                
                {/* Added 'break-all' and 'whitespace-pre-wrap' to handle long hashes */}
                <div className="prose prose-invert max-w-none text-sm text-slate-300 break-all whitespace-pre-wrap leading-relaxed">
                  {isLoading ? (
                    <span className="animate-pulse italic">Consulting knowledge base & executing routing protocol...</span>
                  ) : (
                    chatResponse || "Awaiting command..."
                  )}
                </div>

                {/* PHASE 4: IN-CHAT APPROVAL BUTTON */}
                {activeJob && (
                  <div className="mt-6 p-4 bg-emerald-500/10 border border-emerald-500/40 rounded-xl flex items-center justify-between gap-4 animate-in fade-in slide-in-from-bottom-2">
                    <div className="min-w-0"> {/* 'min-w-0' prevents the text from pushing the button out */}
                        <p className="text-[10px] font-black text-emerald-400 uppercase tracking-widest">Payment Pending</p>
                        <p className="text-xs text-white">Release payment for Job #{activeJob}?</p>
                    </div>
                    <button 
                        onClick={() => handleApprovePayment(activeJob)}
                        className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-[10px] font-black py-2 px-4 rounded-lg transition-all active:scale-95 shrink-0"
                    >
                        APPROVE & PAY
                    </button>
                  </div>
                )}
              </div>

              <div className="flex gap-2">
                <input 
                  value={prompt} 
                  onChange={(e)=>setPrompt(e.target.value)} 
                  onKeyDown={(e)=>e.key==='Enter'&&askAI()} 
                  className="flex-1 bg-slate-900 border border-slate-700 p-4 rounded-xl outline-none focus:border-blue-500 transition-colors" 
                  placeholder="Ask anything..." 
                />
                <button onClick={askAI} disabled={isLoading} className="px-8 bg-blue-600 rounded-xl font-bold transition-all hover:bg-blue-500 active:scale-95 disabled:bg-slate-800">
                  {isLoading ? "..." : "SEND"}
                </button>
              </div>
            </section>

            {/* RIGHT: EVOLUTION TOOLS */}
            <section className="space-y-8 bg-slate-900/50 p-8 rounded-3xl border border-slate-800">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold text-emerald-400 uppercase tracking-widest">Evolution</h2>
                <button onClick={fetchKnowledgeList} className="text-[10px] bg-slate-800 px-3 py-1 rounded-full text-slate-300 font-bold border border-slate-700">MEMORIES</button>
              </div>

              {viewingKB && (
                <div className="bg-slate-950 border border-emerald-500/30 p-4 rounded-xl space-y-2">
                    {knowledgeFiles.map(file => <div key={file} className="text-[10px] font-mono text-slate-400">📄 {file}</div>)}
                    <button onClick={() => setViewingKB(false)} className="text-[10px] text-slate-600 block pt-2">CLOSE</button>
                </div>
              )}
              
              <div className="space-y-3">
                <textarea value={identityText} onChange={(e)=>setIdentityText(e.target.value)} className="w-full bg-slate-950 border border-slate-800 p-3 rounded-xl h-24 text-sm outline-none" placeholder="New traits..." />
                <button onClick={()=>handleEvolution('identity')} disabled={isEvolving || !identityText} className="w-full py-2 bg-emerald-600 rounded-lg text-sm font-bold">APPEND IDENTITY</button>
              </div>

              <div className="space-y-3 pt-4 border-t border-slate-800">
                <input value={docTitle} onChange={(e)=>setDocTitle(e.target.value)} className="w-full bg-slate-950 border border-slate-800 p-3 rounded-xl text-sm outline-none" placeholder="Title" />
                <textarea value={docContent} onChange={(e)=>setDocContent(e.target.value)} className="w-full bg-slate-950 border border-slate-800 p-3 rounded-xl h-24 text-sm outline-none" placeholder="Content..." />
                <button onClick={()=>handleEvolution('knowledge')} disabled={isEvolving || !docContent} className="w-full py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm font-bold">STORE MEMORY</button>
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