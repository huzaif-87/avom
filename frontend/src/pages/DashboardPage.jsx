import React, { useState, useEffect, useMemo } from 'react';
import {
  Sparkles,
  ArrowRight,
  FilePlus2,
  Users,
  CheckCircle2,
  Calendar,
  Layers,
  History,
  Eye,
  Trash2,
  Loader2,
} from 'lucide-react';
import ConnectCandidateButton from '../components/ConnectCandidateButton';
import CandidateDetailModal from '../components/CandidateDetailModal';
import ResumeViewerModal from '../components/ResumeViewerModal';
import ConfirmDeleteModal from '../components/ConfirmDeleteModal';
import CandidateStatusBadge from '../components/CandidateStatusBadge';
import {
  listSavedAnalyses,
  deleteSavedAnalysis,
  updateCandidateDecisionStatus,
} from '../services/api';

export default function DashboardPage({
  onStartNewAnalysis,
  onNavigateCandidates,
  onNavigateHistory,
  onNavigateShortlist,
  onOpenAnalysis,
  jdData,
  parsedCandidates = [],
  aiMatchResults = null,
  activeAnalysisId,
  onUpdateCandidateStatus,
}) {
  const [savedAnalyses, setSavedAnalyses] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [viewingResumeCandidate, setViewingResumeCandidate] = useState(null);

  // Load persistent recruiter analyses
  const loadAnalyses = async () => {
    try {
      const data = await listSavedAnalyses();
      setSavedAnalyses(data || []);
    } catch (err) {
      console.warn('Could not load persistent analyses:', err.message);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    loadAnalyses();
  }, [activeAnalysisId]);

  // Aggregate persistent stats across all saved analyses + current working session
  const stats = useMemo(() => {
    let totalAnalyses = savedAnalyses.length;
    let totalCandidates = 0;
    let totalShortlisted = 0;
    let scoreSum = 0;
    let scoreCount = 0;

    savedAnalyses.forEach((a) => {
      totalCandidates += a.candidate_count || 0;
      totalShortlisted += a.shortlisted_count || 0;
      if (a.average_match_score != null) {
        scoreSum += a.average_match_score;
        scoreCount += 1;
      }
    });

    // If working session has candidates not yet saved to a past analysis
    if (totalAnalyses === 0 && parsedCandidates.length > 0) {
      totalAnalyses = 1;
      totalCandidates = parsedCandidates.length;
      totalShortlisted = parsedCandidates.filter((c) => c.status === 'shortlisted').length;
    }

    const avgScore = scoreCount > 0 ? Math.round(scoreSum / scoreCount) : null;

    return {
      totalAnalyses,
      totalCandidates,
      totalShortlisted,
      avgScore,
    };
  }, [savedAnalyses, parsedCandidates]);

  // Handle status update
  const handleStatusChange = async (candidate, newStatus) => {
    if (onUpdateCandidateStatus) {
      await onUpdateCandidateStatus(candidate.candidate_id, newStatus);
    }
    loadAnalyses();
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-12">
      {/* Editorial Welcome Card */}
      <section className="relative overflow-hidden rounded-2xl bg-olive-dark text-white p-7 sm:p-10 shadow-sm border border-olive-darker">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-3 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sage/20 border border-sage/30 text-sage-light text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Persistent Recruiter Workspace Active</span>
            </div>

            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
              Talent Assessment & Candidate Pipeline
            </h2>

            <p className="text-sm text-cream-200/90 leading-relaxed font-normal">
              Screen resumes against target job descriptions with sentence transformer embeddings, multi-factor scoring, and persistent recruiter shortlists stored in MongoDB.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 shrink-0">
            <button
              onClick={onStartNewAnalysis}
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-sage text-charcoal hover:bg-sage-hover text-sm font-semibold transition-all shadow-xs cursor-pointer"
            >
              <FilePlus2 className="w-4 h-4" />
              <span>New Analysis</span>
            </button>

            <button
              onClick={onNavigateHistory}
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-olive text-white border border-olive-dark hover:bg-olive-hover text-sm font-semibold transition-all cursor-pointer"
            >
              <History className="w-4 h-4" />
              <span>Analysis History</span>
            </button>
          </div>
        </div>
      </section>

      {/* 4 Real Persistent Metric Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Analyses */}
        <div className="bg-white rounded-2xl p-5 border border-sage-muted shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-charcoal-muted uppercase tracking-wider">
              Total Analyses
            </span>
            <div className="w-8 h-8 rounded-xl bg-olive-light text-olive-dark flex items-center justify-center">
              <Layers className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-charcoal">{stats.totalAnalyses}</span>
            <span className="text-xs text-charcoal-muted">roles saved</span>
          </div>
        </div>

        {/* Total Candidates */}
        <div className="bg-white rounded-2xl p-5 border border-sage-muted shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-charcoal-muted uppercase tracking-wider">
              Total Candidates
            </span>
            <div className="w-8 h-8 rounded-xl bg-olive-light text-olive-dark flex items-center justify-center">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-charcoal">{stats.totalCandidates}</span>
            <span className="text-xs text-charcoal-muted">profiles parsed</span>
          </div>
        </div>

        {/* Shortlisted Candidates */}
        <div
          onClick={onNavigateShortlist}
          className="bg-white rounded-2xl p-5 border border-sage-muted shadow-2xs cursor-pointer hover:border-olive/60 transition group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-charcoal-muted uppercase tracking-wider group-hover:text-olive-dark transition">
              Shortlisted Talent
            </span>
            <div className="w-8 h-8 rounded-xl bg-olive-light text-olive-dark flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4 text-olive" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-olive-dark">{stats.totalShortlisted}</span>
            <span className="text-xs text-charcoal-muted">ready for outreach &rarr;</span>
          </div>
        </div>

        {/* Average AI Match Score */}
        <div className="bg-white rounded-2xl p-5 border border-sage-muted shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-charcoal-muted uppercase tracking-wider">
              Avg AI Match
            </span>
            <div className="w-8 h-8 rounded-xl bg-olive-light text-olive-dark flex items-center justify-center">
              <Sparkles className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-charcoal">
              {stats.avgScore != null ? `${stats.avgScore}%` : '—'}
            </span>
            <span className="text-xs text-charcoal-muted">across pipelines</span>
          </div>
        </div>
      </div>

      {/* Recent Analyses Section (Session Scope removed per prompt) */}
      <div className="bg-white rounded-2xl border border-sage-muted shadow-2xs overflow-hidden">
        <div className="p-5 border-b border-sage-muted/70 flex items-center justify-between bg-cream-50/60">
          <div>
            <h3 className="text-base font-bold text-charcoal">Recent Job Analyses</h3>
            <p className="text-xs text-charcoal-muted mt-0.5">
              Saved screening workflows in your recruiter workspace
            </p>
          </div>
          {savedAnalyses.length > 0 && (
            <button
              onClick={onNavigateHistory}
              className="text-xs font-semibold text-olive-dark hover:text-charcoal flex items-center gap-1 transition cursor-pointer"
            >
              <span>View all ({savedAnalyses.length})</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="divide-y divide-sage-muted/60">
          {loadingHistory ? (
            <div className="p-10 text-center flex flex-col items-center justify-center">
              <Loader2 className="w-6 h-6 text-olive animate-spin mb-2" />
              <span className="text-xs text-charcoal-muted">Loading saved workspace...</span>
            </div>
          ) : savedAnalyses.length > 0 ? (
            savedAnalyses.slice(0, 5).map((analysis) => {
              const dateStr = analysis.created_at
                ? new Date(analysis.created_at).toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                  })
                : 'Recent';

              return (
                <div
                  key={analysis.id}
                  onClick={() => onOpenAnalysis(analysis.id)}
                  className="p-4 sm:p-5 flex items-center justify-between gap-4 hover:bg-cream-50/50 transition cursor-pointer group"
                >
                  <div className="flex items-center gap-3.5 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-olive-light border border-sage/60 flex items-center justify-center text-olive-dark font-bold text-sm shrink-0">
                      <Layers className="w-5 h-5" />
                    </div>
                    <div className="min-w-0">
                      <h4 className="text-sm font-bold text-charcoal truncate group-hover:text-olive-dark transition">
                        {analysis.job_title || 'Target Position'}
                      </h4>
                      <p className="text-xs text-charcoal-muted truncate mt-0.5 flex items-center gap-2">
                        <span>{dateStr}</span>
                        <span>•</span>
                        <span>{analysis.candidate_count} candidates</span>
                        <span>•</span>
                        <span className="text-olive-dark font-medium">
                          {analysis.shortlisted_count} shortlisted
                        </span>
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    {analysis.average_match_score != null && (
                      <span className="px-2.5 py-1 rounded-xl text-xs font-bold bg-olive-light text-olive-dark border border-sage/60">
                        {analysis.average_match_score}% Avg Match
                      </span>
                    )}

                    <span className="text-xs font-semibold text-olive-dark group-hover:underline flex items-center gap-1">
                      <span>Open</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </span>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="p-10 text-center flex flex-col items-center justify-center">
              <Layers className="w-10 h-10 text-charcoal-muted/50 mb-3" />
              <h4 className="text-sm font-semibold text-charcoal">No saved analyses yet</h4>
              <p className="text-xs text-charcoal-muted max-w-sm mt-1 mb-4">
                Run and save candidate screenings in New Analysis to persist roles and track shortlists.
              </p>
              <button
                onClick={onStartNewAnalysis}
                className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-olive rounded-xl hover:bg-olive-dark transition shadow-xs cursor-pointer"
              >
                <FilePlus2 className="w-3.5 h-3.5" />
                <span>Start New Analysis</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      {selectedCandidate && (
        <CandidateDetailModal
          candidate={selectedCandidate}
          jobTitle={jdData?.analyzedData ? 'Target Position' : ''}
          onClose={() => setSelectedCandidate(null)}
          onOpenViewer={(cand) => setViewingResumeCandidate(cand)}
        />
      )}

      {viewingResumeCandidate && (
        <ResumeViewerModal
          candidate={viewingResumeCandidate}
          isOpen={Boolean(viewingResumeCandidate)}
          onClose={() => setViewingResumeCandidate(null)}
        />
      )}
    </div>
  );
}
