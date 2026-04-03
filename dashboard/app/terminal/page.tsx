'use client'

import { useState, useEffect, useRef } from 'react'
import { useAccount, useDisconnect, useWriteContract } from 'wagmi'
import { parseAbi } from 'viem'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { 
  LogOut, ChevronRight, Zap, Cpu, Database, 
  Terminal as TerminalIcon, ShieldCheck, 
  FlaskConical, Binary, HardDrive, Sparkles,
  PanelRightClose, PanelRightOpen, FileText, Clock,
  ShieldAlert, Activity
} from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { toast } from "sonner"

// CONSTANTS & ABI (PRESERVED)
const MARKETPLACE_ABI = parseAbi(['function releasePaymentWithRating(uint256 _jobId, uint256 _rating) public'])
const MARKETPLACE_ADDRESS = "0x86A2EE8FAf9A840F7a2c64CA3d51209F9A02081D"
const PROTOCOL_STAGES = [
  "CONSULTING SOVEREIGN REGISTRY...",
  "ROUTING VIA A2A PROTOCOL...",
  "VERIFYING AGENT POLICY...",
  "STAGING SECURE ESCROW...",
  "EXECUTING REMOTE PROXY..."
];

export default function TwinTerminal() {
  const { address, isConnected } = useAccount()
  const { disconnect } = useDisconnect()
  const { writeContractAsync } = useWriteContract()
  const router = useRouter()
  
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const [prompt, setPrompt] = useState('')
  const [chatResponse, setChatResponse] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [loadingTextIndex, setLoadingTextIndex] = useState(0)
  const [activeJob, setActiveJob] = useState<number | null>(null)
  const [userRating, setUserRating] = useState<number>(5)
  const [identityText, setIdentityText] = useState('')
  const [docTitle, setDocTitle] = useState('')
  const [docContent, setDocContent] = useState('')
  const [isEvolving, setIsEvolving] = useState(false)
  const [knowledgeFiles, setKnowledgeFiles] = useState<string[]>([])
  const [viewingKB, setViewingKB] = useState(false)
  const [lastSync, setLastSync] = useState<string>("NEVER")

  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => { if (!isConnected) router.push('/') }, [isConnected, router])

  // --- THE GEMINI STYLE AUTO-RESIZE (FIXED) ---
  useEffect(() => {
    if (textareaRef.current) {
      // 1. Reset height to 0 to get an accurate scrollHeight
      textareaRef.current.style.height = '0px';
      // 2. Set height based on content
      const nextHeight = textareaRef.current.scrollHeight;
      // 3. Apply height with a 200px cap (Gemini standard)
      textareaRef.current.style.height = `${Math.min(nextHeight, 200)}px`;
    }
  }, [prompt])

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isLoading) {
      interval = setInterval(() => {
        setLoadingTextIndex((prev) => (prev + 1) % PROTOCOL_STAGES.length);
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [isLoading]);

  const askAI = async () => {
    if (!address || !prompt || isLoading) return
    setIsLoading(true); setChatResponse(''); setActiveJob(null);
    try {
      const res = await fetch('http://127.0.0.1:8000/ask', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, wallet_address: address })
      })
      const data = await res.json()
      if (res.ok) {
        setChatResponse(data.answer)
        if (data.job_id) setActiveJob(Number(data.job_id))
        setLastSync(new Date().toLocaleTimeString())
      } else { toast.error(`Protocol Error: ${data.detail}`) }
    } catch { toast.error("Network Offline.") }
    finally { setIsLoading(false); setPrompt('') }
  }

  const handleApprovePayment = async (jobId: number) => {
    try {
      await writeContractAsync({
        address: MARKETPLACE_ADDRESS as `0x${string}`,
        abi: MARKETPLACE_ABI,
        functionName: 'releasePaymentWithRating',
        args: [BigInt(jobId), BigInt(userRating)],
      })
      setActiveJob(null)
      toast.success("Escrow Released")
    } catch { toast.error("Release Failure") }
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
        setIdentityText(''); setDocTitle(''); setDocContent(''); fetchKnowledgeList();
        toast.success(`System Updated`)
        setLastSync(new Date().toLocaleTimeString())
      }
    } finally { setIsEvolving(false) }
  }

  const fetchKnowledgeList = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/list-knowledge')
      const data = await res.json()
      setKnowledgeFiles(data.files); setViewingKB(true)
      setLastSync(new Date().toLocaleTimeString())
    } catch { toast.error("Registry Offline") }
  }

  return (
    <main className="h-screen flex flex-col bg-transparent overflow-hidden text-brand-text">
      {/* --- SURGICAL NAV --- */}
      <nav className="h-14 border-b border-white/5 flex items-center justify-between px-6 bg-brand-bg/40 backdrop-blur-xl z-50 shrink-0">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 bg-brand-accent rounded-full shadow-[0_0_10px_rgba(247,245,242,0.5)]" />
            <h1 className="text-[10px] font-black uppercase tracking-[0.4em] text-brand-accent">Sovereign Terminal</h1>
          </div>
          <Separator orientation="vertical" className="h-4 bg-white/10" />
          <div className="flex gap-6">
            <Link href="/marketplaceUI" className="text-[9px] font-bold text-brand-ash hover:text-brand-accent transition-colors tracking-widest uppercase">Registry</Link>
            <Link href="/hive" className="text-[9px] font-bold text-brand-ash hover:text-brand-accent transition-colors tracking-widest uppercase">Mesh Map</Link>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="text-brand-ash hover:text-brand-accent"
          >
            {isSidebarOpen ? <PanelRightClose size={18} /> : <PanelRightOpen size={18} />}
          </Button>
          <Separator orientation="vertical" className="h-4 bg-white/10" />
          <Button variant="ghost" size="icon" onClick={() => disconnect()} className="h-8 w-8 hover:bg-white/5">
            <LogOut className="w-3.5 h-3.5 text-brand-ash" />
          </Button>
        </div>
      </nav>

      <div className="flex-1 flex overflow-hidden min-h-0">
        {/* --- LEFT: MAIN INTERFACE --- */}
        <section className="flex-1 flex flex-col relative overflow-hidden bg-brand-bg-dark/20 transition-all duration-500 ease-in-out">
          
          {/* IMPORTANT: flex-1 and min-h-0 allows the chat to shrink when input grows upward */}
          <ScrollArea className="flex-1 min-h-0 px-8 py-12 lg:px-24">
            <div className="max-w-4xl mx-auto">
              <AnimatePresence mode='wait'>
                {!chatResponse && !isLoading ? (
                  <div className="h-[50vh] flex flex-col items-center justify-center opacity-10 space-y-4">
                    <TerminalIcon className="w-16 h-16" />
                    <p className="text-[10px] font-black uppercase tracking-[1em]">Awaiting Instruction</p>
                  </div>
                ) : (
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-12 pb-10">
                    {isLoading ? (
                      <div className="flex flex-col items-center justify-center py-20 space-y-6">
                        <FlaskConical className="w-10 h-10 text-brand-accent/50 animate-pulse" />
                        <p className="text-[10px] font-black uppercase tracking-[0.5em] text-brand-accent text-center">{PROTOCOL_STAGES[loadingTextIndex]}</p>
                      </div>
                    ) : (
                      <div className="prose prose-invert prose-emerald max-w-none font-sans leading-relaxed text-brand-text/90">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{chatResponse}</ReactMarkdown>
                      </div>
                    )}
                    {activeJob && (
                      <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="glass-forest p-10 rounded-3xl border border-brand-accent/20 flex flex-col md:flex-row items-center justify-between gap-8">
                        <div className="space-y-4">
                          <span className="text-[10px] font-black text-brand-accent uppercase tracking-widest block">Authorization Required // Release Escrow</span>
                          <div className="flex gap-4">
                            {[1,2,3,4,5].map(num => (
                              <button key={num} onClick={() => setUserRating(num)} className={`text-2xl transition-all ${userRating >= num ? 'scale-125 filter-none' : 'grayscale opacity-20'}`}>⭐</button>
                            ))}
                          </div>
                        </div>
                        <Button onClick={() => handleApprovePayment(activeJob)} className="bg-brand-accent text-brand-bg font-black text-[11px] tracking-widest uppercase px-10 h-14 rounded-2xl">
                          Initialize Release <ShieldCheck className="ml-3 w-5 h-5" />
                        </Button>
                      </motion.div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </ScrollArea>

          {/* --- BOTTOM COMMAND BAR (ANCHORED TO BOTTOM) --- */}
          <div className="p-8 border-t border-white/5 bg-brand-bg-dark/40 shrink-0">
            <div className="max-w-4xl mx-auto">
              <div className="bg-brand-bg-light/20 backdrop-blur-3xl border border-white/10 p-3 rounded-[1.5rem] shadow-2xl focus-within:border-brand-accent/40 transition-all flex items-end gap-3">
                  <textarea 
                    ref={textareaRef}
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), askAI())}
                    placeholder="Input protocol command..."
                    className="flex-1 bg-transparent border-none p-4 text-brand-accent placeholder:text-brand-ash/20 outline-none resize-none text-base font-medium custom-scrollbar"
                    style={{ minHeight: '44px' }}
                  />
                  <Button 
                    onClick={askAI} 
                    disabled={isLoading || !prompt} 
                    size="icon" 
                    className="mb-1 mr-1 h-12 w-12 bg-brand-accent text-brand-bg hover:scale-110 rounded-2xl transition-all shrink-0"
                  >
                    <ChevronRight className="w-6 h-6" />
                  </Button>
              </div>
            </div>
          </div>
        </section>

        {/* --- RIGHT: CONFIGURATION (PRESERVED PLACEHOLDERS) --- */}
        <AnimatePresence>
          {isSidebarOpen && (
            <motion.aside 
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 380, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: "circOut" }}
              className="hidden xl:flex flex-col bg-brand-bg-dark/60 border-l border-white/5 relative overflow-hidden shrink-0"
            >
              <ScrollArea className="h-full">
                <div className="p-8 space-y-10">
                  
                  {/* --- SECTION 1: SYSTEM METADATA --- */}
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 text-brand-ash opacity-50">
                      <Activity size={14} />
                      <span className="text-[10px] font-black uppercase tracking-[0.3em]">System Health</span>
                    </div>
                    <div className="grid grid-cols-2 gap-px bg-white/5 border border-white/5 rounded-xl overflow-hidden font-mono">
                      <div className="bg-brand-bg/40 p-4 space-y-1">
                        <span className="text-[8px] text-brand-ash/60 uppercase block">Files Indexed</span>
                        <div className="flex items-center gap-2">
                           <FileText size={12} className="text-brand-accent" />
                           <span className="text-xs font-bold">{knowledgeFiles.length}</span>
                        </div>
                      </div>
                      <div className="bg-brand-bg/40 p-4 space-y-1">
                        <span className="text-[8px] text-brand-ash/60 uppercase block">Last Handshake</span>
                        <div className="flex items-center gap-2">
                           <Clock size={12} className="text-brand-accent" />
                           <span className="text-[10px] font-bold">{lastSync}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <Separator className="bg-white/5" />

                  {/* --- SECTION 2: IDENTITY --- */}
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 text-brand-ash opacity-50">
                      <Cpu size={14} />
                      <span className="text-[10px] font-black uppercase tracking-[0.3em]">Sovereign Identity</span>
                    </div>
                    <div className="bg-black/40 border border-white/10 rounded-2xl p-5 overflow-hidden group focus-within:border-brand-accent/20 transition-all">
                      <div className="flex items-center justify-between mb-4">
                        <span className="text-[8px] font-mono text-brand-ash/40 uppercase tracking-widest flex items-center gap-2">
                          identity.txt
                        </span>
                        <div className="w-1.5 h-1.5 rounded-full bg-brand-accent/50 animate-pulse" />
                      </div>
                      <textarea 
                        value={identityText} 
                        onChange={(e)=>setIdentityText(e.target.value)} 
                        className="w-full bg-transparent text-[11px] text-brand-text font-mono leading-relaxed outline-none h-32 resize-none mb-4 custom-scrollbar" 
                        placeholder="// Modify identity behavioral instructions..." 
                      />
                      <Button 
                        onClick={()=>handleEvolution('identity')} 
                        disabled={isEvolving || !identityText}
                        className="w-full h-10 text-[9px] font-black bg-brand-accent text-brand-bg uppercase tracking-widest rounded-lg"
                      >
                        Commit Changes <Sparkles size={12} className="ml-2" />
                      </Button>
                    </div>
                  </div>

                  {/* --- SECTION 3: KNOWLEDGE BASE --- */}
                  <div className="space-y-4 pb-10">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 text-brand-ash opacity-50">
                        <Database size={14} />
                        <span className="text-[10px] font-black uppercase tracking-[0.3em]">Knowledge Base</span>
                      </div>
                      <Button variant="ghost" size="sm" onClick={fetchKnowledgeList} className="text-[8px] font-bold text-brand-accent/40 uppercase tracking-tighter">Sync_Local</Button>
                    </div>

                    <div className="grid gap-2 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
                      {knowledgeFiles.length > 0 ? knowledgeFiles.map(file => (
                        <div key={file} className="p-3 bg-white/[0.02] border border-white/5 rounded-xl text-[10px] font-mono text-brand-ash flex items-center gap-3">
                          <Binary className="w-3 h-3 text-brand-accent/30" />
                          <span className="truncate">{file}</span>
                        </div>
                      )) : (
                        <p className="text-[9px] text-brand-ash/20 font-mono text-center py-4 italic border border-white/5 border-dashed rounded-xl">// empty_registry</p>
                      )}
                    </div>

                    <div className="space-y-3 bg-black/40 border border-white/10 rounded-2xl p-4">
                      <div className="space-y-3">
                        <input 
                          value={docTitle} 
                          onChange={(e)=>setDocTitle(e.target.value)} 
                          className="w-full bg-white/5 border border-white/5 rounded-lg h-9 px-3 text-[10px] font-mono text-brand-accent outline-none" 
                          placeholder="NEW_FRAGMENT_TITLE.txt" 
                        />
                        <textarea 
                          value={docContent} 
                          onChange={(e)=>setDocContent(e.target.value)} 
                          className="w-full bg-white/5 border border-white/5 rounded-lg p-3 text-[10px] font-mono text-brand-text h-32 resize-none outline-none custom-scrollbar" 
                          placeholder="// Paste context data payload..." 
                        />
                      </div>
                      <Button 
                        onClick={()=>handleEvolution('knowledge')} 
                        disabled={isEvolving || !docContent}
                        className="w-full h-11 bg-white/5 border border-white/10 text-brand-accent text-[9px] font-black uppercase tracking-widest rounded-xl hover:bg-brand-accent hover:text-brand-bg transition-all"
                      >
                        Index to Documents <HardDrive size={14} className="ml-2" />
                      </Button>
                    </div>
                  </div>
                </div>
              </ScrollArea>
            </motion.aside>
          )}
        </AnimatePresence>
      </div>
    </main>
  )
}