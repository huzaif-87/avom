import React, { useState, useEffect } from 'react';
import {
  History,
  Trash2,
  FolderOpen,
  ArrowRight,
  Sparkles,
  Calendar,
  Users,
  CheckCircle2,
  FilePlus2,
  Loader2,
  AlertTriangle,
} from 'lucide-react';
import { listSavedAnalyses, deleteSavedAnalysis } from '../services/api';

export default function AnalysisHistoryPage({ onOpenAnalysis, onStartNewAnalysis }) {
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  const fetchAnalyses = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listSavedAnalyses();
      setAnalyses(data || []);
    } catch (err) {
      setError(err.message || 'Failed to load analysis history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyses();
  }, []);

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this analysis and all candidate records?')) {
      return;
    }

    setDeletingId(id);
    try {
      await deleteSavedAnalysis(id);
      setAnalyses((prev) => prev.filter((a) => a.id !== id));
    } catch (err) {
      alert(err.message || 'Failed to delete analysis');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-sage-muted/70">
        <div>
          <div className="flex items-center gap-2.5">
            <h2 className="text-xl sm:text-2xl font-bold text-charcoal tracking-tight">
              Analysis History
            </h2>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-cream-200 text-charcoal border border-sage-muted">
              {analyses.length} saved
            </span>
          </div>
          <p className="text-xs text-charcoal-muted mt-0.5">
            Reopen previous role assessments, review shortlisted talent, and track recruitment progress
          </p>
        </div>

        <button
          onClick={onStartNewAnalysis}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-olive hover:bg-olive-dark shadow-xs transition-colors shrink-0 cursor-pointer"
        >
          <FilePlus2 className="w-4 h-4" />
          <span>New Analysis</span>
        </button>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-terracotta-light border border-terracotta/40 text-terracotta-dark text-xs flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="p-16 text-center flex flex-col items-center justify-center bg-white rounded-2xl border border-sage-muted">
          <Loader2 className="w-8 h-8 text-olive animate-spin mb-3" />
          <p className="text-xs text-charcoal-muted font-medium">Loading saved recruiter analyses...</p>
        </div>
      ) : analyses.length === 0 ? (
        <div className="bg-white rounded-2xl border border-sage-muted p-12 text-center shadow-2xs">
          <History className="w-10 h-10 text-charcoal-muted/50 mx-auto mb-3" />
          <h3 className="text-base font-bold text-charcoal">No Saved Analyses Yet</h3>
          <p className="text-xs text-charcoal-muted max-w-md mx-auto mt-1 mb-5">
            Analyses you run will automatically be saved to your persistent workspace so you can reopen them anytime.
          </p>
          <button
            onClick={onStartNewAnalysis}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-olive hover:bg-olive-dark shadow-xs transition cursor-pointer"
          >
            <FilePlus2 className="w-4 h-4" />
            <span>Start First Analysis</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {analyses.map((analysis) => {
            const dateStr = analysis.created_at
              ? new Date(analysis.created_at).toLocaleDateString(undefined, {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                })
              : 'Recent';

            return (
              <div
                key={analysis.id}
                onClick={() => onOpenAnalysis(analysis.id)}
                className="bg-white rounded-2xl border border-sage-muted p-5 shadow-2xs hover:shadow-xs hover:border-olive/60 transition-all cursor-pointer flex flex-col justify-between group"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <h3 className="text-base font-bold text-charcoal group-hover:text-olive-dark transition line-clamp-1">
                      {analysis.job_title || 'Target Position'}
                    </h3>
                    <button
                      type="button"
                      disabled={deletingId === analysis.id}
                      onClick={(e) => handleDelete(e, analysis.id)}
                      className="p-1.5 rounded-lg text-charcoal-muted hover:text-terracotta-dark hover:bg-cream-100 transition"
                      title="Delete this analysis"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  <p className="text-xs text-charcoal-muted line-clamp-2 mb-4 leading-relaxed font-normal">
                    {analysis.jd_analysis?.summary || analysis.jd_text?.slice(0, 140) + '...'}
                  </p>
                </div>

                <div className="pt-4 border-t border-sage-muted/60 space-y-3">
                  {/* Stats Bar */}
                  <div className="flex items-center justify-between text-xs text-charcoal">
                    <div className="flex items-center gap-1.5">
                      <Users className="w-3.5 h-3.5 text-charcoal-muted" />
                      <span>{analysis.candidate_count} Candidates</span>
                    </div>

                    <div className="flex items-center gap-1.5 text-olive-dark font-semibold">
                      <CheckCircle2 className="w-3.5 h-3.5 text-olive" />
                      <span>{analysis.shortlisted_count} Shortlisted</span>
                    </div>

                    {analysis.average_match_score != null && (
                      <div className="px-2 py-0.5 rounded-md bg-olive-light text-olive-dark font-bold text-[11px] border border-sage/60">
                        {analysis.average_match_score}% Avg
                      </div>
                    )}
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-charcoal-muted pt-1">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3 text-charcoal-muted/70" />
                      <span>{dateStr}</span>
                    </span>
                    <span className="text-olive-dark font-semibold group-hover:underline flex items-center gap-1">
                      <span>Open Workspace</span>
                      <ArrowRight className="w-3 h-3" />
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
