import React from 'react';
import { Check, CheckCircle2, XCircle, HelpCircle, UserCheck } from 'lucide-react';

/**
 * Reusable CandidateStatusPill / Selector
 * Allows recruiters to immediately change candidate status (shortlisted, maybe, rejected, unreviewed).
 */
export default function CandidateStatusBadge({ status, onChange, size = 'sm', disabled = false }) {
  const current = status || 'unreviewed';

  const config = {
    shortlisted: {
      label: 'Shortlisted',
      bg: 'bg-olive-light',
      text: 'text-olive-dark',
      border: 'border-olive/50',
      icon: CheckCircle2,
    },
    maybe: {
      label: 'Maybe',
      bg: 'bg-cream-200',
      text: 'text-charcoal',
      border: 'border-sage',
      icon: HelpCircle,
    },
    rejected: {
      label: 'Rejected',
      bg: 'bg-terracotta-light',
      text: 'text-terracotta-dark',
      border: 'border-terracotta/40',
      icon: XCircle,
    },
    unreviewed: {
      label: 'Unreviewed',
      bg: 'bg-cream-100',
      text: 'text-charcoal-muted',
      border: 'border-sage-muted',
      icon: UserCheck,
    },
  };

  const activeConf = config[current] || config.unreviewed;
  const Icon = activeConf.icon;

  if (!onChange) {
    return (
      <span
        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold border ${activeConf.bg} ${activeConf.text} ${activeConf.border}`}
      >
        <Icon className="w-3 h-3" />
        <span>{activeConf.label}</span>
      </span>
    );
  }

  return (
    <div className="inline-flex items-center p-0.5 rounded-xl bg-cream-50 border border-sage-muted shadow-2xs" onClick={(e) => e.stopPropagation()}>
      {['unreviewed', 'shortlisted', 'maybe', 'rejected'].map((st) => {
        const conf = config[st];
        const isSelected = current === st;
        return (
          <button
            key={st}
            type="button"
            disabled={disabled}
            onClick={() => onChange(st)}
            className={`px-2 py-1 rounded-lg text-[10px] font-bold transition-all cursor-pointer ${
              isSelected
                ? `${conf.bg} ${conf.text} shadow-2xs border ${conf.border}`
                : 'text-charcoal-muted hover:text-charcoal hover:bg-white/80'
            }`}
            title={`Mark candidate as ${conf.label}`}
          >
            {conf.label}
          </button>
        );
      })}
    </div>
  );
}
