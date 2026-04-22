import { useState, useRef, useCallback, useEffect } from 'react';
import type { AgentPhase, ConnectionStatus, WSChunk, CitationMeta } from '../types';

const WS_URL = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/v1/chat_stream`;

/** Reconnection config */
const MAX_RECONNECT_ATTEMPTS = 5;
const BASE_RECONNECT_DELAY_MS = 1000;

interface UseWebSocketReturn {
  sendQuery: (query: string, history: Message[]) => void;
  connectionStatus: ConnectionStatus;
  streamingContent: string;
  metadata: Record<string, CitationMeta> | null;
  error: string | null;
  agentPhase: AgentPhase;
  isStreaming: boolean;
  resetStream: () => void;
}

/**
 * Custom React hook encapsulating the WebSocket connection lifecycle.
 * Handles connect, reconnect with exponential backoff, query sending,
 * and dispatching incoming chunks to state.
 */
export function useWebSocket(): UseWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [streamingContent, setStreamingContent] = useState('');
  const [metadata, setMetadata] = useState<Record<string, CitationMeta> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [agentPhase, setAgentPhase] = useState<AgentPhase>('idle');
  const [isStreaming, setIsStreaming] = useState(false);

  const resetStream = useCallback(() => {
    setStreamingContent('');
    setMetadata(null);
    setError(null);
    setAgentPhase('idle');
    setIsStreaming(false);
  }, []);

  const connect = useCallback(() => {
    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setConnectionStatus('connecting');
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      setConnectionStatus('connected');
      reconnectAttemptsRef.current = 0;
    };

    ws.onmessage = (event: MessageEvent) => {
      try {
        const chunk: WSChunk = JSON.parse(event.data);

        switch (chunk.type) {
          case 'token':
            // Once we get the first token, we're in the "generating" phase
            if (typeof chunk.content === 'string') {
              setAgentPhase('generating');
              setStreamingContent(prev => prev + chunk.content);
            }
            break;

          case 'metadata':
            setMetadata(chunk.content as Record<string, CitationMeta>);
            setAgentPhase('complete');
            setIsStreaming(false);
            break;

          case 'phase':
            if (typeof chunk.content === 'string') {
              setAgentPhase(chunk.content as AgentPhase);
            }
            break;

          case 'error':
            setError(typeof chunk.content === 'string' ? chunk.content : 'An unknown error occurred.');
            setAgentPhase('error');
            setIsStreaming(false);
            break;
        }
      } catch {
        // Non-JSON message, treat as raw token
        setAgentPhase('generating');
        setStreamingContent(prev => prev + event.data);
      }
    };

    ws.onclose = () => {
      setConnectionStatus('disconnected');
      wsRef.current = null;

      // Attempt reconnection with exponential backoff
      if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
        const delay = BASE_RECONNECT_DELAY_MS * Math.pow(2, reconnectAttemptsRef.current);
        reconnectAttemptsRef.current += 1;
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      }
    };

    ws.onerror = () => {
      // onclose will fire after onerror, handled there
    };

    wsRef.current = ws;
  }, []);

  const sendQuery = useCallback((query: string, history: Message[]) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setError('Not connected to the server. Please wait and try again.');
      return;
    }

    // Reset state for new query
    setStreamingContent('');
    setMetadata(null);
    setError(null);
    setIsStreaming(true);

    // Set an initial starting phase
    setAgentPhase('routing');

    // Send payload as JSON
    const payload = {
      query,
      history: history.map(m => ({
        role: m.role,
        content: m.content
      }))
    };

    wsRef.current.send(JSON.stringify(payload));
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return {
    sendQuery,
    connectionStatus,
    streamingContent,
    metadata,
    error,
    agentPhase,
    isStreaming,
    resetStream,
  };
}
