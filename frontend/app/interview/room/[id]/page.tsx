'use client';
import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useInterviewStore } from '@/lib/stores/interviewStore';
import { useAuthStore } from '@/lib/stores/authStore';
import api from '@/src/lib/api';
import Editor from '@monaco-editor/react';
import {
    Send, Mic, MicOff, Video, VideoOff, Code2, MessageSquare,
    Lightbulb, X, Phone, Bot, Play, RotateCcw, Terminal,
    Cpu, Clock, Activity, ShieldAlert, Power, CheckCircle, XCircle, Loader2,
    ArrowRight, Trash2
} from 'lucide-react';
import toast, { Toaster } from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import './interview-room.css';
interface WhiteboardEntry {
    userText: string;
    aiResponse: string;
    format: 'text' | 'code';
    timestamp: string;
}
export default function InterviewRoomPage() {
    const params = useParams();
    const router = useRouter();
    const sessionId = params.id as string;
    const { accessToken, user } = useAuthStore();
    const {
        status,
        messages,
        coachingHints,
        connect,
        disconnect,
        sendMessage,
        sendAudio,
        sendCode,
        endSession,
        codeResult,
        currentPhase,
    } = useInterviewStore();
    const [inputMessage, setInputMessage] = useState('');
    const [isRecording, setIsRecording] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [lastAIMessage, setLastAIMessage] = useState('');
    const [code, setCode] = useState('# Write your solution here\n\n');
    const [language, setLanguage] = useState('python');
    const [timeElapsed, setTimeElapsed] = useState(0);
    const [codeStatus, setCodeStatus] = useState<'idle' | 'running' | 'success' | 'error'>('idle');
    const [micEnabled, setMicEnabled] = useState(true);
    const [videoEnabled, setVideoEnabled] = useState(true);
    const [showCode, setShowCode] = useState(false);
    const [showChat, setShowChat] = useState(false);
    const [unreadMessageCount, setUnreadMessageCount] = useState(0);
    const viewMode = showCode && showChat ? 'codeChat'
        : showCode ? 'code'
            : showChat ? 'chat'
                : 'default';
    const [showHintPanel, setShowHintPanel] = useState(false);
    const [activeWorkspaceTab, setActiveWorkspaceTab] = useState<'code' | 'whiteboard'>('code');
    const [isEndingSession, setIsEndingSession] = useState(false);
    const [micVolume, setMicVolume] = useState<number[]>([0, 0, 0, 0, 0]);
    const [wbInput, setWbInput] = useState('');
    const [wbMode, setWbMode] = useState<'explain' | 'code' | 'hints' | 'solution'>('explain');
    const [wbEntries, setWbEntries] = useState<WhiteboardEntry[]>([]);
    const [wbLoading, setWbLoading] = useState(false);
    const [isScreenSharing, setIsScreenSharing] = useState(false);
    const screenStreamRef = useRef<MediaStream | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);
    const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
    const videoRef = useRef<HTMLVideoElement>(null);
    const codeTimeoutRef = useRef<NodeJS.Timeout>();
    const analyserRef = useRef<AnalyserNode | null>(null);
    const micAnimFrameRef = useRef<number>(0);
    const endTimeoutRef = useRef<NodeJS.Timeout>();
    const wbResponseEndRef = useRef<HTMLDivElement>(null);
    const lastProcessedMessageRef = useRef<number>(0);
    const languages = [
        { id: 'python', label: 'Python' },
        { id: 'javascript', label: 'JavaScript' },
        { id: 'typescript', label: 'TypeScript' },
        { id: 'java', label: 'Java' },
        { id: 'cpp', label: 'C++' },
    ];
    useEffect(() => {
        if (sessionId && accessToken) {
            const wsUrl = api.getWebSocketUrl(sessionId) + `?token=${accessToken}`;
            connect(sessionId, wsUrl);
        }
        return () => {
            disconnect();
            if (endTimeoutRef.current) clearTimeout(endTimeoutRef.current);
        };
    }, [sessionId, accessToken, connect]);
    useEffect(() => {
        const handleUnload = () => {
            const ws = useInterviewStore.getState().websocket;
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'end_session', data: {} }));
            }
        };
        window.addEventListener('beforeunload', handleUnload);
        return () => window.removeEventListener('beforeunload', handleUnload);
    }, []);
    useEffect(() => {
        if (messages.length > 0 && messages.length > lastProcessedMessageRef.current) {
            const lastMsg = messages[messages.length - 1];
            lastProcessedMessageRef.current = messages.length;
            if (lastMsg.role === 'interviewer') {
                setLastAIMessage(lastMsg.content);
                setIsSpeaking(true);
                setTimeout(() => setIsSpeaking(false), 4500);
                if (!showChat) {
                    setUnreadMessageCount(prev => prev + 1);
                }
                if (lastMsg.audioUrl && audioPlayerRef.current) {
                    audioPlayerRef.current.src = lastMsg.audioUrl;
                    audioPlayerRef.current
                        .play()
                        .catch(() => {
                        });
                }
            }
        }
    }, [messages, showChat]);
    useEffect(() => {
        if (showChat) {
            setUnreadMessageCount(0);
        }
    }, [showChat]);
    useEffect(() => {
        if (status !== 'active') return;
        const interval = setInterval(() => setTimeElapsed(prev => prev + 1), 1000);
        return () => clearInterval(interval);
    }, [status]);
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, showChat]);
    const setupVideoPlayback = () => {
        if (videoRef.current) {
            if (isScreenSharing && screenStreamRef.current) {
                videoRef.current.srcObject = screenStreamRef.current;
            } else if (videoEnabled) {
                navigator.mediaDevices.getUserMedia({ video: true })
                    .then(s => {
                        (videoRef.current as any).webcamStream = s;
                        videoRef.current!.srcObject = s;
                    })
                    .catch(() => {
                        toast.error('Camera access denied');
                        setVideoEnabled(false);
                    });
            } else {
                const oldStream = (videoRef.current as any).webcamStream;
                if (oldStream) {
                    oldStream.getTracks().forEach((t: MediaStreamTrack) => t.stop());
                }
                videoRef.current.srcObject = null;
            }
        }
    };
    useEffect(() => {
        setupVideoPlayback();
        return () => {
            const oldStream = (videoRef.current as any)?.webcamStream;
            if (oldStream) oldStream.getTracks().forEach((t: MediaStreamTrack) => t.stop());
        };
    }, [videoEnabled, isScreenSharing]);
    const toggleScreenShare = async () => {
        if (isScreenSharing) {
            if (screenStreamRef.current) {
                screenStreamRef.current.getTracks().forEach(t => t.stop());
                screenStreamRef.current = null;
            }
            setIsScreenSharing(false);
        } else {
            try {
                const stream = await navigator.mediaDevices.getDisplayMedia({ video: true });
                stream.getVideoTracks()[0].onended = () => {
                    screenStreamRef.current = null;
                    setIsScreenSharing(false);
                };
                screenStreamRef.current = stream;
                setIsScreenSharing(true);
            } catch (err: any) {
                if (err.name !== 'NotAllowedError') { 
                    toast.error('Failed to start screen sharing.');
                }
            }
        }
    };
    useEffect(() => {
        if (codeResult) {
            const isError = codeResult.toLowerCase().includes('error') ||
                codeResult.toLowerCase().includes('traceback') ||
                codeResult.toLowerCase().includes('exception') ||
                codeResult.toLowerCase().includes('syntaxerror') ||
                codeResult.toLowerCase().includes('referenceerror');
            setCodeStatus(isError ? 'error' : 'success');
        }
    }, [codeResult]);
    const startMicAnalyser = useCallback((stream: MediaStream) => {
        try {
            const audioCtx = new AudioContext();
            const source = audioCtx.createMediaStreamSource(stream);
            const analyser = audioCtx.createAnalyser();
            analyser.fftSize = 64;
            source.connect(analyser);
            analyserRef.current = analyser;
            const data = new Uint8Array(analyser.frequencyBinCount);
            const tick = () => {
                analyser.getByteFrequencyData(data);
                const bars = Array.from({ length: 5 }, (_, i) => {
                    const idx = Math.floor((i / 5) * data.length);
                    return Math.round((data[idx] / 255) * 100);
                });
                setMicVolume(bars);
                micAnimFrameRef.current = requestAnimationFrame(tick);
            };
            micAnimFrameRef.current = requestAnimationFrame(tick);
        } catch {
        }
    }, []);
    const stopMicAnalyser = useCallback(() => {
        if (micAnimFrameRef.current) cancelAnimationFrame(micAnimFrameRef.current);
        analyserRef.current = null;
        setMicVolume([0, 0, 0, 0, 0]);
    }, []);
    const handleSendMessage = () => {
        if (inputMessage.trim()) {
            sendMessage(inputMessage);
            setInputMessage('');
        }
    };
    
    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                ? 'audio/webm;codecs=opus'
                : MediaRecorder.isTypeSupported('audio/webm')
                    ? 'audio/webm'
                    : '';
            const options = mimeType ? { mimeType } : {};
            const mediaRecorder = new MediaRecorder(stream, options);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];
            
            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) audioChunksRef.current.push(e.data);
            };
            mediaRecorder.onstop = () => {
                const blobType = mimeType || 'audio/webm';
                const audioBlob = new Blob(audioChunksRef.current, { type: blobType });
                stream.getTracks().forEach(track => track.stop());
                stopMicAnalyser();
                if (audioBlob.size < 2000) {
                    toast.error('Audio too short — please hold the mic button and speak clearly');
                    return;
                }
                const reader = new FileReader();
                reader.onloadend = () => {
                    const base64data = (reader.result as string).split(',')[1];
                    sendAudio(base64data);
                    toast.loading('🎙️ Processing your response…', { id: 'stt-toast', duration: 10000 });
                };
                reader.readAsDataURL(audioBlob);
            };
            mediaRecorder.start();
            setIsRecording(true);
            startMicAnalyser(stream);
            toast('🎙️ Listening… press mic again to stop', { duration: 2000 });
        } catch (err: any) {
            if (err?.name === 'NotAllowedError' || err?.name === 'PermissionDeniedError') {
                toast.error(
                    '🎤 Microphone access is required. Please allow access in browser settings.',
                    { duration: 6000 }
                );
            } else {
                toast.error('Could not start recording — please check your microphone');
            }
        }
    };
    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            if (mediaRecorderRef.current.state === 'recording') {
                mediaRecorderRef.current.requestData();
            }
            mediaRecorderRef.current.stop();
            setIsRecording(false);
        }
    };
    const toggleRecording = () => isRecording ? stopRecording() : startRecording();
    const handleCodeChange = (value: string | undefined) => {
        if (value !== undefined) {
            setCode(value);
            if (codeTimeoutRef.current) clearTimeout(codeTimeoutRef.current);
            codeTimeoutRef.current = setTimeout(() => sendCode(value, language), 1500);
        }
    };
    const handleRunCode = () => {
        setCodeStatus('running');
        sendCode(code, language);
        useInterviewStore.setState({ codeResult: '' });
    };
    
    const handleEndInterview = async () => {
        if (isEndingSession) return;
        setIsEndingSession(true);
        const loadingToastId = toast.loading('Ending session and generating analysis…');
        try {
            endSession();
            
            endTimeoutRef.current = setTimeout(() => {
                toast.dismiss(loadingToastId);
                toast.error('Analysis is taking longer than expected. Redirecting anyway…', { duration: 4000 });
                router.push(`/interview/report/${sessionId}`);
            }, 30000);
            
            const checkInterval = setInterval(() => {
                const currentStatus = useInterviewStore.getState().status;
                if (currentStatus === 'completed') {
                    clearInterval(checkInterval);
                    if (endTimeoutRef.current) clearTimeout(endTimeoutRef.current);
                    toast.dismiss(loadingToastId);
                    toast.success('Session ended! Generating your report…');
                    setTimeout(() => {
                        router.push(`/interview/report/${sessionId}`);
                    }, 1500);
                }
            }, 1000);
            setTimeout(() => {
                const currentStatus = useInterviewStore.getState().status;
                if (currentStatus === 'completed') {
                    clearInterval(checkInterval);
                    if (endTimeoutRef.current) clearTimeout(endTimeoutRef.current);
                    toast.dismiss(loadingToastId);
                    router.push(`/interview/report/${sessionId}`);
                }
            }, 3000);
        } catch (err) {
            toast.dismiss(loadingToastId);
            toast.error('Failed to end session. Please try again.');
            setIsEndingSession(false);
        }
    };
    const handleWhiteboardSubmit = async () => {
        if (!wbInput.trim() || wbLoading) return;
        setWbLoading(true);
        const userContent = wbInput.trim();
        setWbInput('');
        try {
            const speechUrl = api.getServiceUrl('speech');
            const res = await fetch(`${window.location.origin}${speechUrl}/whiteboard/ask`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${accessToken}` },
                body: JSON.stringify({ content: userContent, mode: wbMode, session_id: sessionId }),
            });
            if (!res.ok) throw new Error(`Server returned ${res.status}`);
            const data = await res.json();
            const ts = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            setWbEntries(prev => [...prev, {
                userText: userContent,
                aiResponse: data.response || '',
                format: data.format || 'text',
                timestamp: ts,
            }]);
        } catch (err: any) {
            toast.error('Whiteboard AI unavailable — please try again');
            setWbInput(userContent);
        } finally {
            setWbLoading(false);
        }
    };
    const formatTime = (s: number) => {
        const m = Math.floor(s / 60);
        const sec = s % 60;
        return `${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`;
    };
    const getUserInitials = () => {
        if (user?.full_name) {
            return user.full_name.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase();
        }
        return 'Y';
    };
    if (status === 'idle' || status === 'connecting') {
        return (
            <div className="hud-root" style={{ justifyContent: 'center', alignItems: 'center' }}>
                <div className="hud-bg"><div className="hud-grid" /><div className="hud-aurora" /></div>
                <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    style={{ textAlign: 'center', zIndex: 10 }}
                >
                    <Cpu style={{ width: 64, height: 64, color: '#00d4ff', marginBottom: 20, animation: 'core-pulse 2s infinite' }} />
                    <h2 style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: 2, marginBottom: 8 }}>INITIALIZING NEURAL LINK</h2>
                    <p style={{ color: '#00d4ff', letterSpacing: 4, textTransform: 'uppercase', fontSize: '0.8rem' }}>Connecting to AI Interviewer...</p>
                </motion.div>
            </div>
        );
    }
    return (
        <div className="hud-root">
            <Toaster position="top-center" toastOptions={{
                style: { background: '#0f172a', color: '#fff', border: '1px solid rgba(0, 212, 255, 0.2)' }
            }} />
            <audio ref={audioPlayerRef} className="hidden" />
            {}
            <div className="hud-bg">
                <div className="hud-grid" />
                <div className="hud-aurora" />
            </div>
            {}
            <header className="hud-topbar">
                <div className="hud-brand">
                    <Activity className="hud-brand-icon" />
                    <span className="hud-brand-text">SynthHire</span>
                </div>
                <div className="hud-timer">
                    {formatTime(timeElapsed)}
                </div>
                <div className="hud-status-badge">
                    <div className="hud-status-dot" />
                    {status === 'active' ? 'SYSTEM ONLINE' : 'DISCONNECTED'}
                </div>
            </header>
            {}
            <div className="hud-layout-engine" style={{ display: 'flex', flexDirection: 'row', flex: 1, minHeight: 0, overflow: 'hidden', position: 'relative' }}>
                {}
                {viewMode !== 'codeChat' && (
                    <div style={{
                        display: 'flex',
                        flexDirection: viewMode === 'default' ? 'row' : 'column',
                        flex: '1',
                        gap: '16px',
                        minHeight: 0,
                        overflow: 'hidden',
                    }}>
                        {}
                        <div className="hud-ai-section" style={{
                            display: 'flex',
                            flex: viewMode === 'default' ? '1' : '1',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            position: 'relative',
                            overflow: 'hidden',
                        }}>
                            <div className={`hud-core-wrapper ${viewMode !== 'default' ? 'compact' : ''}`}>
                                <div className="hud-core-ring-1" />
                                <div className="hud-core-ring-2" />
                                <div className="hud-core-ring-3" />
                                <div className={`hud-core-center ${isSpeaking ? 'speaking' : ''}`}>
                                    <Bot className="hud-core-icon" />
                                    <div className="hud-core-eq">
                                        <div className="hud-eq-bar" style={{ height: '12px', animationDelay: '0s' }} />
                                        <div className="hud-eq-bar" style={{ height: '24px', animationDelay: '0.1s' }} />
                                        <div className="hud-eq-bar" style={{ height: '16px', animationDelay: '0.2s' }} />
                                        <div className="hud-eq-bar" style={{ height: '28px', animationDelay: '0.3s' }} />
                                        <div className="hud-eq-bar" style={{ height: '14px', animationDelay: '0.4s' }} />
                                    </div>
                                </div>
                                <div className="hud-core-label">
                                    <div className="hud-core-title">Nexus AI Processor</div>
                                    <div className="hud-core-subtitle">{isSpeaking ? 'TRANSMITTING' : 'LISTENING'}</div>
                                </div>
                            </div>
                        </div>
                        {}
                        <div className="hud-candidate-section" style={{
                            display: 'flex',
                            flex: viewMode === 'default' ? '1' : '1',
                            flexDirection: 'column',
                            position: 'relative',
                            overflow: 'hidden',
                        }}>
                            <div className="hud-candidate-video-wrapper">
                                {videoEnabled || isScreenSharing ? (
                                    <video ref={videoRef} autoPlay muted playsInline className="hud-candidate-video" />
                                ) : (
                                    <div className="hud-candidate-avatar">{getUserInitials()}</div>
                                )}
                                <div className="hud-candidate-overlay">
                                    <span className="hud-candidate-name">{user?.full_name || 'Candidate'} {isScreenSharing && "(Presenting)"}</span>
                                    {isRecording && (
                                        <span className="hud-candidate-rec">
                                            <span className="hud-rec-dot" />
                                            REC
                                        </span>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div> 
                )}
                {}
                {(viewMode === 'code' || viewMode === 'codeChat') && (
                    <div className="hud-code-canvas" style={{
                        display: 'flex',
                        flexDirection: 'column',
                        flex: viewMode === 'codeChat' ? '3' : '1',
                        minWidth: 0,
                        overflow: 'hidden',
                    }}>
                        <header className="hud-code-header">
                            <div className="hud-workspace-tabs">
                                <button
                                    className={`hud-code-tab ${activeWorkspaceTab === 'code' ? 'active' : ''}`}
                                    onClick={() => setActiveWorkspaceTab('code')}
                                >Code Editor</button>
                                <button
                                    className={`hud-code-tab ${activeWorkspaceTab === 'whiteboard' ? 'active' : ''}`}
                                    onClick={() => setActiveWorkspaceTab('whiteboard')}
                                >Whiteboard</button>
                            </div>
                            {activeWorkspaceTab === 'code' && (
                                <div className="hud-code-tabs">
                                    {languages.map(lang => (
                                        <button
                                            key={lang.id}
                                            className={`hud-code-tab ${language === lang.id ? 'active' : ''}`}
                                            onClick={() => setLanguage(lang.id)}
                                        >
                                            {lang.label}
                                        </button>
                                    ))}
                                </div>
                            )}
                            {activeWorkspaceTab === 'whiteboard' && (
                                <div className="hud-wb-mode-toggle">
                                    {(['explain', 'code', 'hints', 'solution'] as const).map(m => (
                                        <button
                                            key={m}
                                            className={`hud-wb-mode-btn ${wbMode === m ? 'active' : ''}`}
                                            onClick={() => setWbMode(m)}
                                        >
                                            {m.charAt(0).toUpperCase() + m.slice(1)}
                                        </button>
                                    ))}
                                </div>
                            )}
                            <div className="hud-code-actions">
                                {activeWorkspaceTab === 'code' && (
                                    <>
                                        <button className="hud-btn" onClick={() => setCode('# Write your solution here\n\n')}>
                                            <RotateCcw style={{ width: 14, height: 14 }} /> Reset
                                        </button>
                                        <button className="hud-btn primary" onClick={handleRunCode}>
                                            {codeStatus === 'running' ? (
                                                <Loader2 style={{ width: 14, height: 14, animation: 'spin-slow 1s linear infinite' }} />
                                            ) : (
                                                <Play style={{ width: 14, height: 14, fill: 'currentColor' }} />
                                            )}
                                            {codeStatus === 'running' ? 'Running...' : 'Execute'}
                                        </button>
                                    </>
                                )}
                            </div>
                        </header>
                        <div className="hud-code-main">
                            {activeWorkspaceTab === 'code' ? (
                                <>
                                    <div className="hud-editor-area">
                                        <Editor
                                            height="100%"
                                            language={language}
                                            theme="vs-dark"
                                            value={code}
                                            onChange={handleCodeChange}
                                            options={{
                                                minimap: { enabled: false },
                                                fontSize: 14,
                                                fontFamily: "'JetBrains Mono', monospace",
                                                padding: { top: 16 },
                                            }}
                                        />
                                    </div>
                                    <div className={`hud-code-output ${codeStatus}`}>
                                        <div className="hud-output-header">
                                            <div className="hud-output-title">
                                                <Terminal style={{ width: 14, height: 14, color: '#00d4ff' }} /> SYS_OUT
                                            </div>
                                            <div className="hud-output-status">
                                                {codeStatus === 'idle' && (
                                                    <span className="hud-status-idle">● Ready</span>
                                                )}
                                                {codeStatus === 'running' && (
                                                    <span className="hud-status-running">
                                                        <Loader2 style={{ width: 12, height: 12, animation: 'spin-slow 1s linear infinite' }} />
                                                        Running...
                                                    </span>
                                                )}
                                                {codeStatus === 'success' && (
                                                    <span className="hud-status-success">
                                                        <CheckCircle style={{ width: 12, height: 12 }} />
                                                        Executed Successfully
                                                    </span>
                                                )}
                                                {codeStatus === 'error' && (
                                                    <span className="hud-status-error">
                                                        <XCircle style={{ width: 12, height: 12 }} />
                                                        Error
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        <pre className={`hud-output-text ${codeStatus}`}>
                                            {codeResult || 'Ready for execution...'}
                                        </pre>
                                    </div>
                                </>
                            ) : (
                                <div className="hud-whiteboard-workspace">
                                    {}
                                    <div className="hud-wb-input-panel">
                                        <div className="hud-wb-header">📝 Your Input</div>
                                        <textarea
                                            className="hud-wb-textarea"
                                            placeholder="Write your approach, pseudo-code, or question here..."
                                            value={wbInput}
                                            onChange={e => setWbInput(e.target.value)}
                                            onKeyDown={e => {
                                                if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                                                    e.preventDefault();
                                                    handleWhiteboardSubmit();
                                                }
                                            }}
                                        />
                                        <div className="hud-wb-actions">
                                            <button
                                                className="hud-wb-submit-btn"
                                                onClick={handleWhiteboardSubmit}
                                                disabled={!wbInput.trim() || wbLoading}
                                            >
                                                {wbLoading ? (
                                                    <Loader2 style={{ width: 14, height: 14, animation: 'spin-slow 1s linear infinite', display: 'inline', marginRight: 6 }} />
                                                ) : (
                                                    <ArrowRight style={{ width: 14, height: 14, display: 'inline', marginRight: 6 }} />
                                                )}
                                                Submit
                                            </button>
                                            <button
                                                className="hud-wb-clear-btn"
                                                onClick={() => { setWbInput(''); setWbEntries([]); }}
                                            >
                                                <Trash2 style={{ width: 13, height: 13, display: 'inline', marginRight: 4 }} />
                                                Clear
                                            </button>
                                            <span style={{ fontSize: '0.65rem', color: '#94a3b8', marginLeft: 'auto' }}>Ctrl+Enter to send</span>
                                        </div>
                                    </div>
                                    {}
                                    <div className="hud-wb-response-panel">
                                        <div className="hud-wb-header">🤖 AI Response</div>
                                        {wbEntries.length === 0 && !wbLoading && (
                                            <div style={{ color: '#94a3b8', fontSize: '0.8rem', padding: '8px 0' }}>
                                                AI responses will appear here. Type your question on the left and click Submit.
                                            </div>
                                        )}
                                        {wbLoading && (
                                            <div className="hud-wb-loading">
                                                <Loader2 style={{ width: 16, height: 16, animation: 'spin-slow 1s linear infinite', color: '#00d4ff' }} />
                                                <span>Thinking…</span>
                                            </div>
                                        )}
                                        {wbEntries.map((entry, idx) => (
                                            <div key={idx} className="hud-wb-response-entry">
                                                <div className="hud-wb-response-ts">
                                                    {entry.timestamp} · {wbMode}
                                                </div>
                                                <div style={{ fontSize: '0.75rem', color: '#475569', marginBottom: 6, fontStyle: 'italic', borderLeft: '2px solid #cbd5e1', paddingLeft: 8 }}>
                                                    {entry.userText.length > 80 ? entry.userText.slice(0, 80) + '…' : entry.userText}
                                                </div>
                                                {entry.format === 'code' ? (
                                                    <pre className="hud-wb-response-code">{entry.aiResponse}</pre>
                                                ) : (
                                                    <div className="hud-wb-response-text">{entry.aiResponse}</div>
                                                )}
                                            </div>
                                        ))}
                                        <div ref={wbResponseEndRef} />
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}
                {}
                {(viewMode === 'chat' || viewMode === 'codeChat') && (
                    <div className="hud-chat-panel" style={{
                        display: 'flex',
                        flexDirection: 'column',
                        flex: viewMode === 'codeChat' ? '2' : '1',
                        minWidth: 0,
                        overflow: 'hidden',
                        background: 'rgba(15, 23, 42, 0.95)',
                        borderLeft: '1px solid rgba(0, 212, 255, 0.15)',
                    }}>
                        <div className="hud-chat-header">
                            <div className="hud-chat-title"><MessageSquare size={16} /> Comms Link</div>
                            <button className="hud-chat-close" onClick={() => setShowChat(false)}><X size={20} /></button>
                        </div>
                        <div className="hud-chat-messages">
                            {messages.map((msg, idx) => {
                                if (!msg) return null;
                                const safeContent = typeof msg.content === 'string'
                                    ? msg.content
                                    : typeof msg.content === 'object' && msg.content !== null
                                        ? JSON.stringify(msg.content)
                                        : String(msg.content || '');
                                return (
                                    <div key={idx} className={`hud-msg ${msg.role}`}>
                                        <div className="hud-msg-role">{msg.role === 'interviewer' ? 'Nexus AI' : 'Candidate'}</div>
                                        <div className="hud-msg-bubble">{safeContent}</div>
                                    </div>
                                );
                            })}
                            <div ref={messagesEndRef} />
                        </div>
                        <div className="hud-chat-input-wrapper">
                            <div className="hud-chat-input-box">
                                <input
                                    className="hud-chat-input"
                                    value={inputMessage}
                                    onChange={e => setInputMessage(e.target.value)}
                                    onKeyDown={e => e.key === 'Enter' && handleSendMessage()}
                                    placeholder="Transmit message..."
                                />
                                <button className="hud-chat-send" onClick={handleSendMessage} disabled={!inputMessage.trim()}>
                                    <Send size={18} />
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
            {}
            <div className="hud-dock-wrapper">
                <div className="hud-dock">
                    {}
                    <button
                        className={`hud-dock-btn ${isRecording ? 'recording' : micEnabled ? 'active' : ''}`}
                        onClick={toggleRecording}
                        style={{ position: 'relative' }}
                    >
                        {isRecording || micEnabled ? <Mic size={22} /> : <MicOff size={22} />}
                        {isRecording && (
                            <div className="hud-mic-volume" style={{ position: 'absolute', bottom: 2, left: '50%', transform: 'translateX(-50%)' }}>
                                {micVolume.map((v, i) => (
                                    <div
                                        key={i}
                                        className="hud-mic-bar"
                                        style={{ height: `${Math.max(2, v * 0.18)}px` }}
                                    />
                                ))}
                            </div>
                        )}
                        <div className="hud-tooltip">{isRecording ? 'STOP RECORDING' : 'START RECORDING'}</div>
                    </button>
                    <button
                        className={`hud-dock-btn ${videoEnabled ? 'active' : ''}`}
                        onClick={() => setVideoEnabled(!videoEnabled)}
                    >
                        {videoEnabled ? <Video size={22} /> : <VideoOff size={22} />}
                        <div className="hud-tooltip">CAMERA</div>
                    </button>
                    {}
                    <button
                        className={`hud-dock-btn ${isScreenSharing ? 'active screen-sharing' : ''}`}
                        onClick={toggleScreenShare}
                    >
                        <svg xmlns="http:
                        <div className="hud-tooltip">{isScreenSharing ? 'STOP SHARING' : 'SHARE SCREEN'}</div>
                    </button>
                    <div className="hud-dock-sep" />
                    <button className={`hud-dock-btn ${showCode ? 'active' : ''}`} onClick={() => setShowCode(!showCode)}>
                        <Code2 size={22} />
                        <div className="hud-tooltip">WORKSPACE</div>
                    </button>
                    <button className={`hud-dock-btn ${showChat ? 'active' : ''}`} onClick={() => setShowChat(!showChat)}>
                        <MessageSquare size={22} />
                        {unreadMessageCount > 0 && <div className="hud-badge">{unreadMessageCount}</div>}
                        <div className="hud-tooltip">COMMS LINK</div>
                    </button>
                    <button className={`hud-dock-btn ${showHintPanel ? 'active' : ''}`} onClick={() => setShowHintPanel(!showHintPanel)}>
                        <Lightbulb size={22} />
                        {coachingHints.length > 0 && <div className="hud-badge">{coachingHints.length}</div>}
                        <div className="hud-tooltip">AI NUDGES</div>
                    </button>
                    <div className="hud-dock-sep" />
                    <button
                        className={`hud-dock-btn danger ${isEndingSession ? 'recording' : ''}`}
                        onClick={handleEndInterview}
                        disabled={isEndingSession}
                    >
                        {isEndingSession
                            ? <Loader2 style={{ width: 22, height: 22, animation: 'spin-slow 1s linear infinite' }} />
                            : <Power style={{ width: 22, height: 22 }} />
                        }
                        <div className="hud-tooltip">DISCONNECT</div>
                    </button>
                </div>
            </div>
            {}
            <AnimatePresence>
                {showHintPanel && coachingHints.length > 0 && (
                    <motion.div
                        className="hud-hints-panel"
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                    >
                        <div className="hud-hint-title"><ShieldAlert size={14} /> Critical Nudges</div>
                        {coachingHints.slice(-3).map((hint, i) => (
                            <div key={i} className="hud-hint-item">
                                <div className="hud-hint-dim">{hint.dimension.replace(/_/g, ' ')}</div>
                                <p>{hint.hint}</p>
                            </div>
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
