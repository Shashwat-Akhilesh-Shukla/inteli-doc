import { useState, useRef, useEffect } from 'react';
import type { CitationMeta } from '../../types';
import styles from './CitationChip.module.css';

interface CitationChipProps {
  label: string;
  meta: CitationMeta;
}

export function CitationChip({ label, meta }: CitationChipProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const chipRef = useRef<HTMLSpanElement>(null);

  // Close tooltip when clicking outside
  useEffect(() => {
    if (!showTooltip) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (chipRef.current && !chipRef.current.contains(e.target as Node)) {
        setShowTooltip(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showTooltip]);

  return (
    <span
      ref={chipRef}
      className={styles.chip}
      onClick={() => setShowTooltip(prev => !prev)}
      role="button"
      tabIndex={0}
      aria-label={`Citation ${label}`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          setShowTooltip(prev => !prev);
        }
      }}
    >
      {label}
      {showTooltip && (
        <div className={styles.tooltip} onClick={(e) => e.stopPropagation()}>
          {meta.source && (
            <>
              <div className={styles.tooltipLabel}>Source</div>
              <div className={styles.tooltipValue}>{meta.source}</div>
            </>
          )}
          {meta.section && (
            <>
              <div className={styles.tooltipLabel}>Section</div>
              <div className={styles.tooltipValue}>{meta.section}</div>
            </>
          )}
          {/* Show any other metadata keys */}
          {Object.entries(meta)
            .filter(([key]) => !['source', 'section', 'page_content'].includes(key))
            .map(([key, value]) => (
              <div key={key}>
                <div className={styles.tooltipLabel}>{key}</div>
                <div className={styles.tooltipValue}>{String(value)}</div>
              </div>
            ))
          }
        </div>
      )}
    </span>
  );
}
