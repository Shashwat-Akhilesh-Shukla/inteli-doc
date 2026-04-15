import type { Message, CitationMeta } from '../../types';
import { CitationChip } from '../CitationChip/CitationChip';
import styles from './ChatMessage.module.css';

interface ChatMessageProps {
  message: Message;
}

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export function ChatMessage({ message }: ChatMessageProps) {
  const { role, content, metadata, timestamp, isStreaming } = message;

  return (
    <div
      className={styles.messageWrapper}
      data-role={role}
      id={`message-${message.id}`}
    >
      <div
        className={styles.bubble}
        data-role={role}
        data-streaming={isStreaming ? 'true' : 'false'}
      >
        <div className={styles.roleLabel}>
          {role === 'user' ? 'You' : 'Navigator'}
        </div>

        <div className={styles.content}>
          {content}
          {isStreaming && <span className={styles.cursor} aria-hidden="true" />}
        </div>

        {/* Citation chips for completed assistant messages */}
        {role === 'assistant' && !isStreaming && metadata && Object.keys(metadata).length > 0 && (
          <div className={styles.citationsRow}>
            {Object.entries(metadata).map(([label, meta]) => (
              <CitationChip
                key={label}
                label={label}
                meta={meta as CitationMeta}
              />
            ))}
          </div>
        )}

        <div className={styles.timestamp}>{formatTime(timestamp)}</div>
      </div>
    </div>
  );
}
