import React from 'react';
import { AlertTriangle, Trash2, X } from 'lucide-react';

export default function ConfirmDeleteModal({ candidate, isOpen, onClose, onConfirm, isDeleting }) {
  if (!isOpen || !candidate) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-charcoal/50 backdrop-blur-xs animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-xl border border-sage-muted w-full max-w-md p-6 overflow-hidden animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start gap-4">
          <div className="w-11 h-11 rounded-xl bg-terracotta-light border border-terracotta/30 flex items-center justify-center text-terracotta-dark shrink-0">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-base font-bold text-charcoal">
              Remove Candidate?
            </h3>
            <p className="text-xs text-charcoal-muted mt-1 leading-relaxed">
              Are you sure you want to remove{' '}
              <span className="font-semibold text-charcoal">
                {candidate.name && candidate.name !== 'Unknown'
                  ? candidate.name
                  : candidate.filename}
              </span>{' '}
              from the current analysis?
            </p>
            <p className="text-[11px] text-charcoal-muted mt-2.5 bg-cream-50 p-2.5 rounded-lg border border-sage-muted/70">
              This will remove the candidate from your working list and clear their cached resume file from the session vault.
            </p>
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-sage-muted/60">
          <button
            type="button"
            onClick={onClose}
            disabled={isDeleting}
            className="px-4 py-2 text-xs font-semibold text-charcoal bg-white border border-sage-muted rounded-xl hover:bg-cream-100 transition disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => onConfirm(candidate)}
            disabled={isDeleting}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-terracotta-dark hover:bg-terracotta rounded-xl shadow-xs transition disabled:opacity-50"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>{isDeleting ? 'Removing...' : 'Remove Candidate'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
