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
const MARKETPLACE_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
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
  
  // NEW: State for the Glass Box Streaming Thoughts
  const [missionLogs, setMissionLogs] = useState<string[]>([])

  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const logEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => { if (!isConnected) router.push('/') }, [isConnected, router])

  // --- THE GEMINI STYLE AUTO-RESIZE (FIXED) ---
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = '0px';
      const nextHeight = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = `${Math.min(nextHeight, 200)}px`;
    }
  }, [prompt])

  // --- AUTO SCROLL FOR MISSION LOGS ---
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [missionLogs])

  // Preserved Loading Animation for Initial Connection
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isLoading && missionLogs.length === 0) {
      interval = setInterval(() => {
        setLoadingTextIndex((prev) => (prev + 1) % PROTOCOL_STAGES.length);
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [isLoading, missionLogs.length]);

  // --- UPGRADED askAI (STREAMING JSON FETCH) ---
  const askAI = async () => {
    if (!address || !prompt || isLoading) return
    
    setIsLoading(true); 
    setChatResponse(''); 
    setActiveJob(null);
    setMissionLogs([]); // Reset the Glass Box for new query
    
    try {
      const res = await fetch('http://127.0.0.1:8000/ask-stream', {
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, wallet_address: address })
      })
      
      if (!res.ok) {
        const errorData = await res.json()
        toast.error(`Protocol Error: ${errorData.detail || 'Unknown'}`)
        setIsLoading(false);
        return;
      }

      // Manual stream parsing logic
      const reader = res.body?.getReader()
      const decoder = new TextDecoder("utf-8")
      
      if (!reader) throw new Error("Stream not supported.")

      let done = false;
      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const dataStr = line.substring(6);
                if (!dataStr.trim()) continue;
                
                const data = JSON.parse(dataStr);
                
                if (data.type === 'thought') {
                  setMissionLogs(prev => [...prev, data.content]);
                } 
                else if (data.type === 'result') {
                  setChatResponse(data.answer);
                  if (data.job_id) setActiveJob(Number(data.job_id));
                  setLastSync(new Date().toLocaleTimeString());
                } 
                else if (data.type === 'error') {
                  toast.error(data.content);
                  setMissionLogs(prev => [...prev, `[CRITICAL_ERROR] ${data.content}`]);
                }
              } catch (e) {
                console.error("Error parsing stream chunk:", e);
              }
            }
          }
        }
      }
    } catch { 
      toast.error("Network Offline.") 
    } finally { 
      setIsLoading(false); 
      setPrompt('') 
    }
  }

  // --- CONTRACT METHODS (PRESERVED) ---
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

  // Helper for color coding the logs
  const getLogColor = (log: string) => {
    if (log.includes('[ERROR]') || log.includes('[WARNING]') || log.includes('[CRITICAL')) return "text-red-400 font-bold";
    if (log.includes('[BLOCKCHAIN]')) return "text-amber-400 font-bold";
    if (log.includes('[SYNTHESIS]') || log.includes('[NETWORK]')) return "text-brand-text font-bold";
    if (log.includes('[PLANNING]') || log.includes('[SYSTEM]')) return "text-cyan-400 font-bold";
    return "text-brand-ash/90";
  }

  return (
    <main className="h-screen flex flex-col bg-transparent overflow-hidden text-brand-text">
      {/* --- SURGICAL NAV --- */}
      <nav className="h-16 border-b border-white/5 flex items-center justify-between px-6 bg-brand-bg/40 backdrop-blur-xl z-50 shrink-0">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-3">
            <div className="w-2.5 h-2.5 bg-brand-accent rounded-full shadow-[0_0_12px_rgba(247,245,242,0.6)]" />
            <h1 className="text-xs font-black uppercase tracking-[0.4em] text-brand-accent">Sovereign Terminal</h1>
          </div>
          <Separator orientation="vertical" className="h-5 bg-white/10" />
          <div className="flex gap-6">
            <Link href="/marketplaceUI" className="text-[10px] font-bold text-brand-ash hover:text-brand-accent transition-colors tracking-widest uppercase">Registry</Link>
            <Link href="/hive" className="text-[10px] font-bold text-brand-ash hover:text-brand-accent transition-colors tracking-widest uppercase">Mesh Map</Link>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="text-brand-ash hover:text-brand-accent"
          >
            {isSidebarOpen ? <PanelRightClose size={20} /> : <PanelRightOpen size={20} />}
          </Button>
          <Separator orientation="vertical" className="h-5 bg-white/10" />
          <Button variant="ghost" size="icon" onClick={() => disconnect()} className="h-10 w-10 hover:bg-white/5">
            <LogOut className="w-4 h-4 text-brand-ash" />
          </Button>
        </div>
      </nav>

      <div className="flex-1 flex overflow-hidden min-h-0">
        {/* --- LEFT: MAIN INTERFACE --- */}
        <section className="flex-1 flex flex-col relative overflow-hidden bg-brand-bg-dark/20 transition-all duration-500 ease-in-out">
          
          <ScrollArea className="flex-1 min-h-0 px-8 py-12 lg:px-24">
            <div className="max-w-4xl mx-auto">
              <AnimatePresence mode='wait'>
                {!chatResponse && !isLoading ? (
                  <div className="h-[50vh] flex flex-col items-center justify-center opacity-20 space-y-4">
                    <TerminalIcon className="w-20 h-20 text-brand-ash" />
                    <p className="text-xs font-black uppercase tracking-[1em] text-brand-ash">Awaiting Instruction</p>
                  </div>
                ) : (
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-12 pb-10">
                    {/* Render standard loading flask ONLY if no stream logs exist yet */}
                    {(isLoading && missionLogs.length === 0) ? (
                      <div className="flex flex-col items-center justify-center py-20 space-y-6">
                        <FlaskConical className="w-12 h-12 text-brand-accent/50 animate-pulse" />
                        <p className="text-xs font-black uppercase tracking-[0.5em] text-brand-accent text-center">{PROTOCOL_STAGES[loadingTextIndex]}</p>
                      </div>
                    ) : (
                      /* Render the final markdown response if available */
                      chatResponse && (
                        <div className="prose prose-invert prose-emerald max-w-none font-sans leading-relaxed text-brand-text text-lg prose-p:my-6 prose-headings:mb-4 whitespace-pre-line">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {chatResponse}
                          </ReactMarkdown>
                        </div>
                      )
                    )}
                    
                    {activeJob && (
                      <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="glass-forest p-10 rounded-3xl border border-brand-accent/20 flex flex-col md:flex-row items-center justify-between gap-8">
                        <div className="space-y-4">
                          <span className="text-xs font-black text-brand-accent uppercase tracking-widest block">Authorization Required // Release Escrow</span>
                          <div className="flex gap-4">
                            {[1,2,3,4,5].map(num => (
                              <button key={num} onClick={() => setUserRating(num)} className={`text-3xl transition-all ${userRating >= num ? 'scale-125 filter-none' : 'grayscale opacity-20'}`}>⭐</button>
                            ))}
                          </div>
                        </div>
                        <Button onClick={() => handleApprovePayment(activeJob)} className="bg-brand-accent text-brand-bg font-black text-xs tracking-widest uppercase px-12 h-16 rounded-2xl hover:scale-105 transition-all">
                          Initialize Release <ShieldCheck className="ml-3 w-5 h-5" />
                        </Button>
                      </motion.div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </ScrollArea>

          {/* --- BOTTOM COMMAND BAR & MISSION LOG --- */}
          <div className="p-8 border-t border-brand-accent/10 bg-brand-bg-dark/40 shrink-0 relative">
            <div className="max-w-4xl mx-auto">
              
              {/* THE GLASS BOX MISSION LOG */}
              <AnimatePresence>
                {(missionLogs.length > 0 && isLoading) && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 10, filter: 'blur(4px)' }}
                    className="mb-6 bg-black/60 border border-brand-accent/20 rounded-2xl overflow-hidden backdrop-blur-xl shadow-2xl"
                  >
                    <div className="bg-brand-accent/10 px-5 py-3 border-b border-brand-accent/20 flex items-center gap-3">
                      <Activity className="w-4 h-4 text-brand-text animate-pulse" />
                      <span className="text-[10px] font-black uppercase tracking-widest text-brand-text">Live Mission Trace</span>
                    </div>
                    <div className="p-6 max-h-56 overflow-y-auto font-mono text-xs leading-relaxed space-y-4 custom-scrollbar">
                      {missionLogs.map((log, idx) => (
                        <motion.div 
                          key={idx} 
                          initial={{ opacity: 0, x: -10 }} 
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.1 }}
                          className={`flex items-start gap-3 ${getLogColor(log)}`}
                        >
                          <span className="opacity-40 shrink-0">{'>'}</span>
                          <span>{log}</span>
                        </motion.div>
                      ))}
                      <div ref={logEndRef} className="h-2" />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* INPUT BAR */}
              <div className="bg-brand-bg-light/20 backdrop-blur-3xl border border-brand-accent/10 p-3 rounded-[1.5rem] shadow-2xl focus-within:border-brand-accent/40 transition-all flex items-end gap-3">
                  <textarea 
                    ref={textareaRef}
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), askAI())}
                    placeholder="Input protocol command..."
                    className="flex-1 bg-transparent border-none p-4 text-brand-text placeholder:text-brand-ash/40 outline-none resize-none text-lg font-medium custom-scrollbar"
                    style={{ minHeight: '50px' }}
                  />
                  <Button 
                    onClick={askAI} 
                    disabled={isLoading || !prompt} 
                    size="icon" 
                    className="mb-1 mr-1 h-14 w-14 bg-brand-accent text-brand-bg hover:scale-110 hover:shadow-[0_0_20px_rgba(247,245,242,0.3)] rounded-2xl transition-all shrink-0 disabled:opacity-50"
                  >
                    <ChevronRight className="w-8 h-8" />
                  </Button>
              </div>
            </div>
          </div>
        </section>

        {/* --- RIGHT: CONFIGURATION --- */}
        <AnimatePresence>
          {isSidebarOpen && (
            <motion.aside 
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 400, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: "circOut" }}
              className="hidden xl:flex flex-col bg-brand-bg-dark/80 border-l border-brand-accent/10 relative overflow-hidden shrink-0 shadow-[-20px_0_40px_rgba(0,0,0,0.3)]"
            >
              <ScrollArea className="h-full">
                <div className="p-8 space-y-12">
                  
                  {/* --- SECTION 1: SYSTEM METADATA --- */}
                  <div className="space-y-5">
                    <div className="flex items-center gap-3 text-brand-ash opacity-60">
                      <Activity size={16} />
                      <span className="text-xs font-black uppercase tracking-[0.3em]">System Health</span>
                    </div>
                    <div className="grid grid-cols-2 gap-px bg-brand-accent/10 border border-brand-accent/10 rounded-2xl overflow-hidden font-mono">
                      <div className="bg-brand-bg/60 p-5 space-y-2">
                        <span className="text-[10px] text-brand-ash/80 uppercase block font-bold tracking-widest">Files Indexed</span>
                        <div className="flex items-center gap-2">
                           <FileText size={16} className="text-brand-accent" />
                           <span className="text-sm font-bold text-brand-accent">{knowledgeFiles.length}</span>
                        </div>
                      </div>
                      <div className="bg-brand-bg/60 p-5 space-y-2">
                        <span className="text-[10px] text-brand-ash/80 uppercase block font-bold tracking-widest">Last Handshake</span>
                        <div className="flex items-center gap-2">
                           <Clock size={16} className="text-brand-accent" />
                           <span className="text-xs font-bold text-brand-accent">{lastSync}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <Separator className="bg-brand-accent/10" />

                  {/* --- SECTION 2: IDENTITY --- */}
                  <div className="space-y-5">
                    <div className="flex items-center gap-3 text-brand-ash opacity-60">
                      <Cpu size={16} />
                      <span className="text-xs font-black uppercase tracking-[0.3em]">Sovereign Identity</span>
                    </div>
                    <div className="bg-black/60 border border-brand-accent/10 rounded-2xl p-6 overflow-hidden group focus-within:border-brand-accent/30 transition-all">
                      <div className="flex items-center justify-between mb-5">
                        <span className="text-[10px] font-mono text-brand-ash/60 uppercase tracking-widest flex items-center gap-2">
                          identity.txt
                        </span>
                        <div className="w-2 h-2 rounded-full bg-brand-accent/60 animate-pulse shadow-[0_0_8px_rgba(247,245,242,0.4)]" />
                      </div>
                      <textarea 
                        value={identityText} 
                        onChange={(e)=>setIdentityText(e.target.value)} 
                        className="w-full bg-transparent text-xs text-brand-text font-mono leading-relaxed outline-none h-36 resize-none mb-5 custom-scrollbar" 
                        placeholder="// Modify identity behavioral instructions..." 
                      />
                      <Button 
                        onClick={()=>handleEvolution('identity')} 
                        disabled={isEvolving || !identityText}
                        className="w-full h-12 text-[10px] font-black bg-brand-accent text-brand-bg uppercase tracking-widest rounded-xl hover:shadow-[0_0_20px_rgba(247,245,242,0.2)] transition-all"
                      >
                        Commit Changes <Sparkles size={14} className="ml-2" />
                      </Button>
                    </div>
                  </div>

                  <Separator className="bg-brand-accent/10" />

                  {/* --- SECTION 3: KNOWLEDGE BASE --- */}
                  <div className="space-y-5 pb-10">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 text-brand-ash opacity-60">
                        <Database size={16} />
                        <span className="text-xs font-black uppercase tracking-[0.3em]">Knowledge Base</span>
                      </div>
                      <Button variant="ghost" size="sm" onClick={fetchKnowledgeList} className="text-[10px] font-bold text-brand-accent/50 hover:text-brand-accent uppercase tracking-tighter">Sync_Local</Button>
                    </div>

                    <div className="grid gap-2 max-h-56 overflow-y-auto pr-2 custom-scrollbar">
                      {knowledgeFiles.length > 0 ? knowledgeFiles.map(file => (
                        <div key={file} className="p-4 bg-white/[0.03] border border-white/10 rounded-xl text-xs font-mono text-brand-ash flex items-center gap-4 hover:bg-brand-accent/5 transition-colors">
                          <Binary className="w-4 h-4 text-brand-accent/40" />
                          <span className="truncate">{file}</span>
                        </div>
                      )) : (
                        <p className="text-[10px] text-brand-ash/30 font-mono text-center py-5 border border-white/5 border-dashed rounded-xl tracking-widest">// empty_registry</p>
                      )}
                    </div>

                    <div className="space-y-4 bg-black/60 border border-brand-accent/10 rounded-2xl p-5">
                      <div className="space-y-4">
                        <input 
                          value={docTitle} 
                          onChange={(e)=>setDocTitle(e.target.value)} 
                          className="w-full bg-white/5 border border-white/10 rounded-xl h-11 px-4 text-xs font-mono text-brand-text placeholder:text-brand-ash/30 outline-none focus:border-brand-accent/30 transition-colors" 
                          placeholder="NEW_FRAGMENT_TITLE.txt" 
                        />
                        <textarea 
                          value={docContent} 
                          onChange={(e)=>setDocContent(e.target.value)} 
                          className="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-xs font-mono text-brand-text h-36 resize-none outline-none custom-scrollbar focus:border-brand-accent/30 transition-colors placeholder:text-brand-ash/30" 
                          placeholder="// Paste context data payload..." 
                        />
                      </div>
                      <Button 
                        onClick={()=>handleEvolution('knowledge')} 
                        disabled={isEvolving || !docContent}
                        className="w-full h-12 bg-white/5 border border-white/10 text-brand-accent text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-brand-accent hover:text-brand-bg transition-all"
                      >
                        Index to Documents <HardDrive size={16} className="ml-2" />
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