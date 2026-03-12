import { create } from 'zustand';
import { Session, Exchange, DimensionScores, CoachingHint, Message, InterviewPhase, CodeExecutionResult } from '../../types';
interface SessionState {
    currentSession: Session | null;
    messages: Message[];
    exchanges: Exchange[];
    currentScores: DimensionScores | null;
    coachingHints: CoachingHint[];
    currentPhase: InterviewPhase;
    codeResult: CodeExecutionResult | null;
    isRecording: boolean;
    isProcessing: boolean;
    isConnected: boolean;
    setSession: (session: Session) => void;
    addMessage: (message: Message) => void;
    addExchange: (exchange: Exchange) => void;
    incrementExchange: () => void;
    updateScores: (scores: DimensionScores) => void;
    setDimensionScores: (scores: DimensionScores) => void;
    addCoachingHints: (hints: CoachingHint[]) => void;
    setCoachingHints: (hints: CoachingHint[]) => void;
    setPhase: (phase: InterviewPhase) => void;
    setCodeResult: (result: CodeExecutionResult | null) => void;
    setRecording: (status: boolean) => void;
    setProcessing: (status: boolean) => void;
    setConnected: (status: boolean) => void;
    resetSession: () => void;
}
export const useSessionStore = create<SessionState>((set) => ({
    currentSession: null,
    messages: [],
    exchanges: [],
    currentScores: null,
    coachingHints: [],
    currentPhase: 'talk',
    codeResult: null,
    isRecording: false,
    isProcessing: false,
    isConnected: false,
    setSession: (session: Session) => set({ currentSession: session }),
    addMessage: (message: Message) => set((state: SessionState) => ({
        messages: [...state.messages, message]
    })),
    addExchange: (exchange: Exchange) => set((state: SessionState) => ({
        exchanges: [...state.exchanges, exchange]
    })),
    incrementExchange: () => set((state: SessionState) => ({
        currentSession: state.currentSession ? {
            ...state.currentSession,
            difficulty_level: (state.currentSession.difficulty_level || 1) 
        } : null
    })),
    updateScores: (scores: DimensionScores) => set({ currentScores: scores }),
    setDimensionScores: (scores: DimensionScores) => set({ currentScores: scores }),
    addCoachingHints: (hints: CoachingHint[]) => set((state: SessionState) => ({
        coachingHints: [...hints, ...state.coachingHints].slice(0, 10)
    })),
    setCoachingHints: (hints: CoachingHint[]) => set({ coachingHints: hints }),
    setPhase: (phase: InterviewPhase) => set({ currentPhase: phase }),
    setCodeResult: (result: CodeExecutionResult | null) => set({ codeResult: result }),
    setRecording: (status: boolean) => set({ isRecording: status }),
    setProcessing: (status: boolean) => set({ isProcessing: status }),
    setConnected: (status: boolean) => set({ isConnected: status }),
    resetSession: () => set({
        currentSession: null,
        messages: [],
        exchanges: [],
        currentScores: null,
        coachingHints: [],
        currentPhase: 'talk',
        codeResult: null,
        isRecording: false,
        isProcessing: false,
        isConnected: false
    })
}));
