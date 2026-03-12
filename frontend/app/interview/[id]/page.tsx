'use client';
import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
    Mic, MicOff, Video, VideoOff, MessageSquare, Code2,
    Send, Phone, Monitor, X, Play, RotateCcw, User, Bot,
    Lightbulb, Terminal
} from 'lucide-react';
import { getServiceUrl, apiClient } from '../../../src/lib/api';
import * as faceapi from 'face-api.js';
import Editor from '@monaco-editor/react';
import './interview-room.css';
interface Message {
    role: 'interviewer' | 'candidate';
    content: string;
    timestamp: Date;
}
interface DimensionScores {
    [key: string]: number;
}
export default function InterviewRoomPage() {
    const params = useParams();
    const router = useRouter();
    const sessionId = params.id as string;
    const wsRef = useRef<WebSocket | null>(null);
    const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
    const videoRef = useRef<HTMLVideoElement>(null);
    const [modelsLoaded, setModelsLoaded] = useState(false);
    const [currentEmotion, setCurrentEmotion] = useState<string>('neutral');
    const [messages, setMessages] = useState<Message[]>([]);
    const [currentInput, setCurrentInput] = useState('');
    const [code, setCode] = useState('# Write your solution here\n\n');
    const [language, setLanguage] = useState('python');
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [lastAIMessage, setLastAIMessage] = useState<string>('');
    const [codeOutput, setCodeOutput] = useState('');
    
    const [dimensionScores, setDimensionScores] = useState<DimensionScores>({});
    
    const [assessmentMode, setAssessmentMode] = useState<string>('practice');
    const [timeLimitMinutes, setTimeLimitMinutes] = useState<number | null>(null);
    const [consentGiven, setConsentGiven] = useState(false);
    const [antiCheatWarnings, setAntiCheatWarnings] = useState(0);
    const [micEnabled, setMicEnabled] = useState(true);
    const [videoEnabled, setVideoEnabled] = useState(true);
    const [showCode, setShowCode] = useState(false);
    const [showChat, setShowChat] = useState(false);
    const [chatClosing, setChatClosing] = useState(false);
    const [hintsRemaining, setHintsRemaining] = useState(3);
    const [currentHint, setCurrentHint] = useState<string | null>(null);
    const [hintLoading, setHintLoading] = useState(false);
    const [showHintPanel, setShowHintPanel] = useState(false);
    const [timeElapsed, setTimeElapsed] = useState(0);
    const chatEndRef = useRef<HTMLDivElement>(null);
    const languages = [
        { id: 'python', label: 'Python', monacoId: 'python' },
        { id: 'javascript', label: 'JavaScript', monacoId: 'javascript' },
        { id: 'typescript', label: 'TypeScript', monacoId: 'typescript' },
        { id: 'java', label: 'Java', monacoId: 'java' },
        { id: 'cpp', label: 'C++', monacoId: 'cpp' },
    ];
    const waveformBars = Array.from({ length: 16 }, (_, i) => ({
        id: i,
        delay: `${i * 0.07}s`,
    }));
    useEffect(() => {
        const fetchSession = async () => {
            try {
                const res = await apiClient.get(`${getServiceUrl('session')}/sessions/${sessionId}`);
                setAssessmentMode(res.data.assessment_mode || 'practice');
                setTimeLimitMinutes(res.data.time_limit_minutes);
                if (res.data.assessment_mode !== 'certified') {
                    setConsentGiven(true);
                }
            } catch (err) {
                console.error("Failed to fetch session", err);
                setConsentGiven(true);
            }
        };
        fetchSession();
    }, [sessionId]);
    useEffect(() => {
        if (!consentGiven) return;
        const token = localStorage.getItem('access_token');
        if (!token) {
            router.push('/login');
            return;
        }
        const baseWs = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
        const wsUrl = `${baseWs}/ws/sessions/ws/${sessionId}?token=${token}`;
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;
        setWsStatus('connecting');
        ws.onopen = () => {
            console.log('WebSocket connected');
            setWsStatus('connected');
        };
        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            handleWebSocketMessage(message);
        };
        ws.onerror = () => setWsStatus('disconnected');
        ws.onclose = () => setWsStatus('disconnected');
        return () => {
            if (ws.readyState === WebSocket.OPEN) ws.close();
        };
    }, [sessionId, router, consentGiven]);
    useEffect(() => {
        if (wsStatus !== 'connected') return;
        const interval = setInterval(() => setTimeElapsed(prev => prev + 1), 1000);
        return () => clearInterval(interval);
    }, [wsStatus]);
    useEffect(() => {
        const loadModels = async () => {
            try {
                await Promise.all([
                    faceapi.nets.tinyFaceDetector.loadFromUri('/models'),
                    faceapi.nets.faceExpressionNet.loadFromUri('/models')
                ]);
                setModelsLoaded(true);
            } catch (err) {
                console.error("Failed to load face-api models", err);
            }
        };
        loadModels();
    }, []);
    useEffect(() => {
        let stream: MediaStream | null = null;
        if (consentGiven && videoEnabled) {
            navigator.mediaDevices.getUserMedia({ video: true, audio: micEnabled })
                .then(s => {
                    stream = s;
                    if (videoRef.current) {
                        videoRef.current.srcObject = s;
                    }
                })
                .catch(err => console.error("Webcam access denied", err));
        }
        return () => {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
        };
    }, [consentGiven, videoEnabled, micEnabled]);
    const handleVideoPlay = () => {
        if (!modelsLoaded || !videoRef.current) return;
        setInterval(async () => {
            if (videoRef.current && !videoRef.current.paused && !videoRef.current.ended) {
                const detections = await faceapi.detectSingleFace(
                    videoRef.current,
                    new faceapi.TinyFaceDetectorOptions()
                ).withFaceExpressions();
                if (detections) {
                    const expressions = detections.expressions;
                    const dominant = Object.keys(expressions).reduce((a, b) =>
                        expressions[a as keyof faceapi.FaceExpressions] > expressions[b as keyof faceapi.FaceExpressions] ? a : b
                    );
                    setCurrentEmotion(dominant);
                }
            }
        }, 2000);
    };
    useEffect(() => {
        if (assessmentMode !== 'certified' || !consentGiven) return;
        const handleVisibilityChange = async () => {
            if (document.hidden) {
                setAntiCheatWarnings(prev => prev + 1);
                try {
                    await apiClient.post(`${getServiceUrl('session')}/sessions/${sessionId}/anti-cheat`, {
                        signal_type: 'tab_switch', description: 'Tab switch detected.', level: 'flagged'
                    });
                } catch (e) { console.error("Anti-cheat report failed", e); }
            }
        };
        document.addEventListener('visibilitychange', handleVisibilityChange);
        return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
    }, [assessmentMode, consentGiven, sessionId]);
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);
    const handleWebSocketMessage = useCallback((message: any) => {
        switch (message.type) {
            case 'interviewer_text':
                setMessages(prev => [...prev, {
                    role: 'interviewer', content: message.data, timestamp: new Date()
                }]);
                setLastAIMessage(message.data);
                setIsSpeaking(true);
                setTimeout(() => setIsSpeaking(false), 3000);
                break;
            case 'score_update':
                setDimensionScores(message.data.scores || {});
                break;
            case 'hint_response':
                setCurrentHint(message.data?.hint || 'Consider breaking the problem into smaller parts.');
                setHintLoading(false);
                setShowHintPanel(true);
                break;
            case 'session_ended':
                router.push(`/interview/report/${sessionId}`);
                break;
            case 'error':
                console.error('Session error:', message.data);
                break;
        }
    }, [router, sessionId]);
    const sendTextMessage = () => {
        if (!currentInput.trim() || wsStatus !== 'connected') return;
        const ws = wsRef.current;
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'text_message', data: { message: currentInput } }));
            setMessages(prev => [...prev, {
                role: 'candidate', content: currentInput, timestamp: new Date()
            }]);
            setCurrentInput('');
        }
    };
    const sendCodeUpdate = () => {
        const ws = wsRef.current;
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'code_update', data: { code, language } }));
            setCodeOutput('⏳ Submitting code...');
        }
    };
    const endSession = () => {
        const ws = wsRef.current;
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'end_session', data: {} }));
        }
        router.push(`/interview/report/${sessionId}`);
    };
    const requestHint = () => {
        if (hintsRemaining <= 0 || hintLoading) return;
        const ws = wsRef.current;
        if (ws && ws.readyState === WebSocket.OPEN) {
            setHintLoading(true);
            setHintsRemaining(prev => prev - 1);
            ws.send(JSON.stringify({ type: 'hint_request', data: { context: messages.slice(-3).map(m => m.content).join(' ') } }));
        }
    };
    const toggleChat = () => {
        if (showChat) {
            setChatClosing(true);
            setTimeout(() => { setShowChat(false); setChatClosing(false); }, 250);
        } else {
            setShowChat(true);
        }
    };
    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };
    const getUserInitials = () => {
        try {
            const user = JSON.parse(localStorage.getItem('user') || '{}');
            if (user?.full_name) {
                return user.full_name.split(' ').map((n: string) => n[0]).join('').slice(0, 2);
            }
        } catch { }
        return 'Y';
    };
    if (!consentGiven && assessmentMode === 'certified') {
        return (
            <div className="consent-overlay">
                <div className="consent-card">
                    <div style={{
                        width: 64, height: 64, borderRadius: '50%',
                        background: 'rgba(0, 212, 255, 0.1)', margin: '0 auto 16px',
                        display: 'flex', alignItems: 'center', justifyContent: 'center'
                    }}>
                        <Monitor style={{ width: 32, height: 32, color: '#00d4ff' }} />
                    </div>
                    <h1>Certified Assessment</h1>
                    <p>This is a formal, proctored assessment. By continuing, you agree to the following:</p>
                    <ul>
                        <li>Your webcam and microphone may be recorded.</li>
                        <li>Leaving the browser tab will be logged.</li>
                        <li>A strict time limit of {timeLimitMinutes || 'custom'} minutes is enforced.</li>
                        <li>Live coaching hints are disabled.</li>
                    </ul>
                    <button className="consent-btn-primary" onClick={() => setConsentGiven(true)}>
                        I Agree — Start Assessment
                    </button>
                    <button className="consent-btn-secondary" onClick={() => router.push('/dashboard')}>
                        Cancel & Return
                    </button>
                </div>
            </div>
        );
    }
    return (
        <div className="interview-room">
            {}
            {antiCheatWarnings > 0 && assessmentMode === 'certified' && (
                <div className="anti-cheat-banner">
                    <Monitor style={{ width: 16, height: 16 }} />
                    Warning: Tab switching detected ({antiCheatWarnings}). This activity is logged.
                </div>
            )}
            {}
            <div className="top-bar">
                <div className="top-bar-left">
                    <div className="session-timer">{formatTime(timeElapsed)}</div>
                    <div className="session-info">
                        <span className="company-name">SynthHire Interview</span>
                        <span>•</span>
                        <span>Session {sessionId.slice(0, 8)}</span>
                    </div>
                    <div className={`connection-pill ${wsStatus}`}>
                        <span className="connection-dot" />
                        {wsStatus}
                    </div>
                </div>
                <button className="end-btn" onClick={endSession}>
                    End Interview
                </button>
            </div>
            {}
            <div className="main-content">
                {}
                <div className={`video-tiles-grid ${showCode ? 'compact' : ''}`}>
                    {}
                    <div className={`video-tile ${isSpeaking ? 'speaking' : ''}`}>
                        <div className="ai-tile-content">
                            <div className={`ai-avatar-ring ${isSpeaking ? 'speaking' : ''}`}>
                                <div className="ai-avatar-inner">
                                    <Bot className="ai-avatar-icon" />
                                </div>
                            </div>
                            <div className="ai-tile-info">
                                <div className="ai-name">AI Interviewer</div>
                                <div className={`ai-status ${isSpeaking ? 'speaking-status' : ''}`}>
                                    {isSpeaking ? (
                                        <>
                                            <div className="waveform-container">
                                                {waveformBars.map(bar => (
                                                    <div
                                                        key={bar.id}
                                                        className={`waveform-bar ${isSpeaking ? 'active' : ''}`}
                                                        style={{
                                                            animationDelay: bar.delay,
                                                            height: `${6 + Math.random() * 14}px`,
                                                        }}
                                                    />
                                                ))}
                                            </div>
                                            Speaking...
                                        </>
                                    ) : (
                                        'Listening...'
                                    )}
                                </div>
                            </div>
                        </div>
                        {}
                        {lastAIMessage && (
                            <div className="live-caption">
                                {lastAIMessage.slice(0, 200)}{lastAIMessage.length > 200 ? '...' : ''}
                            </div>
                        )}
                    </div>
                    {}
                    <div className="video-tile">
                        <div className="candidate-tile-content">
                            {videoEnabled ? (
                                <video
                                    ref={videoRef}
                                    autoPlay
                                    muted
                                    playsInline
                                    onPlay={handleVideoPlay}
                                />
                            ) : (
                                <div className="candidate-avatar">
                                    <span className="candidate-initials">{getUserInitials()}</span>
                                </div>
                            )}
                        </div>
                        {}
                        <div className="tile-label">
                            You
                            {!micEnabled && <MicOff className="muted-icon" style={{ width: 12, height: 12 }} />}
                        </div>
                        {}
                        {videoEnabled && modelsLoaded && currentEmotion && currentEmotion !== 'neutral' && (
                            <div className="emotion-badge">{currentEmotion}</div>
                        )}
                    </div>
                </div>
                {}
                {showCode && (
                    <div className="code-pane">
                        <div className="code-pane-header">
                            <div className="lang-tabs">
                                {languages.map(lang => (
                                    <button
                                        key={lang.id}
                                        className={`lang-tab ${language === lang.id ? 'active' : ''}`}
                                        onClick={() => setLanguage(lang.id)}
                                    >
                                        {lang.label}
                                    </button>
                                ))}
                            </div>
                            <div style={{ display: 'flex', gap: 6 }}>
                                <button className="reset-btn" onClick={() => setCode('# Write your solution here\n\n')}>
                                    <RotateCcw style={{ width: 12, height: 12 }} /> Reset
                                </button>
                                <button className="run-btn" onClick={sendCodeUpdate}>
                                    <Play style={{ width: 14, height: 14 }} /> Run
                                </button>
                            </div>
                        </div>
                        <div className="code-editor-wrapper">
                            <Editor
                                height="100%"
                                language={languages.find(l => l.id === language)?.monacoId || 'python'}
                                value={code}
                                onChange={(value) => setCode(value || '')}
                                theme="vs-dark"
                                options={{
                                    minimap: { enabled: false },
                                    fontSize: 14,
                                    lineNumbersMinChars: 3,
                                    scrollBeyondLastLine: false,
                                    fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                                    padding: { top: 12, bottom: 12 },
                                    renderLineHighlight: 'line',
                                    cursorBlinking: 'smooth',
                                    smoothScrolling: true,
                                    automaticLayout: true,
                                }}
                            />
                        </div>
                        {}
                        <div className="code-output-panel">
                            <div className="code-output-header">
                                <span><Terminal style={{ width: 12, height: 12, display: 'inline', marginRight: 6, verticalAlign: 'middle' }} />Output</span>
                                <span style={{ fontSize: '0.65rem', color: '#475569' }}>
                                    {language.toUpperCase()} • {code.split('\n').length} lines
                                </span>
                            </div>
                            <div className="code-output-body">
                                {codeOutput || 'Run code to see output...'}
                            </div>
                        </div>
                    </div>
                )}
            </div>
            {}
            <div className="control-bar">
                <button
                    className={`ctrl-btn ${micEnabled ? 'active' : 'muted'}`}
                    onClick={() => setMicEnabled(!micEnabled)}
                >
                    {micEnabled ? <Mic style={{ width: 20, height: 20 }} /> : <MicOff style={{ width: 20, height: 20 }} />}
                    <span className="ctrl-btn-tooltip">{micEnabled ? 'Mute' : 'Unmute'}</span>
                </button>
                <button
                    className={`ctrl-btn ${videoEnabled ? 'active' : 'muted'}`}
                    onClick={() => setVideoEnabled(!videoEnabled)}
                >
                    {videoEnabled ? <Video style={{ width: 20, height: 20 }} /> : <VideoOff style={{ width: 20, height: 20 }} />}
                    <span className="ctrl-btn-tooltip">{videoEnabled ? 'Camera Off' : 'Camera On'}</span>
                </button>
                <div className="ctrl-divider" />
                <button
                    className={`ctrl-btn ${showCode ? 'active' : ''}`}
                    onClick={() => setShowCode(!showCode)}
                >
                    <Code2 style={{ width: 20, height: 20 }} />
                    <span className="ctrl-btn-tooltip">{showCode ? 'Hide Code' : 'Code Editor'}</span>
                </button>
                <button
                    className={`ctrl-btn ${showChat ? 'active' : ''}`}
                    onClick={toggleChat}
                >
                    <MessageSquare style={{ width: 20, height: 20 }} />
                    <span className="ctrl-btn-tooltip">{showChat ? 'Hide Chat' : 'Chat'}</span>
                </button>
                <div className="ctrl-divider" />
                <button
                    className={`ctrl-btn ${hintsRemaining > 0 ? 'hint' : 'muted'}`}
                    onClick={requestHint}
                    disabled={hintsRemaining <= 0 || hintLoading}
                    style={hintsRemaining > 0 ? { position: 'relative' } : {}}
                >
                    <Lightbulb style={{ width: 20, height: 20 }} />
                    <span className="ctrl-btn-tooltip">Panic Button ({hintsRemaining} left)</span>
                    {hintsRemaining > 0 && (
                        <span style={{
                            position: 'absolute', top: -2, right: -2,
                            width: 14, height: 14, borderRadius: '50%',
                            background: '#f59e0b', color: '#000', fontSize: 9, fontWeight: 'bold',
                            display: 'flex', alignItems: 'center', justifyContent: 'center'
                        }}>{hintsRemaining}</span>
                    )}
                </button>
                <div className="ctrl-divider" />
                <button className="ctrl-btn danger" onClick={endSession}>
                    <Phone style={{ width: 20, height: 20, transform: 'rotate(135deg)' }} />
                    <span className="ctrl-btn-tooltip">Leave Interview</span>
                </button>
            </div>
            {}
            {showHintPanel && currentHint && (
                <div className="hint-panel">
                    <div className="hint-panel-header">
                        <div className="hint-panel-title">
                            <Lightbulb style={{ width: 16, height: 16, color: '#f59e0b' }} />
                            <span>AI Nudge</span>
                            <span className="hint-panel-subtitle">({hintsRemaining} left • −XP penalty)</span>
                        </div>
                        <button onClick={() => setShowHintPanel(false)} style={{ color: '#64748b', cursor: 'pointer', background: 'none', border: 'none' }}>
                            <X style={{ width: 14, height: 14 }} />
                        </button>
                    </div>
                    <p>{currentHint}</p>
                </div>
            )}
            {}
            {showChat && (
                <div className={`chat-panel ${chatClosing ? 'closing' : ''}`}>
                    <div className="chat-header">
                        <h3>💬 Interview Chat</h3>
                        <button className="chat-close-btn" onClick={toggleChat}>
                            <X style={{ width: 14, height: 14 }} />
                        </button>
                    </div>
                    <div className="chat-messages">
                        {messages.length === 0 && (
                            <div style={{ textAlign: 'center', color: '#475569', paddingTop: 40 }}>
                                <Bot style={{ width: 40, height: 40, margin: '0 auto 10px', opacity: 0.3 }} />
                                <p style={{ fontSize: '0.8rem' }}>Messages will appear here...</p>
                            </div>
                        )}
                        {messages.map((msg, idx) => (
                            <div key={idx} className={`chat-msg ${msg.role}`}>
                                <div className="chat-msg-bubble">{msg.content}</div>
                                <div className="chat-msg-meta">
                                    <span className="chat-msg-role">
                                        {msg.role === 'interviewer' ? '🤖 AI' : '👤 You'}
                                    </span>
                                    <span className="chat-msg-time">
                                        {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </span>
                                </div>
                            </div>
                        ))}
                        <div ref={chatEndRef} />
                    </div>
                    <div className="chat-input-area">
                        <textarea
                            className="chat-input"
                            value={currentInput}
                            onChange={(e) => setCurrentInput(e.target.value)}
                            placeholder="Type your response..."
                            rows={1}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    sendTextMessage();
                                }
                            }}
                        />
                        <button
                            className="chat-send-btn"
                            onClick={sendTextMessage}
                            disabled={!currentInput.trim() || wsStatus !== 'connected'}
                        >
                            <Send style={{ width: 16, height: 16 }} />
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
