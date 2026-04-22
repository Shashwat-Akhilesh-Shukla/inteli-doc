/**
 * Shared TypeScript types for the Intelligent Documentation Navigator frontend.
 */

/** Possible phases in the agentic reasoning pipeline */
export type AgentPhase =
  | 'idle'
  | 'routing'
  | 'retrieving'
  | 'evaluating'
  | 'rewriting'
  | 'generating'
  | 'complete'
  | 'error';

/** WebSocket connection status */
export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected';

/** A single chat message */
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  metadata?: Record<string, CitationMeta>;
  timestamp: number;
  isStreaming?: boolean;
}

/** Metadata attached to a citation reference like [Doc 1] */
export interface CitationMeta {
  source?: string;
  section?: string;
  page_content?: string;
  [key: string]: unknown;
}

/** Shape of a single chunk received over the WebSocket */
export interface WSChunk {
  type: 'token' | 'metadata' | 'error' | 'phase';
  content: string | Record<string, CitationMeta>;
}
