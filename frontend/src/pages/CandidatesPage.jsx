import React, { useState, useMemo } from 'react';
import {
  Users,
  Search,
  Filter,
  Eye,
  FileText,
  AlertTriangle,
  ArrowRight,
  Sparkles,
  FilePlus2,
  Trash2,
  ArrowUpDown,
  Zap,
  CheckCircle2,
  HelpCircle,
  XCircle,
  BookmarkCheck,
} from 'lucide-react';
import ConnectCandidateButton from '../components/ConnectCandidateButton';
import CandidateDetailModal from '../components/CandidateDetailModal';
import ResumeViewerModal from '../components/ResumeViewerModal';
import ConfirmDeleteModal from '../components/ConfirmDeleteModal';
import CandidateStatusBadge from '../components/CandidateStatusBadge';
import { deleteCandidateResume } from '../services/api';

export default function CandidatesPage({
  parsedCandidates = [],
  onStartNewAnalysis,
  jobTitle = '',
  jdData = null,
  aiMatchResults = null,
  onRemoveCandidate,
  onUpdateCandidateStatus,
  filterOnlyShortlisted = false,
  activeAnalysisTitle = '',
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState(filterOnlyShortlisted ? 'shortlisted' : 'all');
  const [sortBy, setSortBy] = useState('match'); // 'match' | 'experience' | 'name'

  // Modals state
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [viewingResumeCandidate, setViewingResumeCandidate] = useState(null);
  const [candidateToDelete, setCandidateToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Map AI Match Results
  const scoredCandidateMap = useMemo(() => {
    const map = new Map();
    if (aiMatchResults?.ranked_candidates) {
      for (const sc of aiMatchResults.ranked_candidates) {
        map.set(sc.candidate_id, sc);
      }
    }
    return map;
  }, [aiMatchResults]);

  // Status counts
  const statusCounts = useMemo(() => {
    const counts = { all: parsedCandidates.length, shortlisted: 0, maybe: 0, rejected: 0, unreviewed: 0 };
    parsedCandidates.forEach((c) => {
      const st = c.status || 'unreviewed';
      if (counts[st] !== undefined) {
        counts[st]++;
      } else {
        counts.unreviewed++;
      }
    });
    return counts;
  }, [parsedCandidates]);

  // Combine and sort
  const displayCandidates = useMemo(() => {
    let list = parsedCandidates.map((candidate) => {
      const scored = scoredCandidateMap.get(candidate.candidate_id) || candidate;
      const profExp = candidate.professional_experience_years ?? candidate.experience_years ?? 0;
      return {
        candidate,
        scored,
        matchScore: scored?.overall_match_score ?? candidate.overall_match_score ?? null,
        rank: scored?.rank ?? candidate.rank ?? null,
        profExpNumeric: typeof profExp === 'number' ? profExp : 0,
        name: candidate.name || '',
        email: candidate.email || '',
        filename: candidate.filename || '',
        skills: candidate.skills || [],
        status: candidate.status || 'unreviewed',
      };
    });

    // Filter by status tab
    if (statusFilter !== 'all') {
      list = list.filter((item) => item.status === statusFilter);
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter((item) => {
        const matchName = item.name.toLowerCase().includes(q);
        const matchEmail = item.email.toLowerCase().includes(q);
        const matchFile = item.filename.toLowerCase().includes(q);
        const matchSkills = item.skills.some((s) => s.toLowerCase().includes(q));
        return matchName || matchEmail || matchFile || matchSkills;
      });
    }

    list.sort((a, b) => {
      if (sortBy === 'match') {
        if (a.matchScore !== null && b.matchScore !== null) {
          if (b.matchScore !== a.matchScore) return b.matchScore - a.matchScore;
          return b.profExpNumeric - a.profExpNumeric;
        }
        if (a.matchScore !== null) return -1;
        if (b.matchScore !== null) return 1;
        return b.profExpNumeric - a.profExpNumeric;
      } else if (sortBy === 'experience') {
        return b.profExpNumeric - a.profExpNumeric;
      } else if (sortBy === 'name') {
        return a.name.localeCompare(b.name);
      }
      return 0;
    });

    return list;
  }, [parsedCandidates, scoredCandidateMap, searchQuery, statusFilter, sortBy]);

  // Delete Candidate Handler
  const handleConfirmDeleteCandidate = async (candidate) => {
    if (!candidate) return;
    setIsDeleting(true);
    try {
      await deleteCandidateResume(candidate.candidate_id);
      if (onRemoveCandidate) {
        onRemoveCandidate(candidate.candidate_id);
      }
      setCandidateToDelete(null);
    } catch (err) {
      console.error('Failed to delete resume:', err);
      if (onRemoveCandidate) {
        onRemoveCandidate(candidate.candidate_id);
      }
      setCandidateToDelete(null);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleStatusChange = async (candidateId, newStatus) => {
    if (onUpdateCandidateStatus) {
      await onUpdateCandidateStatus(candidateId, newStatus);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-sage-muted/70">
        <div>
          <div className="flex items-center gap-2.5">
            <h2 className="text-xl sm:text-2xl font-bold text-charcoal tracking-tight">
              {filterOnlyShortlisted ? 'Shortlisted Candidates' : 'Candidate Directory'}
            </h2>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-cream-200 text-charcoal border border-sage-muted">
              {displayCandidates.length} {filterOnlyShortlisted ? 'shortlisted' : 'in workspace'}
            </span>
          </div>
          <p className="text-xs text-charcoal-muted mt-0.5">
            {activeAnalysisTitle ? `Assessment: ${activeAnalysisTitle}` : 'Evaluated candidate profiles, shortlist decisions, and AI semantic scores'}
          </p>
        </div>

        {parsedCandidates.length > 0 && (
          <div className="flex flex-wrap items-center gap-3">
            {/* Sort Select */}
            <div className="flex items-center gap-1.5 text-xs text-charcoal bg-white border border-sage-muted px-3 py-1.5 rounded-xl shadow-2xs">
              <ArrowUpDown className="w-3.5 h-3.5 text-charcoal-muted" />
              <span className="text-[11px] font-medium text-charcoal-muted">Sort:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="bg-transparent font-semibold text-charcoal focus:outline-hidden text-xs cursor-pointer"
              >
                <option value="match">AI Match Score (High to Low)</option>
                <option value="experience">Experience (High to Low)</option>
                <option value="name">Candidate Name (A-Z)</option>
              </select>
            </div>

            {/* Search Input */}
            <div className="relative">
              <Search className="w-4 h-4 text-charcoal-muted absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search candidates..."
                className="pl-9 pr-4 py-1.5 text-xs rounded-xl border border-sage-muted bg-white focus:outline-hidden focus:ring-2 focus:ring-olive/30 focus:border-olive text-charcoal placeholder:text-charcoal-muted/60 w-48 sm:w-60 transition-all shadow-2xs"
              />
            </div>

            <button
              onClick={onStartNewAnalysis}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-white bg-olive hover:bg-olive-dark shadow-xs transition-colors shrink-0 cursor-pointer"
            >
              <FilePlus2 className="w-3.5 h-3.5" />
              <span>Add More</span>
            </button>
          </div>
        )}
      </div>

      {/* Recruiter Shortlist Decision Filter Tabs */}
      {!filterOnlyShortlisted && parsedCandidates.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          {[
            { id: 'all', label: 'All Candidates', count: statusCounts.all },
            { id: 'shortlisted', label: 'Shortlisted', count: statusCounts.shortlisted, color: 'text-olive-dark font-bold' },
            { id: 'maybe', label: 'Maybe', count: statusCounts.maybe },
            { id: 'rejected', label: 'Rejected', count: statusCounts.rejected },
            { id: 'unreviewed', label: 'Unreviewed', count: statusCounts.unreviewed },
          ].map((tab) => {
            const isActive = statusFilter === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setStatusFilter(tab.id)}
                className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer border ${
                  isActive
                    ? 'bg-olive text-white border-olive-dark shadow-2xs'
                    : 'bg-white text-charcoal border-sage-muted hover:bg-cream-100'
                }`}
              >
                <span>{tab.label}</span>
                <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${isActive ? 'bg-white/20 text-white' : 'bg-cream-200 text-charcoal-muted'}`}>
                  {tab.count}
                </span>
              </button>
            );
          })}
        </div>
      )}

      {/* Empty State when no candidates exist */}
      {parsedCandidates.length === 0 ? (
        <div className="bg-white rounded-2xl border border-sage-muted p-10 sm:p-14 text-center shadow-2xs">
          <div className="max-w-md mx-auto space-y-4">
            <div className="w-13 h-13 rounded-2xl bg-olive-light text-olive-dark mx-auto flex items-center justify-center border border-sage/60 shadow-xs">
              <Users className="w-6 h-6" />
            </div>

            <div>
              <h3 className="text-base font-bold text-charcoal">
                {filterOnlyShortlisted ? 'No Shortlisted Candidates Yet' : 'No candidates evaluated yet'}
              </h3>
              <p className="text-xs sm:text-sm text-charcoal-muted mt-1.5 leading-relaxed">
                {filterOnlyShortlisted
                  ? 'Mark candidates as Shortlisted in Candidates or New Analysis to build your interview queue.'
                  : 'Upload candidate resumes in New Analysis to evaluate skills and make shortlist decisions.'}
              </p>
            </div>

            <div className="pt-2">
              <button
                type="button"
                onClick={onStartNewAnalysis}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-olive hover:bg-olive-dark shadow-xs transition-all cursor-pointer"
              >
                <FilePlus2 className="w-4 h-4" />
                <span>Start New Analysis</span>
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* Candidates Table Card */
        <div className="bg-white rounded-2xl border border-sage-muted shadow-2xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-cream-50 border-b border-sage-muted text-charcoal-muted uppercase tracking-wider font-semibold">
                <tr>
                  <th className="px-6 py-3.5">Candidate</th>
                  <th className="px-6 py-3.5">Decision Status</th>
                  <th className="px-6 py-3.5">AI Match Score</th>
                  <th className="px-6 py-3.5">Experience</th>
                  <th className="px-6 py-3.5">Key Skills</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-sage-muted/60">
                {displayCandidates.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-10 text-center text-charcoal-muted">
                      No candidates match your current filter ({statusFilter}).
                    </td>
                  </tr>
                ) : (
                  displayCandidates.map(({ candidate, scored, matchScore, rank, status }) => (
                    <tr
                      key={candidate.candidate_id}
                      onClick={() => setSelectedCandidate(candidate)}
                      className="hover:bg-cream-50/70 cursor-pointer transition-colors"
                    >
                      {/* Name & Contact */}
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          {rank && (
                            <span className="w-5 h-5 rounded-full bg-cream-200 text-charcoal text-[10px] font-bold flex items-center justify-center shrink-0">
                              #{rank}
                            </span>
                          )}
                          <div className="font-bold text-charcoal text-sm">
                            {candidate.name || 'Unknown'}
                          </div>
                        </div>
                        <div className="text-[11px] text-charcoal-muted mt-0.5 ml-7">
                          {candidate.email || <span className="italic text-charcoal-muted">No email detected</span>}
                        </div>
                        <div className="text-[10px] text-charcoal-muted/70 font-mono mt-0.5 ml-7">
                          {candidate.filename}
                        </div>
                      </td>

                      {/* Immediate Status Selector */}
                      <td className="px-6 py-4" onClick={(e) => e.stopPropagation()}>
                        <CandidateStatusBadge
                          status={status}
                          onChange={(newSt) => handleStatusChange(candidate.candidate_id, newSt)}
                        />
                      </td>

                      {/* AI Match Score on Sage/Olive Scale */}
                      <td className="px-6 py-4">
                        {matchScore !== null ? (
                          <div className="space-y-1">
                            <span
                              className={`px-3 py-1 rounded-xl text-xs font-bold border inline-block shadow-2xs ${
                                matchScore >= 80
                                  ? 'bg-olive-light text-olive-dark border-olive/50'
                                  : matchScore >= 60
                                  ? 'bg-sage-light text-charcoal border-sage'
                                  : matchScore >= 40
                                  ? 'bg-cream-200 text-charcoal-muted border-sage-muted'
                                  : 'bg-terracotta-light text-terracotta-dark border-terracotta/40'
                              }`}
                            >
                              {matchScore}% Match
                            </span>
                            {scored?.semantic_similarity !== undefined && (
                              <div className="text-[10px] text-charcoal-muted font-medium">
                                Semantic: {Math.round(scored.semantic_similarity * 100)}%
                              </div>
                            )}
                          </div>
                        ) : (
                          <span className="text-charcoal-muted italic text-[11px]">
                            Not evaluated
                          </span>
                        )}
                      </td>

                      {/* Experience */}
                      <td className="px-6 py-4">
                        <div className="font-semibold text-charcoal">
                          {candidate.professional_experience_years !== null &&
                          candidate.professional_experience_years !== undefined ? (
                            `${candidate.professional_experience_years} yrs prof. exp`
                          ) : candidate.experience_source === 'fresher_override' ? (
                            <span className="text-olive-dark font-bold">Fresher / Entry Level</span>
                          ) : candidate.experience_years !== null && candidate.experience_years !== undefined ? (
                            `${candidate.experience_years} yrs`
                          ) : (
                            <span className="text-charcoal-muted italic font-normal">Not specified</span>
                          )}
                        </div>
                        {candidate.internship_experience_years && (
                          <div className="text-[10px] text-olive-dark font-medium mt-0.5">
                            +{Math.round(candidate.internship_experience_years * 12)} mos internship
                          </div>
                        )}
                      </td>

                      {/* Skills */}
                      <td className="px-6 py-4 max-w-xs">
                        {candidate.skills && candidate.skills.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {candidate.skills.slice(0, 3).map((skill, sIdx) => (
                              <span
                                key={sIdx}
                                className="px-2 py-0.5 rounded-md bg-cream-100 text-charcoal text-[10px] font-medium border border-sage-muted"
                              >
                                {skill}
                              </span>
                            ))}
                            {candidate.skills.length > 3 && (
                              <span className="text-[10px] text-charcoal-muted font-medium self-center">
                                +{candidate.skills.length - 3}
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-charcoal-muted italic text-[11px]">None detected</span>
                        )}
                      </td>

                      {/* Actions: Details, Resume, Connect, Remove */}
                      <td className="px-6 py-4 text-right">
                        <div
                          className="inline-flex items-center gap-1.5"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <button
                            type="button"
                            onClick={() => setSelectedCandidate(candidate)}
                            className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold text-charcoal bg-white border border-sage-muted hover:bg-cream-100 transition-colors shadow-2xs cursor-pointer"
                          >
                            <Eye className="w-3 h-3 text-charcoal-muted" />
                            <span>Details</span>
                          </button>

                          <button
                            type="button"
                            onClick={() => setViewingResumeCandidate(candidate)}
                            className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold text-olive-dark bg-olive-light border border-sage hover:bg-sage-light transition-colors shadow-2xs cursor-pointer"
                            title="View original uploaded resume"
                          >
                            <FileText className="w-3 h-3" />
                            <span>Resume</span>
                          </button>

                          <ConnectCandidateButton
                            candidate={{
                              ...candidate,
                              jobTitle: jobTitle || candidate.jobTitle,
                            }}
                            size="sm"
                          />

                          <button
                            type="button"
                            onClick={() => setCandidateToDelete(candidate)}
                            className="p-1.5 rounded-lg text-charcoal-muted hover:text-terracotta-dark hover:bg-cream-200 border border-transparent hover:border-sage-muted transition-colors cursor-pointer"
                            title="Remove candidate from analysis"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="p-4 bg-cream-50/50 border-t border-sage-muted/70 text-xs text-charcoal-muted flex items-center justify-between">
            <span>
              Showing {displayCandidates.length} candidate(s)
            </span>
          </div>
        </div>
      )}

      {/* Candidate Detail Modal */}
      {selectedCandidate && (
        <CandidateDetailModal
          candidate={selectedCandidate}
          scoredCandidate={scoredCandidateMap.get(selectedCandidate.candidate_id)}
          jobTitle={jobTitle}
          onClose={() => setSelectedCandidate(null)}
          onOpenViewer={(cand) => setViewingResumeCandidate(cand)}
        />
      )}

      {/* Resume Viewer Modal */}
      {viewingResumeCandidate && (
        <ResumeViewerModal
          candidate={viewingResumeCandidate}
          isOpen={Boolean(viewingResumeCandidate)}
          onClose={() => setViewingResumeCandidate(null)}
        />
      )}

      {/* Confirm Delete Modal */}
      {candidateToDelete && (
        <ConfirmDeleteModal
          candidate={candidateToDelete}
          isOpen={Boolean(candidateToDelete)}
          onClose={() => setCandidateToDelete(null)}
          onConfirm={handleConfirmDeleteCandidate}
          isDeleting={isDeleting}
        />
      )}
    </div>
  );
}
