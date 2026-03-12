"use client";
import { useEffect, useRef, useCallback, useState } from "react";
import { useSessionStore } from "../stores/sessionStore";
import api from "../api";
interface WSMessage {
    id: string;
    seq: number;
    type: string;
    channel: "control" | "interview" | "coaching" | "code";
    timestamp: number;
    data: any;
    ack_required: boolean;
}
export function useWebSocketProtocol(sessionId: string | null) {
    const wsRef = useRef<WebSocket | null>(null);
    const seqRef = useRef(0);
    const reconnectAttempts = useRef(0);
    const reconnectTimeout = useRef<any>(null);
    const heartbeatInterval = useRef<any>(null);
    const messageBuffer = useRef<WSMessage[]>([]);
    const [connected, setConnected] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const store = useSessionStore();
    const sendRaw = useCallback((msg: WSMessage) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(msg));
        } else {
            messageBuffer.current.push(msg);
        }
    }, []);
    const send = useCallback(
        (
            type: string,
            data: any,
            channel: WSMessage["channel"] = "interview",
            ackRequired = false
        ) => {
            seqRef.current += 1;
            const msg: WSMessage = {
                id: crypto.randomUUID(),
                seq: seqRef.current,
                type,
                channel,
                timestamp: Date.now() / 1000,
                data,
                ack_required: ackRequired,
            };
            sendRaw(msg);
            return msg;
        },
        [sendRaw]
    );
    const handleMessage = useCallback(
        (event: MessageEvent) => {
            const msg: WSMessage = JSON.parse(event.data);
            if (msg.type === "ping") {
                sendRaw({
                    id: crypto.randomUUID(),
                    seq: 0,
                    type: "pong",
                    channel: "control",
                    timestamp: Date.now() / 1000,
                    data: {},
                    ack_required: false,
                });
                return;
            }
            if (msg.ack_required) {
                sendRaw({
                    id: crypto.randomUUID(),
                    seq: seqRef.current + 1,
                    type: "ack",
                    channel: "control",
                    timestamp: Date.now() / 1000,
                    data: { ack_id: msg.id },
                    ack_required: false,
                });
            }
            switch (msg.type) {
                case "session_started":
                    store.addMessage({
                        role: "assistant",
                        content: msg.data.response_text,
                        timestamp: new Date().toISOString(),
                        audio_url: msg.data.audio_url,
                    });
                    if (msg.data.audio_url) playAudio(msg.data.audio_url);
                    break;
                case "ai_response":
                    store.addMessage({
                        role: "assistant",
                        content: msg.data.response_text,
                        timestamp: new Date().toISOString(),
                        audio_url: msg.data.audio_url,
                    });
                    store.incrementExchange();
                    if (msg.data.phase_suggestion === "switch_to_code") store.setPhase("code");
                    if (msg.data.phase_suggestion === "switch_to_whiteboard") store.setPhase("whiteboard");
                    if (msg.data.audio_url) playAudio(msg.data.audio_url);
                    break;
                case "score_update":
                    store.setDimensionScores(msg.data.scores);
                    break;
                case "coaching_hints":
                    store.setCoachingHints(msg.data.hints);
                    break;
                case "transcript":
                    store.addMessage({
                        role: "user",
                        content: msg.data.text,
                        timestamp: new Date().toISOString(),
                    });
                    break;
                case "code_result":
                    store.setCodeResult(msg.data);
                    break;
                case "phase_change":
                    store.setPhase(msg.data.phase);
                    break;
                case "session_ended":
                    store.setConnected(false);
                    break;
                case "error":
                    setError(msg.data.message);
                    break;
            }
        },
        [send, sendRaw, store]
    );
    const connect = useCallback(() => {
        if (!sessionId) return;
        const url = api.getWebSocketUrl(sessionId);
        const ws = new WebSocket(url);
        wsRef.current = ws;
        ws.onopen = () => {
            setConnected(true);
            store.setConnected(true);
            setError(null);
            reconnectAttempts.current = 0;
            while (messageBuffer.current.length > 0) {
                const msg = messageBuffer.current.shift()!;
                ws.send(JSON.stringify(msg));
            }
            heartbeatInterval.current = setInterval(() => {
                if (ws.readyState === WebSocket.OPEN) {
                    sendRaw({
                        id: crypto.randomUUID(),
                        seq: 0,
                        type: "ping",
                        channel: "control",
                        timestamp: Date.now() / 1000,
                        data: {},
                        ack_required: false,
                    });
                }
            }, 30000);
        };
        ws.onmessage = handleMessage;
        ws.onclose = (e) => {
            setConnected(false);
            store.setConnected(false);
            if (heartbeatInterval.current) clearInterval(heartbeatInterval.current);
            if (reconnectAttempts.current < 5 && e.code !== 1000) {
                const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
                reconnectTimeout.current = setTimeout(() => {
                    reconnectAttempts.current++;
                    connect();
                }, delay);
            }
        };
        ws.onerror = () => setError("Connection error");
    }, [sessionId, handleMessage, sendRaw, store]);
    const disconnect = useCallback(() => {
        if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
        if (heartbeatInterval.current) clearInterval(heartbeatInterval.current);
        if (wsRef.current) {
            wsRef.current.close(1000);
            wsRef.current = null;
        }
        setConnected(false);
        store.setConnected(false);
    }, [store]);
    const sendUserMessage = useCallback(
        (text: string) => {
            store.addMessage({ role: "user", content: text, timestamp: new Date().toISOString() });
            send("user_message", { text }, "interview", true);
        },
        [send, store]
    );
    const sendAudioChunk = useCallback(
        (base64: string) => send("audio_chunk", { audio: base64 }, "interview"),
        [send]
    );
    const sendVideoFrame = useCallback(
        (base64: string) => send("video_frame", { image: base64 }, "interview"),
        [send]
    );
    const sendCodeSubmit = useCallback(
        (code: string, language: string) => send("code_submit", { code, language }, "code", true),
        [send]
    );
    const sendEndSession = useCallback(
        () => send("end_session", {}, "control", true),
        [send]
    );
    useEffect(() => {
        connect();
        return () => disconnect();
    }, [connect, disconnect]);
    return { connected, error, sendUserMessage, sendAudioChunk, sendVideoFrame, sendCodeSubmit, sendEndSession, disconnect };
}
function playAudio(url: string) {
    try { new Audio(url).play().catch(() => { }); } catch { }
}
