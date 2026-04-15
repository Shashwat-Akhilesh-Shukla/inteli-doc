import type { ConnectionStatus } from '../../types';
import styles from './Header.module.css';

interface HeaderProps {
  connectionStatus: ConnectionStatus;
}

const statusLabels: Record<ConnectionStatus, string> = {
  connected: 'Connected',
  connecting: 'Reconnecting…',
  disconnected: 'Disconnected',
};

export function Header({ connectionStatus }: HeaderProps) {
  return (
    <header className={styles.header} id="header">
      <div className={styles.brand}>
        <div className={styles.logoMark} aria-hidden="true">⚡</div>
        <div className={styles.titleGroup}>
          <h1 className={styles.title}>Intelligent Doc Navigator</h1>
          <span className={styles.subtitle}>Agentic Hybrid RAG System</span>
        </div>
      </div>
      <div className={styles.statusBadge}>
        <span
          className={styles.statusDot}
          data-status={connectionStatus}
          aria-label={`Connection status: ${statusLabels[connectionStatus]}`}
        />
        <span>{statusLabels[connectionStatus]}</span>
      </div>
    </header>
  );
}
