import { useState, useCallback, useRef, useEffect } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { Header } from './components/Header/Header';
import { ChatMessage } from './components/ChatMessage/ChatMessage';
import { ChatInput } from './components/ChatInput/ChatInput';
import { ThoughtProcess } from './components/ThoughtProcess/ThoughtProcess';
import type { Message } from './types';

/* ---- Scoped Layout Styles ---- */
const layoutStyles = {
  main: {
    display: 'flex',
    flex: 1,
    overflow: 'hidden',
    minHeight: 0,
  } as React.CSSProperties,
  chatPanel: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column' as const,
    minWidth: 0,
    overflow: 'hidden',
  } as React.CSSProperties,
  messageArea: {
    flex: 1,
    overflowY: 'auto' as const,
    padding: '24px 0',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '16px',
  } as React.CSSProperties,
  emptyState: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    gap: '16px',
    padding: '48px 24px',
    textAlign: 'center' as const,
    animation: 'fadeIn 0.6s ease-out',
  } as React.CSSProperties,
  emptyIcon: {
    fontSize: '3rem',
    opacity: 0.4,
  } as React.CSSProperties,
  emptyTitle: {
    fontSize: '1.25rem',
    fontWeight: 600,
    color: 'var(--text-primary)',
    margin: 0,
  } as React.CSSProperties,
  emptySubtitle: {
    fontSize: '0.875rem',
    color: 'var(--text-muted)',
    maxWidth: '360px',
    lineHeight: 1.6,
    margin: 0,
  } as React.CSSProperties,
  suggestionsRow: {
    display: 'flex',
    flexWrap: 'wrap' as const,
    gap: '8px',
    marginTop: '8px',
    justifyContent: 'center',
  } as React.CSSProperties,
  suggestionChip: {
    padding: '8px 16px',
    borderRadius: '20px',
    background: 'var(--glass-bg)',
    border: '1px solid var(--glass-border)',
    color: 'var(--text-secondary)',
    fontSize: '0.8rem',
    cursor: 'pointer',
    transition: 'all 250ms cubic-bezier(0.16, 1, 0.3, 1)',
    fontFamily: 'var(--font-sans)',
  } as React.CSSProperties,
};

const SUGGESTIONS = [
  'How do I get started?',
  'Explain the architecture',
  'Troubleshoot connection errors',
];

let messageIdCounter = 0;
function nextId(): string {
  messageIdCounter += 1;
  return `msg-${messageIdCounter}-${Date.now()}`;
}

function App() {
  const {
    sendQuery,
    connectionStatus,
    streamingContent,
    metadata,
    error,
    agentPhase,
    isStreaming,
    resetStream,
  } = useWebSocket();

  const [messages, setMessages] = useState<Message[]>([]);
  const messageAreaRef = useRef<HTMLDivElement>(null);
  const activeAssistantIdRef = useRef<string | null>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (messageAreaRef.current) {
      messageAreaRef.current.scrollTop = messageAreaRef.current.scrollHeight;
    }
  }, [messages, streamingContent]);

  // Update the active assistant message as tokens stream in
  useEffect(() => {
    if (!isStreaming && !streamingContent) return;

    const assistantId = activeAssistantIdRef.current;
    if (!assistantId) return;

    setMessages(prev =>
      prev.map(msg =>
        msg.id === assistantId
          ? { ...msg, content: streamingContent, isStreaming }
          : msg
      )
    );
  }, [streamingContent, isStreaming]);

  // When streaming completes, finalize the message with metadata
  useEffect(() => {
    if (agentPhase !== 'complete' && agentPhase !== 'error') return;

    const assistantId = activeAssistantIdRef.current;
    if (!assistantId) return;

    setMessages(prev =>
      prev.map(msg =>
        msg.id === assistantId
          ? {
              ...msg,
              content: error || streamingContent,
              metadata: metadata ?? undefined,
              isStreaming: false,
            }
          : msg
      )
    );

    activeAssistantIdRef.current = null;
  }, [agentPhase, metadata, error, streamingContent]);

  const handleSend = useCallback((text: string) => {
    const userMsg: Message = {
      id: nextId(),
      role: 'user',
      content: text,
      timestamp: Date.now(),
    };

    const assistantMsg: Message = {
      id: nextId(),
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      isStreaming: true,
    };

    activeAssistantIdRef.current = assistantMsg.id;
    setMessages(prev => [...prev, userMsg, assistantMsg]);

    resetStream();
    sendQuery(text);
  }, [sendQuery, resetStream]);

  const handleSuggestion = (text: string) => {
    handleSend(text);
  };

  const hasMessages = messages.length > 0;

  return (
    <>
      <Header connectionStatus={connectionStatus} />

      <div style={layoutStyles.main}>
        <div style={layoutStyles.chatPanel}>
          <div ref={messageAreaRef} style={layoutStyles.messageArea} id="message-area">
            {!hasMessages ? (
              <div style={layoutStyles.emptyState}>
                <div style={layoutStyles.emptyIcon}>📚</div>
                <h2 style={layoutStyles.emptyTitle}>Intelligent Doc Navigator</h2>
                <p style={layoutStyles.emptySubtitle}>
                  Ask questions about your documentation and get precise, cited answers powered by agentic hybrid retrieval.
                </p>
                <div style={layoutStyles.suggestionsRow}>
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      style={layoutStyles.suggestionChip}
                      onClick={() => handleSuggestion(s)}
                      onMouseEnter={(e) => {
                        (e.target as HTMLButtonElement).style.borderColor = 'rgba(124, 58, 237, 0.4)';
                        (e.target as HTMLButtonElement).style.color = 'var(--text-primary)';
                      }}
                      onMouseLeave={(e) => {
                        (e.target as HTMLButtonElement).style.borderColor = 'var(--glass-border)';
                        (e.target as HTMLButtonElement).style.color = 'var(--text-secondary)';
                      }}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg) => (
                <ChatMessage key={msg.id} message={msg} />
              ))
            )}
          </div>

          <ChatInput
            onSend={handleSend}
            disabled={isStreaming}
          />
        </div>

        <ThoughtProcess phase={agentPhase} />
      </div>
    </>
  );
}

export default App;
