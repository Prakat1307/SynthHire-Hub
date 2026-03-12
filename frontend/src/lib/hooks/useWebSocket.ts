import { useEffect, useRef, useCallback } from 'react';
import { useSessionStore } from '../stores/sessionStore';
import { useAuthStore } from '@/lib/stores/authStore';
import { getServiceUrl } from '../api';
export const useWebSocket = (sessionId: string | null) => {
    const ws = useRef<WebSocket | null>(null);
    const { accessToken } = useAuthStore();
    const {
        setConnected,
        addExchange,
        updateScores,
        addCoachingHints,
        setProcessing
    } = useSessionStore();
    useEffect(() => {
        if (!sessionId || !accessToken) return;
        const url = `${getServiceUrl('session').replace('http', 'ws')}/sessions/ws/${sessionId}?token=${accessToken}`;
        ws.current = new WebSocket(url);
        ws.current.onopen = () => {
            console.log('WebSocket Connected');
            setConnected(true);
        };
        ws.current.onclose = () => {
            console.log('WebSocket Disconnected');
            setConnected(false);
        };
        ws.current.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                const { type, data } = message;
                switch (type) {
                    case 'session_started':
                        addExchange({
                            exchange_number: 0,
                            response_text: data.response_text,
                            question_type: 'greeting',
                            phase_suggestion: 'opening',
                            audio_url: data.audio_url
                        });
                        break;
                    case 'ai_response':
                        setProcessing(false);
                        addExchange({
                            exchange_number: data.exchange_number,
                            response_text: data.response_text,
                            question_type: data.question_type,
                            phase_suggestion: data.phase_suggestion,
                            audio_url: data.audio_url
                        });
                        break;
                    case 'score_update':
                        updateScores(data.scores);
                        break;
                    case 'coaching_hints':
                        addCoachingHints(data.hints);
                        break;
                    case 'error':
                        console.error('WS Error:', data.message);
                        setProcessing(false);
                        break;
                }
            } catch (err) {
                console.error('Failed to parse WS message', err);
            }
        };
        return () => {
            ws.current?.close();
        };
    }, [sessionId, accessToken, setConnected, addExchange, updateScores, addCoachingHints, setProcessing]);
    const sendMessage = useCallback((text: string) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
            setProcessing(true);
            ws.current.send(JSON.stringify({
                type: 'user_message',
                data: { text }
            }));
        }
    }, [setProcessing]);
    const sendAudio = useCallback((base64Audio: string) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
            setProcessing(true);
            ws.current.send(JSON.stringify({
                type: 'audio_chunk',
                data: { audio: base64Audio }
            }));
        }
    }, [setProcessing]);
    const submitCode = useCallback((code: string, language: string) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({
                type: 'code_submit',
                data: { code, language }
            }));
        }
    }, []);
    return { sendMessage, sendAudio, submitCode };
};
