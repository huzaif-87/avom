import React, { useState, useEffect } from 'react';
import {
  X,
  User,
  Mail,
  Phone,
  FileText,
  Briefcase,
  GraduationCap,
  Sparkles,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  Copy,
  Check,
  Eye,
  Download,
  Calendar,
  Layers,
  Award,
  Zap,
  TrendingUp,
  AlertOctagon,
  HelpCircle,
} from 'lucide-react';
import ConnectCandidateButton from './ConnectCandidateButton';
import { getResumeDownloadUrl } from '../services/api';

export default function CandidateDetailModal({
  candidate,
  scoredCandidate = null,
  jobTitle = '',
  onClose,
  onOpenViewer,
}) {
  const [showRawText, setShowRawText] = useState(false);
  const [showBreakdown, setShowBreakdown] = useState(false);
  const [copiedField, setCopiedField] = useState(null);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!candidate) return null;

  const handleCopy = (text, field) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  // Format experience labels
  const profExp = candidate.professional_experience_years ?? candidate.experience_years;
  const internExp = candidate.internship_experience_years;
  const expSource = candidate.experience_source || 'none';

  // AI Matching properties
  const aiScore = scoredCandidate?.overall_match_score;
  const semanticSim = scoredCandidate?.semantic_similarity;
  const matchedReq = scoredCandidate?.matched_required_skills || [];
  const missingReq = scoredCandidate?.missing_required_skills || [];
  const matchedPref = scoredCandidate?.matched_preferred_skills || [];
  const missingPref = scoredCandidate?.missing_preferred_skills || [];
  const strengths = scoredCandidate?.strengths || [];
  const gaps = scoredCandidate?.gaps || [];
  const explanation = scoredCandidate?.explanation;
  const breakdown = scoredCandidate?.breakdown;

  // Score styling on calm sage/olive scale
  const getScoreTheme = (score) => {
    if (score == null) return { bg: 'bg-cream-200', text: 'text-charcoal-muted', border: 'border-sage-muted' };
    if (score >= 80) return { bg: 'bg-olive-light', text: 'text-olive-dark', border: 'border-olive/50' };
    if (score >= 60) return { bg: 'bg-sage-light', text: 'text-charcoal', border: 'border-sage' };
    if (score >= 40) return { bg: 'bg-cream-200', text: 'text-charcoal-muted', border: 'border-sage-muted' };
    return { bg: 'bg-terracotta-light', text: 'text-terracotta-dark', border: 'border-terracotta/40' };
  };

  const scoreTheme = getScoreTheme(aiScore);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-charcoal/50 backdrop-blur-xs animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-xl border border-sage-muted w-full max-w-3xl max-h-[92vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between px-6 py-5 border-b border-sage-muted/70 bg-cream-50/70">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-olive-light border border-sage/60 flex items-center justify-center text-olive-dark font-bold text-lg shrink-0">
              {candidate.name && candidate.name !== 'Unknown'
                ? candidate.name.charAt(0).toUpperCase()
                : 'C'}
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="text-lg font-bold text-charcoal">
                  {candidate.name || 'Candidate Profile'}
                </h3>
                {scoredCandidate?.rank && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-olive-dark text-white uppercase tracking-wider">
                    Rank #{scoredCandidate.rank}
                  </span>
                )}
              </div>
              <p className="text-xs text-charcoal-muted mt-0.5 flex items-center gap-2">
                <span>{candidate.filename}</span>
                {candidate.file_type && (
                  <span className="uppercase text-[10px] font-semibold bg-cream-200 text-charcoal-muted px-1.5 py-0.5 rounded">
                    {candidate.file_type}
                  </span>
                )}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {onOpenViewer && (
              <button
                type="button"
                onClick={() => onOpenViewer(candidate)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-charcoal bg-white border border-sage-muted rounded-xl hover:bg-cream-100 hover:text-olive-dark transition shadow-2xs"
                title="View original uploaded resume"
              >
                <Eye className="w-3.5 h-3.5" />
                <span>View Original</span>
              </button>
            )}

            <ConnectCandidateButton
              candidate={{ ...candidate, jobTitle }}
              size="sm"
              variant="primary"
            />

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-charcoal-muted hover:text-charcoal hover:bg-cream-100 transition"
              title="Close modal"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* AI Matching Summary Card */}
          {aiScore != null && (
            <div className={`p-4 rounded-xl border ${scoreTheme.border} ${scoreTheme.bg}`}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-olive-dark" />
                  <span className="text-xs font-bold uppercase tracking-wider text-charcoal">
                    Stage 3 AI Match Evaluation
                  </span>
                </div>
                <div className="flex items-baseline gap-1">
                  <span className="text-2xl font-extrabold text-charcoal">{aiScore}</span>
                  <span className="text-xs font-medium text-charcoal-muted">/100</span>
                </div>
              </div>

              {explanation && (
                <p className="text-xs text-charcoal leading-relaxed mb-3 font-normal">
                  {explanation}
                </p>
              )}

              {/* 5-Factor Score Pill Grid */}
              {breakdown && (
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-3 border-t border-sage-muted/50 text-center">
                  <div className="bg-white/80 p-2 rounded-lg border border-sage-muted/40">
                    <div className="text-[10px] text-charcoal-muted font-medium">Semantic (35%)</div>
                    <div className="text-xs font-bold text-charcoal mt-0.5">
                      {Math.round(breakdown.semantic_similarity?.weighted_points || 0)} pts
                    </div>
                  </div>
                  <div className="bg-white/80 p-2 rounded-lg border border-sage-muted/40">
                    <div className="text-[10px] text-charcoal-muted font-medium">Req Skills (30%)</div>
                    <div className="text-xs font-bold text-charcoal mt-0.5">
                      {Math.round(breakdown.required_skills?.weighted_points || 0)} pts
                    </div>
                  </div>
                  <div className="bg-white/80 p-2 rounded-lg border border-sage-muted/40">
                    <div className="text-[10px] text-charcoal-muted font-medium">Experience (20%)</div>
                    <div className="text-xs font-bold text-charcoal mt-0.5">
                      {Math.round(breakdown.experience?.weighted_points || 0)} pts
                    </div>
                  </div>
                  <div className="bg-white/80 p-2 rounded-lg border border-sage-muted/40">
                    <div className="text-[10px] text-charcoal-muted font-medium">Education (10%)</div>
                    <div className="text-xs font-bold text-charcoal mt-0.5">
                      {Math.round(breakdown.education?.weighted_points || 0)} pts
                    </div>
                  </div>
                  <div className="bg-white/80 p-2 rounded-lg border border-sage-muted/40">
                    <div className="text-[10px] text-charcoal-muted font-medium">Pref Skills (5%)</div>
                    <div className="text-xs font-bold text-charcoal mt-0.5">
                      {Math.round(breakdown.preferred_skills?.weighted_points || 0)} pts
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Strengths & Gaps */}
          {(strengths.length > 0 || gaps.length > 0) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {strengths.length > 0 && (
                <div className="p-3.5 rounded-xl bg-olive-light/40 border border-sage-muted">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-olive-dark mb-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-olive" />
                    <span>Key Strengths</span>
                  </div>
                  <ul className="space-y-1 text-xs text-charcoal">
                    {strengths.map((str, idx) => (
                      <li key={idx} className="flex items-start gap-1.5">
                        <span className="text-olive font-bold">•</span>
                        <span>{str}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {gaps.length > 0 && (
                <div className="p-3.5 rounded-xl bg-cream-50 border border-sage-muted">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-charcoal mb-2">
                    <AlertTriangle className="w-3.5 h-3.5 text-terracotta" />
                    <span>Identified Gaps & Missing Criteria</span>
                  </div>
                  <ul className="space-y-1 text-xs text-charcoal-muted">
                    {gaps.map((gap, idx) => (
                      <li key={idx} className="flex items-start gap-1.5">
                        <span className="text-terracotta font-bold">•</span>
                        <span>{gap}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Contact Details */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-3 rounded-xl bg-cream-50 border border-sage-muted flex items-center justify-between">
              <div className="flex items-center gap-2.5 min-w-0">
                <Mail className="w-4 h-4 text-olive-dark shrink-0" />
                <div className="min-w-0">
                  <div className="text-[10px] text-charcoal-muted font-medium uppercase tracking-wider">Email</div>
                  <div className="text-xs font-semibold text-charcoal truncate">
                    {candidate.email || 'Not detected'}
                  </div>
                </div>
              </div>
              {candidate.email && (
                <button
                  type="button"
                  onClick={() => handleCopy(candidate.email, 'email')}
                  className="p-1 rounded text-charcoal-muted hover:text-charcoal transition"
                  title="Copy email"
                >
                  {copiedField === 'email' ? (
                    <Check className="w-3.5 h-3.5 text-olive" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                </button>
              )}
            </div>

            <div className="p-3 rounded-xl bg-cream-50 border border-sage-muted flex items-center justify-between">
              <div className="flex items-center gap-2.5 min-w-0">
                <Phone className="w-4 h-4 text-olive-dark shrink-0" />
                <div className="min-w-0">
                  <div className="text-[10px] text-charcoal-muted font-medium uppercase tracking-wider">Phone</div>
                  <div className="text-xs font-semibold text-charcoal truncate">
                    {candidate.phone || 'Not detected'}
                  </div>
                </div>
              </div>
              {candidate.phone && (
                <button
                  type="button"
                  onClick={() => handleCopy(candidate.phone, 'phone')}
                  className="p-1 rounded text-charcoal-muted hover:text-charcoal transition"
                  title="Copy phone"
                >
                  {copiedField === 'phone' ? (
                    <Check className="w-3.5 h-3.5 text-olive" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                </button>
              )}
            </div>
          </div>

          {/* Experience & Education */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-3.5 rounded-xl bg-white border border-sage-muted">
              <div className="flex items-center gap-2 text-xs font-bold text-charcoal mb-2">
                <Briefcase className="w-4 h-4 text-olive-dark" />
                <span>Professional Experience</span>
              </div>
              <div className="space-y-1">
                <div className="text-sm font-semibold text-charcoal">
                  {profExp != null
                    ? profExp === 0
                      ? 'Fresher / 0 years'
                      : `${profExp} year${profExp === 1 ? '' : 's'}`
                    : 'Not specified'}
                </div>
                {internExp != null && internExp > 0 && (
                  <div className="text-xs text-charcoal-muted">
                    + {internExp} year{internExp === 1 ? '' : 's'} internship
                  </div>
                )}
                {candidate.experience_details && candidate.experience_details.length > 0 && (
                  <div className="text-[11px] text-charcoal-muted mt-2 border-t border-sage-muted/50 pt-2 space-y-1">
                    {candidate.experience_details.slice(0, 3).map((exp, i) => (
                      <div key={i} className="truncate">• {exp}</div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-white border border-sage-muted">
              <div className="flex items-center gap-2 text-xs font-bold text-charcoal mb-2">
                <GraduationCap className="w-4 h-4 text-olive-dark" />
                <span>Education</span>
              </div>
              <div className="space-y-1">
                {candidate.education && candidate.education.length > 0 ? (
                  <ul className="text-xs text-charcoal space-y-1">
                    {candidate.education.map((edu, idx) => (
                      <li key={idx} className="flex items-start gap-1.5">
                        <span className="text-olive font-bold">•</span>
                        <span>{edu}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-xs text-charcoal-muted">No education records detected</div>
                )}
              </div>
            </div>
          </div>

          {/* Extracted Skills */}
          <div className="p-3.5 rounded-xl bg-white border border-sage-muted">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 text-xs font-bold text-charcoal">
                <Award className="w-4 h-4 text-olive-dark" />
                <span>Extracted Skills ({candidate.skills ? candidate.skills.length : 0})</span>
              </div>
            </div>
            {candidate.skills && candidate.skills.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {candidate.skills.map((skill, idx) => {
                  const isReq = matchedReq.some((s) => s.toLowerCase() === skill.toLowerCase());
                  const isPref = matchedPref.some((s) => s.toLowerCase() === skill.toLowerCase());
                  return (
                    <span
                      key={idx}
                      className={`px-2.5 py-1 rounded-lg text-xs font-medium border ${
                        isReq
                          ? 'bg-olive-light text-olive-dark border-olive/40 font-semibold'
                          : isPref
                          ? 'bg-sage-light text-charcoal border-sage'
                          : 'bg-cream-100 text-charcoal border-sage-muted/70'
                      }`}
                    >
                      {skill}
                      {isReq && <span className="ml-1 text-[10px] text-olive font-bold">✓</span>}
                    </span>
                  );
                })}
              </div>
            ) : (
              <div className="text-xs text-charcoal-muted">No skills detected</div>
            )}
          </div>

          {/* Raw Text Accordion */}
          <div className="border border-sage-muted rounded-xl overflow-hidden bg-white">
            <button
              type="button"
              onClick={() => setShowRawText(!showRawText)}
              className="w-full px-4 py-2.5 text-xs font-semibold text-charcoal bg-cream-50 flex items-center justify-between hover:bg-cream-100 transition"
            >
              <div className="flex items-center gap-2">
                <FileText className="w-3.5 h-3.5 text-charcoal-muted" />
                <span>Extracted Resume Text ({candidate.raw_text ? candidate.raw_text.length : 0} chars)</span>
              </div>
              {showRawText ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
            {showRawText && (
              <div className="p-4 bg-cream-100/50 max-h-60 overflow-y-auto text-xs font-mono text-charcoal whitespace-pre-wrap leading-relaxed border-t border-sage-muted">
                {candidate.raw_text || 'No raw text available.'}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-sage-muted/70 bg-cream-50/70 flex items-center justify-between">
          <div className="text-xs text-charcoal-muted">
            Candidate ID: <span className="font-mono text-charcoal">{candidate.candidate_id}</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-charcoal bg-white border border-sage-muted rounded-xl hover:bg-cream-100 transition shadow-2xs"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
