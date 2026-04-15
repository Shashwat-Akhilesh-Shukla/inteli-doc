import { useState } from 'react';
import type { AgentPhase } from '../../types';
import styles from './ThoughtProcess.module.css';

interface ThoughtProcessProps {
  phase: AgentPhase;
}

interface StepDef {
  key: AgentPhase;
  label: string;
  description: string;
  icon: string;
  doneIcon: string;
}

const STEPS: StepDef[] = [
  {
    key: 'routing',
    label: 'Routing',
    description: 'Classifying query intent',
    icon: '🧭',
    doneIcon: '✓',
  },
  {
    key: 'retrieving',
    label: 'Retrieving',
    description: 'Hybrid vector + keyword search',
    icon: '🔍',
    doneIcon: '✓',
  },
  {
    key: 'evaluating',
    label: 'Evaluating',
    description: 'Judging context sufficiency',
    icon: '⚖️',
    doneIcon: '✓',
  },
  {
    key: 'generating',
    label: 'Generating',
    description: 'Streaming LLM response',
    icon: '✨',
    doneIcon: '✓',
  },
];

/** Order index for each phase, used to determine step status */
const PHASE_ORDER: Record<string, number> = {
  idle: -1,
  routing: 0,
  retrieving: 1,
  evaluating: 2,
  generating: 3,
  complete: 4,
  error: 4,
};

function getStepStatus(stepKey: AgentPhase, currentPhase: AgentPhase): 'pending' | 'active' | 'done' | 'error' {
  const stepIdx = PHASE_ORDER[stepKey] ?? -1;
  const currentIdx = PHASE_ORDER[currentPhase] ?? -1;

  if (currentPhase === 'error' && stepIdx === currentIdx) return 'error';
  if (stepIdx < currentIdx) return 'done';
  if (stepIdx === currentIdx) return 'active';
  return 'pending';
}

export function ThoughtProcess({ phase }: ThoughtProcessProps) {
  const [mobileOpen, setMobileOpen] = useState(false);

  const isActive = phase !== 'idle';

  return (
    <aside className={styles.panel} id="thought-process-panel">
      <div className={styles.panelTitle}>
        <span className={styles.panelTitleIcon}>🧠</span>
        Thought Process
      </div>

      {/* Mobile toggle */}
      <button
        className={styles.mobileToggle}
        onClick={() => setMobileOpen(prev => !prev)}
      >
        {mobileOpen ? '▾ Hide Steps' : '▸ Show Steps'}
      </button>

      <div className={styles.mobileWrapper}>
        <div className={styles.mobileContent} data-open={mobileOpen ? 'true' : 'false'}>
          <div className={styles.stepper}>
            {STEPS.map((step) => {
              const status = isActive ? getStepStatus(step.key, phase) : 'pending';

              return (
                <div
                  key={step.key}
                  className={styles.step}
                  data-status={status}
                >
                  <div className={styles.indicator}>
                    {status === 'active' ? (
                      <div className={styles.spinner} />
                    ) : status === 'done' ? (
                      step.doneIcon
                    ) : status === 'error' ? (
                      '✗'
                    ) : (
                      step.icon
                    )}
                  </div>
                  <div className={styles.stepContent}>
                    <div className={styles.stepLabel}>{step.label}</div>
                    <div className={styles.stepDescription}>{step.description}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Bottom info */}
      <div className={styles.infoSection}>
        <div className={styles.infoLabel}>Pipeline</div>
        <div className={styles.infoValue}>
          {phase === 'idle' ? 'Awaiting query' :
           phase === 'complete' ? 'Response delivered' :
           phase === 'error' ? 'Pipeline error' :
           'Processing…'}
        </div>
      </div>
    </aside>
  );
}
