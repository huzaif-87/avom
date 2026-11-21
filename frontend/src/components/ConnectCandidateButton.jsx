import React from 'react';
import { Mail, AlertCircle } from 'lucide-react';
import { openGmailCompose } from '../services/gmailService';

/**
 * Reusable ConnectCandidateButton component
 *
 * Prepares candidate outreach via Gmail.
 * Opens Gmail compose in a new secure tab with pre-filled recruitment details.
 * Disables automatically with an accessible tooltip if candidate email is missing.
 *
 * @param {Object} props
 * @param {Object} props.candidate - Candidate object with name, email, jobTitle, etc.
 * @param {string} [props.size='sm'] - 'sm' | 'md' | 'lg'
 * @param {string} [props.variant='primary'] - 'primary' | 'outline' | 'subtle'
 * @param {string} [props.className] - Additional CSS classes
 * @param {Function} [props.onConnect] - Optional callback after opening compose
 */
export default function ConnectCandidateButton({
  candidate,
  size = 'sm',
  variant = 'primary',
  className = '',
  onConnect,
}) {
  const hasEmail = Boolean(candidate?.email && candidate.email.trim());

  const handleConnect = (e) => {
    e.stopPropagation();
    if (!hasEmail) return;

    const opened = openGmailCompose(candidate);
    if (opened && onConnect) {
      onConnect(candidate);
    }
  };

  // Size styling variants
  const sizeStyles = {
    sm: 'text-xs px-3 py-1.5 gap-1.5 rounded-lg',
    md: 'text-sm px-4 py-2 gap-2 rounded-xl',
    lg: 'text-sm px-5 py-2.5 gap-2.5 rounded-xl font-semibold',
  };

  const iconSizes = {
    sm: 'w-3.5 h-3.5',
    md: 'w-4 h-4',
    lg: 'w-4 h-4',
  };

  // Visual variants matching calm, editorial design
  const variantStyles = {
    primary:
      'bg-olive hover:bg-olive-dark text-white shadow-xs hover:shadow-sm border border-olive-dark/40',
    outline:
      'bg-white hover:bg-cream-100 text-charcoal hover:text-olive-dark border border-sage-muted shadow-2xs',
    subtle:
      'bg-olive-light/60 hover:bg-olive-light text-olive-dark border border-sage-muted/80',
  };

  const disabledStyles =
    'bg-cream-200/60 text-charcoal-muted/60 border border-sage-muted/40 cursor-not-allowed opacity-60 shadow-none hover:bg-cream-200/60 hover:text-charcoal-muted/60 hover:border-sage-muted/40';

  const baseStyles =
    'inline-flex items-center justify-center font-medium transition-all duration-150 select-none focus:outline-hidden focus:ring-2 focus:ring-olive/30';

  const tooltipText = hasEmail
    ? `Compose recruitment email to ${candidate.name || candidate.email}`
    : 'Candidate email is not available';

  return (
    <button
      type="button"
      onClick={handleConnect}
      disabled={!hasEmail}
      title={tooltipText}
      aria-label={tooltipText}
      className={`group relative ${baseStyles} ${sizeStyles[size] || sizeStyles.sm} ${
        hasEmail ? variantStyles[variant] || variantStyles.primary : disabledStyles
      } ${className}`}
    >
      <Mail
        className={`${iconSizes[size] || iconSizes.sm} transition-transform group-hover:scale-105 shrink-0`}
      />
      <span>Connect</span>

      {/* Accessible missing indicator indicator for screen readers */}
      {!hasEmail && (
        <span className="sr-only">(Email missing — connect disabled)</span>
      )}
    </button>
  );
}
