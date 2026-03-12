import { create } from 'zustand';
import toast from 'react-hot-toast';
export interface DimensionScores {
    technical_correctness: number;
    problem_decomposition: number;
    communication_clarity: number;
    handling_ambiguity: number;
    edge_case_awareness: number;
    time_management: number;
    collaborative_signals: number;
    growth_mindset: number;
}
interface Message {
    role: 'interviewer' | 'candidate';
    content: string;
    audioUrl?: string;
    timestamp: Date;
}
interface CoachingHint {
    hint: string;
    dimension: string;
    priority: string;
    timestamp: Date;
}
interface InterviewState {
    sessionId: string | null;
    status: 'idle' | 'connecting' | 'active' | 'paused' | 'completed';
    websocket: WebSocket | null;
    messages: Message[];
    dimensionScores: DimensionScores;
    coachingHints: CoachingHint[];
    currentPhase: string;
    timeElapsed: number;
    connect: (sessionId: string, wsUrl: string) => void;
    disconnect: () => void;
    sendMessage: (message: string) => void;
    sendAudio: (base64Audio: string) => void;
    sendCode: (code: string, language: string) => void;
    endSession: () => void;
    codeResult: string;
    addMessage: (role: 'interviewer' | 'candidate', content: string, audioUrl?: string) => void;
    updateScores: (scores: Partial<DimensionScores>) => void;
    addCoachingHint: (hint: CoachingHint) => void;
    reset: () => void;
}
const initialScores: DimensionScores = {
    technical_correctness: 0,
    problem_decomposition: 0,
    communication_clarity: 0,
    handling_ambiguity: 0,
    edge_case_awareness: 0,
    time_management: 0,
    collaborative_signals: 0,
    growth_mindset: 0
};
export const useInterviewStore = create<InterviewState>((set, get) => ({
    sessionId: null,
    status: 'idle',
    websocket: null,
    messages: [],
    dimensionScores: initialScores,
    coachingHints: [],
    currentPhase: 'waiting',
    timeElapsed: 0,
    codeResult: '',
    connect: (sessionId: string, wsUrl: string) => {
        const ws = new WebSocket(wsUrl);
        ws.onopen = () => {
            console.log('WebSocket connected');
            set({ status: 'active', sessionId, websocket: ws });
        };
        ws.onmessage = (event) => {
            try {
                const payload = JSON.parse(event.data);
                console.log('WebSocket received:', payload);
                switch (payload.type) {
                    case 'session_started':
                    case 'ai_response':
                        toast.dismiss('stt-toast'); 
                        if (payload.data?.response_text) {
                            get().addMessage('interviewer', payload.data.response_text, payload.data.audio_url);
                        }
                        if (payload.data?.phase) {
                            set({ currentPhase: payload.data.phase });
                        }
                        if (payload.data?.phase_suggestion) {
                            set({ currentPhase: payload.data.phase_suggestion });
                        }
                        break;
                    case 'transcript':
                        toast.dismiss('stt-toast');
                        if (payload.data?.text) {
                            get().addMessage('candidate', payload.data.text);
                        } else {
                            toast.error('Could not understand audio. Please speak clearly and try again.', { duration: 4000 });
                        }
                        break;
                    case 'score_update':
                        get().updateScores(payload.data?.scores);
                        break;
                    case 'code_result':
                        let outputStr = '';
                        if (payload.data.stderr || payload.data.error) {
                            outputStr = payload.data.stderr || payload.data.error;
                        } else if (payload.data.stdout || payload.data.output) {
                            outputStr = payload.data.stdout || payload.data.output;
                        } else {
                            outputStr = 'Executed successfully with no output.';
                        }
                        set({ codeResult: outputStr });
                        break;
                    case 'session_ended':
                        console.log('Session ended by server');
                        set({ status: 'completed' });
                        break;
                    case 'coaching_hints':
                        if (payload.data?.hints && Array.isArray(payload.data.hints)) {
                            payload.data.hints.forEach((hint: any) => {
                                get().addCoachingHint({
                                    ...hint,
                                    timestamp: new Date()
                                });
                            });
                        }
                        break;
                    case 'error':
                        console.error('WebSocket error payload:', payload.data);
                        break;
                    default:
                        console.log('Unknown WebSocket message type:', payload.type);
                }
            } catch (err) {
                console.error("Failed to parse WebSocket message:", err);
            }
        };
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            set({ status: 'idle' });
        };
        ws.onclose = () => {
            console.log('WebSocket disconnected');
            set({ status: 'completed', websocket: null });
        };
        set({ status: 'connecting', websocket: ws });
    },
    disconnect: () => {
        const ws = get().websocket;
        if (ws) {
            ws.close();
        }
        set({ websocket: null, status: 'idle' });
    },
    sendMessage: (message: string) => {
        const ws = get().websocket;
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'user_message',
                data: { text: message }
            }));
            get().addMessage('candidate', message);
        }
    },
    sendCode: (code: string, language: string) => {
        const ws = get().websocket;
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'code_submit',
                data: { code, language }
            }));
        }
    },
    sendAudio: (base64Audio: string) => {
        const ws = get().websocket;
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'audio_chunk',
                data: { audio: base64Audio }
            }));
        }
    },
    endSession: () => {
        const ws = get().websocket;
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'end_session',
                data: {}
            }));
            setTimeout(() => {
                ws.close();
                set({ websocket: null, status: 'completed', sessionId: null });
            }, 2000);
        } else {
            set({ status: 'completed', sessionId: null });
        }
    },
    addMessage: (role, content, audioUrl) => {
        set(state => ({
            messages: [...state.messages, {
                role,
                content,
                audioUrl,
                timestamp: new Date()
            }]
        }));
    },
    updateScores: (scores) => {
        set(state => ({
            dimensionScores: { ...state.dimensionScores, ...scores }
        }));
    },
    addCoachingHint: (hint) => {
        set(state => ({
            coachingHints: [...state.coachingHints, hint]
        }));
    },
    reset: () => {
        set({
            sessionId: null,
            status: 'idle',
            websocket: null,
            messages: [],
            dimensionScores: initialScores,
            coachingHints: [],
            currentPhase: 'waiting',
            timeElapsed: 0
        });
    }
}));
