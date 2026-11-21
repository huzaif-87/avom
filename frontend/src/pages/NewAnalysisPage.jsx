import React, { useState, useRef, useMemo, useEffect } from 'react';
import {
  FileText,
  UploadCloud,
  ArrowLeft,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Trash2,
  X,
  File,
  Eye,
  Briefcase,
  GraduationCap,
  Layers,
  RotateCcw,
  Info,
  ArrowUpDown,
  Download,
  Zap,
  Award,
  HelpCircle,
  Save,
} from 'lucide-react';
import ConnectCandidateButton from '../components/ConnectCandidateButton';
import CandidateDetailModal from '../components/CandidateDetailModal';
import ResumeViewerModal from '../components/ResumeViewerModal';
import ConfirmDeleteModal from '../components/ConfirmDeleteModal';
import CandidateStatusBadge from '../components/CandidateStatusBadge';
import {
  analyzeJobDescription,
  parseResumes,
  deleteCandidateResume,
  evaluateAIMatching,
  saveJobAnalysis,
} from '../services/api';

const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10MB
const ALLOWED_EXTENSIONS = ['.pdf', '.docx'];

export default function NewAnalysisPage({
  onBackToDashboard,
  onNavigateCandidates,
  jdData,
  onUpdateJDData,
  parsedCandidates = [],
  onUpdateParsedCandidates,
  batchSummary,
  onClearSession,
  onRemoveCandidate,
  aiMatchResults,
  onUpdateAiMatchResults,
  isAiMatching,
  setIsAiMatching,
  aiMatchError,
  setAiMatchError,
  onUpdateCandidateStatus,
  activeAnalysisId,
  setActiveAnalysisId,
}) {
  // --- JD Analysis State ---
  const [jdText, setJdText] = useState(jdData?.text || '');
  const [isAnalyzingJD, setIsAnalyzingJD] = useState(false);
  const [jdError, setJdError] = useState(null);

  // --- Saving State ---
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccessNotice, setSaveSuccessNotice] = useState(null);
  const [saveErrorNotice, setSaveErrorNotice] = useState(null);


  // --- Resume Upload State ---
  const [stagedFiles, setStagedFiles] = useState([]);
  const [isParsingResumes, setIsParsingResumes] = useState(false);
  const [resumeError, setResumeError] = useState(null);
  const [uploadNotice, setUploadNotice] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  // --- Sorting & Controls ---
  const [sortBy, setSortBy] = useState('match'); // 'match' | 'experience' | 'name'

  // --- Modals State ---
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [viewingResumeCandidate, setViewingResumeCandidate] = useState(null);
  const [candidateToDelete, setCandidateToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Format file size
  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // Sync jdText if parent updates jdData
  useEffect(() => {
    if (jdData?.text && !jdText) {
      setJdText(jdData.text);
    }
  }, [jdData]);

  // -----------------------------------------------------------
  // JD Analysis Submission
  // -----------------------------------------------------------
  const handleAnalyzeJD = async () => {
    if (!jdText.trim()) {
      setJdError('Please enter a job description before analyzing.');
      return;
    }

    setIsAnalyzingJD(true);
    setJdError(null);

    try {
      const analyzedResult = await analyzeJobDescription(jdText);
      onUpdateJDData({
        text: jdText,
        analyzedData: analyzedResult,
      });
    } catch (err) {
      setJdError(err.message || 'Failed to analyze job description.');
    } finally {
      setIsAnalyzingJD(false);
    }
  };

  const handleClearJD = () => {
    setJdText('');
    setJdError(null);
    onUpdateJDData(null);
  };

  // -----------------------------------------------------------
  // Resume Staging & File Validation
  // -----------------------------------------------------------
  const handleValidateAndAddFiles = (incomingFiles) => {
    setUploadNotice(null);
    setResumeError(null);
    const validFiles = [];
    const rejectedFiles = [];

    Array.from(incomingFiles).forEach((file) => {
      const ext = '.' + file.name.split('.').pop().toLowerCase();
      if (!ALLOWED_EXTENSIONS.includes(ext)) {
        rejectedFiles.push(`${file.name} (unsupported file format: ${ext})`);
        return;
      }
      if (file.size > MAX_FILE_SIZE_BYTES) {
        rejectedFiles.push(`${file.name} (exceeds 10MB limit: ${formatFileSize(file.size)})`);
        return;
      }
      // Check duplicate against staged
      const alreadyStaged = stagedFiles.some(
        (sf) => sf.name === file.name && sf.size === file.size
      );
      if (alreadyStaged) {
        rejectedFiles.push(`${file.name} (already staged for upload)`);
        return;
      }
      validFiles.push(file);
    });

    if (rejectedFiles.length > 0) {
      setUploadNotice(`Ignored ${rejectedFiles.length} file(s): ${rejectedFiles.join(', ')}`);
    }

    if (validFiles.length > 0) {
      setStagedFiles((prev) => [...prev, ...validFiles]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleValidateAndAddFiles(e.target.files);
    }
    e.target.value = '';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleValidateAndAddFiles(e.dataTransfer.files);
    }
  };

  const handleRemoveStagedFile = (idx) => {
    setStagedFiles((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleClearStagedFiles = () => {
    setStagedFiles([]);
    setUploadNotice(null);
    setResumeError(null);
  };

  // -----------------------------------------------------------
  // Parse Resumes Submission
  // -----------------------------------------------------------
  const handleParseResumes = async () => {
    if (stagedFiles.length === 0) return;
    setIsParsingResumes(true);
    setResumeError(null);

    try {
      const responseData = await parseResumes(stagedFiles);
      const newResults = responseData.results || [];
      onUpdateParsedCandidates(newResults, {
        total_files: responseData.total_files || stagedFiles.length,
        successful: responseData.successful || 0,
        failed: responseData.failed || 0,
      });
      setStagedFiles([]);
    } catch (err) {
      setResumeError(err.message || 'Failed to parse uploaded resumes.');
    } finally {
      setIsParsingResumes(false);
    }
  };

  // Persist / Save to Recruiter Workspace in MongoDB
  const handleSaveToWorkspace = async () => {
    if (!jdData?.analyzedData && !jdText.trim()) {
      setSaveErrorNotice('A job description is required to save an analysis.');
      return;
    }

    setIsSaving(true);
    setSaveSuccessNotice(null);
    setSaveErrorNotice(null);

    try {
      const payload = {
        analysis_id: activeAnalysisId || undefined,
        job_title: jdData?.analyzedData?.summary?.slice(0, 50) || 'Target Role Assessment',
        jd_text: jdText,
        jd_analysis: jdData?.analyzedData || { summary: jdText.slice(0, 100) },
        candidates: parsedCandidates,
        ai_matching_results: aiMatchResults || undefined,
      };

      const saved = await saveJobAnalysis(payload);
      if (setActiveAnalysisId) {
        setActiveAnalysisId(saved.id);
      }
      localStorage.setItem('talentrank_last_analysis_id', saved.id);
      setSaveSuccessNotice('Analysis and candidates saved to persistent recruiter workspace!');
      setTimeout(() => setSaveSuccessNotice(null), 4000);
    } catch (err) {
      setSaveErrorNotice(err.message || 'Failed to save analysis');
    } finally {
      setIsSaving(false);
    }
  };

  // Auto-save whenever AI matching completes with candidates
  useEffect(() => {
    if (aiMatchResults?.ranked_candidates?.length > 0 && jdData?.analyzedData) {
      handleSaveToWorkspace();
    }
  }, [aiMatchResults]);

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

  // -----------------------------------------------------------
  // Trigger Stage 3 AI Matching Engine
  // -----------------------------------------------------------
  const handleRunAIMatching = async () => {
    if (!parsedCandidates || parsedCandidates.length === 0) return;
    if (!jdData?.analyzedData && !jdText.trim()) {
      setAiMatchError('Please provide and analyze a job description first before running AI matching.');
      return;
    }

    setIsAiMatching(true);
    setAiMatchError(null);

    try {
      const result = await evaluateAIMatching({
        jdText: jdText.trim() || undefined,
        jdAnalysis: jdData?.analyzedData || undefined,
        candidates: parsedCandidates,
      });
      onUpdateAiMatchResults(result);
    } catch (err) {
      setAiMatchError(err.message || 'Failed to execute AI matching evaluation.');
    } finally {
      setIsAiMatching(false);
    }
  };

  // Auto-trigger Stage 3 AI matching once both JD and parsed resumes are present and not yet matched
  useEffect(() => {
    if (
      jdData?.analyzedData &&
      parsedCandidates.length > 0 &&
      !aiMatchResults &&
      !isAiMatching
    ) {
      handleRunAIMatching();
    }
  }, [jdData?.analyzedData, parsedCandidates.length]);

  // -----------------------------------------------------------
  // Scored Map & Sorting Helpers
  // -----------------------------------------------------------
  const scoredCandidateMap = useMemo(() => {
    const map = new Map();
    if (aiMatchResults?.ranked_candidates) {
      for (const sc of aiMatchResults.ranked_candidates) {
        map.set(sc.candidate_id, sc);
      }
    }
    return map;
  }, [aiMatchResults]);

  const displayCandidates = useMemo(() => {
    const list = parsedCandidates.map((candidate) => {
      const scored = scoredCandidateMap.get(candidate.candidate_id);
      const profExp = candidate.professional_experience_years ?? candidate.experience_years ?? 0;
      return {
        candidate,
        scored,
        matchScore: scored?.overall_match_score ?? null,
        rank: scored?.rank ?? null,
        profExpNumeric: typeof profExp === 'number' ? profExp : 0,
        name: candidate.name || '',
      };
    });

    list.sort((a, b) => {
      if (sortBy === 'match') {
        if (a.matchScore !== null && b.matchScore !== null) {
          return b.matchScore - a.matchScore;
        }
        if (a.matchScore !== null) return -1;
        if (b.matchScore !== null) return 1;
        return b.profExpNumeric - a.profExpNumeric;
      }
      if (sortBy === 'experience') {
        return b.profExpNumeric - a.profExpNumeric;
      }
      if (sortBy === 'name') {
        return a.name.localeCompare(b.name);
      }
      return 0;
    });

    return list;
  }, [parsedCandidates, scoredCandidateMap, sortBy]);

  const hasAnalyzedJD = Boolean(jdData?.analyzedData);
  const hasParsedResumes = parsedCandidates.length > 0;
  const hasAIMatches = Boolean(aiMatchResults?.ranked_candidates?.length);

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-16">
      {/* Editorial Navigation Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-sage-muted/70">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onBackToDashboard}
            className="p-2 rounded-xl text-charcoal-muted hover:text-charcoal hover:bg-cream-200 transition-colors shadow-2xs cursor-pointer border border-sage-muted/60"
            title="Return to Dashboard"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-charcoal">
              New Candidate Screening
            </h2>
            <p className="text-xs text-charcoal-muted mt-0.5">
              Target requirements, bulk resume extraction, and transformer matching
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {hasParsedResumes && (
            <button
              type="button"
              onClick={handleSaveToWorkspace}
              disabled={isSaving}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-white bg-olive hover:bg-olive-dark transition-colors shadow-2xs cursor-pointer"
              title="Save to Recruiter MongoDB Workspace"
            >
              {isSaving ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Save className="w-3.5 h-3.5" />
                  <span>Save to Workspace</span>
                </>
              )}
            </button>
          )}

          {hasParsedResumes && (
            <button
              type="button"
              onClick={onNavigateCandidates}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-charcoal bg-white border border-sage-muted hover:bg-cream-100 transition-colors shadow-2xs cursor-pointer"
            >
              <span>View Candidates ({parsedCandidates.length})</span>
            </button>
          )}

          {(hasAnalyzedJD || hasParsedResumes) && (
            <button
              type="button"
              onClick={onClearSession}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium text-terracotta-dark hover:text-charcoal hover:bg-cream-100 transition-colors cursor-pointer"
              title="Clear all session data"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset Session</span>
            </button>
          )}
        </div>
      </div>

      {/* Save feedback notices */}
      {saveSuccessNotice && (
        <div className="p-3.5 rounded-xl bg-olive-light border border-sage text-olive-dark text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-olive" />
          <span>{saveSuccessNotice}</span>
        </div>
      )}

      {saveErrorNotice && (
        <div className="p-3.5 rounded-xl bg-terracotta-light border border-terracotta/40 text-terracotta-dark text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-terracotta-dark" />
          <span>{saveErrorNotice}</span>
        </div>
      )}

      {/* Guided Progress Bar: Steps 1, 2, 3 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Step 1: Job Description */}
        <div
          className={`p-4 rounded-xl border transition-all ${
            hasAnalyzedJD
              ? 'bg-olive-light/50 border-olive/40 text-charcoal'
              : 'bg-white border-sage-muted text-charcoal shadow-2xs'
          }`}
        >
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[11px] font-bold uppercase tracking-wider text-charcoal-muted">
              Step 1
            </span>
            {hasAnalyzedJD ? (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-olive-dark bg-olive-light px-2 py-0.5 rounded-full border border-sage">
                <CheckCircle2 className="w-3 h-3 text-olive" />
                JD Configured
              </span>
            ) : (
              <span className="text-[11px] font-semibold text-charcoal-muted bg-cream-200 px-2 py-0.5 rounded-full">
                Required
              </span>
            )}
          </div>
          <h3 className="text-sm font-bold text-charcoal">Job Description</h3>
          <p className="text-xs text-charcoal-muted mt-0.5">
            {hasAnalyzedJD
              ? `${jdData.analyzedData.extracted_skills?.length || 0} skills extracted`
              : 'Paste and analyze job requirements'}
          </p>
        </div>

        {/* Step 2: Batch Upload */}
        <div
          className={`p-4 rounded-xl border transition-all ${
            hasParsedResumes
              ? 'bg-olive-light/50 border-olive/40 text-charcoal'
              : hasAnalyzedJD
              ? 'bg-cream-50 border-sage text-charcoal'
              : 'bg-white border-sage-muted text-charcoal shadow-2xs opacity-80'
          }`}
        >
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[11px] font-bold uppercase tracking-wider text-charcoal-muted">
              Step 2
            </span>
            {hasParsedResumes ? (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-olive-dark bg-olive-light px-2 py-0.5 rounded-full border border-sage">
                <CheckCircle2 className="w-3 h-3 text-olive" />
                {parsedCandidates.length} Parsed
              </span>
            ) : (
              <span className="text-[11px] font-semibold text-charcoal-muted bg-cream-200 px-2 py-0.5 rounded-full">
                Batch Upload
              </span>
            )}
          </div>
          <h3 className="text-sm font-bold text-charcoal">Upload Resumes</h3>
          <p className="text-xs text-charcoal-muted mt-0.5">
            {hasParsedResumes
              ? 'Stored securely in session vault'
              : 'Drop PDF/DOCX applicant files'}
          </p>
        </div>

        {/* Step 3: AI Matching Engine */}
        <div
          className={`p-4 rounded-xl border transition-all ${
            hasAIMatches
              ? 'bg-olive text-white shadow-xs border-olive-dark'
              : hasParsedResumes && hasAnalyzedJD
              ? 'bg-cream-50 border-sage text-charcoal'
              : 'bg-white border-sage-muted text-charcoal shadow-2xs opacity-70'
          }`}
        >
          <div className="flex items-center justify-between mb-1.5">
            <span className={`text-[11px] font-bold uppercase tracking-wider ${hasAIMatches ? 'text-cream-200' : 'text-charcoal-muted'}`}>
              Step 3
            </span>
            <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
              hasAIMatches
                ? 'bg-sage text-charcoal font-bold'
                : 'bg-cream-200 text-charcoal-muted'
            }`}>
              {hasAIMatches ? 'AI Match Ready' : 'AI Engine'}
            </span>
          </div>
          <h3 className={`text-sm font-bold ${hasAIMatches ? 'text-white' : 'text-charcoal'}`}>
            AI Match & Ranking
          </h3>
          <p className={`text-xs mt-0.5 ${hasAIMatches ? 'text-cream-200' : 'text-charcoal-muted'}`}>
            {hasAIMatches
              ? 'Semantic vectors & weighted scoring active'
              : 'Embeddings & multi-factor evaluation'}
          </p>
        </div>
      </div>

      {/* SECTION 1: JOB DESCRIPTION INPUT */}
      <section className="bg-white rounded-2xl border border-sage-muted p-6 shadow-2xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-olive-light text-olive-dark flex items-center justify-center font-bold text-xs">
              1
            </div>
            <div>
              <h3 className="text-base font-bold text-charcoal">Job Description</h3>
              <p className="text-xs text-charcoal-muted">
                Paste the role criteria to extract required skills, experience thresholds, and education
              </p>
            </div>
          </div>

          {jdText && (
            <button
              type="button"
              onClick={handleClearJD}
              className="text-xs text-charcoal-muted hover:text-charcoal font-medium cursor-pointer"
            >
              Clear
            </button>
          )}
        </div>

        <div className="relative">
          <textarea
            rows={6}
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            placeholder="Paste complete job description here (e.g., Senior Full-Stack Developer: Looking for 4+ years experience with React, Python, FastAPI, and PostgreSQL...)"
            className="w-full text-xs sm:text-sm p-4 rounded-xl border border-sage-muted bg-cream-50/50 focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-olive/30 focus:border-olive text-charcoal placeholder:text-charcoal-muted/60 transition-all font-mono leading-relaxed"
          />
          <div className="absolute right-3 bottom-3 text-[10px] text-charcoal-muted bg-white/80 px-2 py-0.5 rounded backdrop-blur-xs border border-sage-muted/60">
            {jdText.length} characters
          </div>
        </div>

        {jdError && (
          <div className="p-3.5 rounded-xl bg-terracotta-light border border-terracotta/40 text-terracotta-dark text-xs flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-terracotta-dark shrink-0 mt-0.5" />
            <span>{jdError}</span>
          </div>
        )}

        <div className="flex items-center justify-between pt-1">
          <span className="text-xs text-charcoal-muted">
            {hasAnalyzedJD ? 'Criteria analyzed and cached for semantic matching.' : 'Click below to extract requirements.'}
          </span>

          <button
            type="button"
            onClick={handleAnalyzeJD}
            disabled={!jdText.trim() || isAnalyzingJD}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-olive hover:bg-olive-dark disabled:bg-cream-200 disabled:text-charcoal-muted/60 disabled:cursor-not-allowed shadow-xs transition-all cursor-pointer"
          >
            {isAnalyzingJD ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                <span>Analyzing Criteria...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-white" />
                <span>Analyze Job Description</span>
              </>
            )}
          </button>
        </div>

        {/* Structured JD Analysis Result */}
        {hasAnalyzedJD && (
          <div className="mt-4 pt-4 border-t border-sage-muted/60 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-charcoal flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-olive" />
                Extracted Job Criteria
              </span>
              <span className="text-[11px] text-charcoal-muted">
                Minimum Experience:{' '}
                <strong className="text-charcoal">
                  {jdData.analyzedData.minimum_experience
                    ? `${jdData.analyzedData.minimum_experience} yrs`
                    : 'Not specified'}
                </strong>
              </span>
            </div>

            {/* Skills Tags */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-cream-50 border border-sage-muted">
                <span className="block text-[10px] font-bold uppercase tracking-wider text-charcoal-muted mb-2">
                  Required Core Skills ({jdData.analyzedData.required_skills?.length || 0})
                </span>
                <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto">
                  {jdData.analyzedData.required_skills?.length > 0 ? (
                    jdData.analyzedData.required_skills.map((skill, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold bg-olive-light text-olive-dark border border-sage/60 shadow-2xs"
                      >
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span className="text-charcoal-muted italic text-[11px]">None specified</span>
                  )}
                </div>
              </div>

              <div className="p-3 rounded-xl bg-cream-50 border border-sage-muted">
                <span className="block text-[10px] font-bold uppercase tracking-wider text-charcoal-muted mb-2">
                  Preferred / Secondary Skills ({jdData.analyzedData.preferred_skills?.length || 0})
                </span>
                <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto">
                  {jdData.analyzedData.preferred_skills?.length > 0 ? (
                    jdData.analyzedData.preferred_skills.map((skill, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-white text-charcoal border border-sage-muted shadow-2xs"
                      >
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span className="text-charcoal-muted italic text-[11px]">None specified</span>
                  )}
                </div>
              </div>
            </div>

            {/* Qualifications & Summary */}
            <div className="p-3 rounded-xl bg-cream-50 border border-sage-muted text-xs space-y-1.5">
              <span className="block text-[10px] font-bold uppercase tracking-wider text-charcoal-muted">
                Analysis Summary
              </span>
              <p className="text-charcoal leading-relaxed font-normal">
                {jdData.analyzedData.summary || 'Job requirements successfully extracted.'}
              </p>
            </div>
          </div>
        )}
      </section>

      {/* SECTION 2: BULK RESUME UPLOAD */}
      <section className="bg-white rounded-2xl border border-sage-muted p-6 shadow-2xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-olive-light text-olive-dark flex items-center justify-center font-bold text-xs">
              2
            </div>
            <div>
              <h3 className="text-base font-bold text-charcoal">Batch Resume Upload</h3>
              <p className="text-xs text-charcoal-muted">
                Upload applicant resumes in PDF or DOCX format for extraction and AI screening
              </p>
            </div>
          </div>
          <span className="text-xs text-charcoal-muted font-medium">
            Max 10MB per file
          </span>
        </div>

        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          onChange={handleFileChange}
          className="hidden"
        />

        {/* Drag & Drop Zone: Light Olive Background with Olive Dashed Border */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-8 sm:p-10 text-center cursor-pointer transition-all ${
            isDragOver
              ? 'border-olive bg-olive-light scale-[1.005]'
              : 'border-olive/60 bg-olive-light/40 hover:bg-olive-light/70 hover:border-olive'
          }`}
        >
          <div className="w-12 h-12 rounded-2xl bg-white text-olive-dark mx-auto flex items-center justify-center mb-3 shadow-2xs border border-sage-muted">
            <UploadCloud className="w-6 h-6" />
          </div>

          <h4 className="text-sm font-bold text-charcoal">
            Drag and drop candidate resumes here, or{' '}
            <span className="text-olive-dark font-semibold hover:underline">browse files</span>
          </h4>
          <p className="text-xs text-charcoal-muted mt-1">
            Supports PDF and DOCX documents (stored securely in session vault for instant viewing)
          </p>
        </div>

        {/* Upload Notice / Error */}
        {uploadNotice && (
          <div className="p-3.5 rounded-xl bg-cream-200 border border-sage-muted text-charcoal text-xs flex items-start justify-between gap-2">
            <div className="flex items-center gap-2">
              <Info className="w-4 h-4 text-olive-dark shrink-0" />
              <span>{uploadNotice}</span>
            </div>
            <button
              type="button"
              onClick={() => setUploadNotice(null)}
              className="text-charcoal-muted hover:text-charcoal"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {resumeError && (
          <div className="p-3.5 rounded-xl bg-terracotta-light border border-terracotta/40 text-terracotta-dark text-xs flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-terracotta-dark shrink-0 mt-0.5" />
            <span>{resumeError}</span>
          </div>
        )}

        {/* Staged Files List */}
        {stagedFiles.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-charcoal">
                Ready to Parse ({stagedFiles.length})
              </span>
              <button
                type="button"
                onClick={handleClearStagedFiles}
                className="text-charcoal-muted hover:text-terracotta-dark transition-colors cursor-pointer"
              >
                Clear all
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-56 overflow-y-auto p-1">
              {stagedFiles.map((file, idx) => (
                <div
                  key={`${file.name}-${idx}`}
                  className="flex items-center justify-between p-2.5 rounded-xl bg-cream-50 border border-sage-muted text-xs shadow-2xs group"
                >
                  <div className="flex items-center gap-2.5 truncate">
                    <File className="w-4 h-4 text-olive-dark shrink-0" />
                    <div className="truncate">
                      <span className="font-medium text-charcoal block truncate">
                        {file.name}
                      </span>
                      <span className="text-[10px] text-charcoal-muted">
                        {formatFileSize(file.size)}
                      </span>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleRemoveStagedFile(idx)}
                    className="p-1 rounded-lg text-charcoal-muted hover:text-terracotta-dark hover:bg-cream-200 transition-colors"
                    title="Remove file"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>

            <div className="pt-2 flex justify-end">
              <button
                type="button"
                onClick={handleParseResumes}
                disabled={isParsingResumes}
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-semibold text-white bg-olive hover:bg-olive-dark disabled:opacity-50 shadow-xs transition-all cursor-pointer"
              >
                {isParsingResumes ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-white" />
                    <span>Parsing {stagedFiles.length} Resume(s)...</span>
                  </>
                ) : (
                  <>
                    <UploadCloud className="w-4 h-4 text-white" />
                    <span>Parse {stagedFiles.length} Staged Resume(s)</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </section>

      {/* SECTION 3: STAGE 3 AI MATCHING & RANKING ENGINE */}
      {hasParsedResumes && (
        <section className="bg-white rounded-2xl border border-sage-muted shadow-2xs overflow-hidden space-y-0">
          <div className="p-6 border-b border-sage-muted/70 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-cream-50/50">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-olive text-white flex items-center justify-center font-bold text-sm shadow-xs">
                <Zap className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-bold text-charcoal">
                    Candidate AI Ranking ({displayCandidates.length})
                  </h3>
                  {hasAIMatches ? (
                    <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-olive-light text-olive-dark border border-sage">
                      Sentence Transformers Active
                    </span>
                  ) : isAiMatching ? (
                    <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-cream-200 text-charcoal border border-sage-muted flex items-center gap-1">
                      <Loader2 className="w-3 h-3 animate-spin" />
                      Evaluating with AI...
                    </span>
                  ) : null}
                </div>
                <p className="text-xs text-charcoal-muted mt-0.5">
                  {hasAIMatches
                    ? 'Ranked by 5-Factor Weighted Score (Semantic 35%, Skills 30%, Experience 20%, Education 10%, Preferred 5%)'
                    : 'Candidate profiles loaded and ready for AI evaluation.'}
                </p>
              </div>
            </div>

            {/* Action Bar & Sorting */}
            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={handleRunAIMatching}
                disabled={isAiMatching || (!hasAnalyzedJD && !jdText.trim())}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold text-white bg-olive hover:bg-olive-dark disabled:bg-cream-200 disabled:text-charcoal-muted/60 disabled:cursor-not-allowed shadow-xs transition-all cursor-pointer"
              >
                {isAiMatching ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-white" />
                    <span>Evaluating AI Matches...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5 text-white" />
                    <span>{hasAIMatches ? 'Re-calculate AI Matches' : 'Run AI Matching Engine'}</span>
                  </>
                )}
              </button>

              <div className="flex items-center gap-1.5 text-xs text-charcoal bg-white border border-sage-muted px-2.5 py-1.5 rounded-xl shadow-2xs">
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
            </div>
          </div>

          {/* AI Matching In-Progress Banner */}
          {isAiMatching && (
            <div className="p-4 bg-olive-light/60 border-b border-sage flex items-center justify-between text-xs text-olive-dark animate-pulse">
              <div className="flex items-center gap-2.5">
                <Loader2 className="w-4 h-4 text-olive-dark animate-spin shrink-0" />
                <span>
                  <strong>Sentence Transformers evaluating candidates:</strong> Generating semantic vectors and calculating weighted scores in background...
                </span>
              </div>
              <span className="text-[11px] text-olive-dark font-semibold hidden sm:inline">
                Please wait a moment
              </span>
            </div>
          )}

          {/* AI Matching Error State */}
          {aiMatchError && (
            <div className="p-4 mx-6 my-4 rounded-xl bg-terracotta-light border border-terracotta/40 text-terracotta-dark text-xs flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 text-terracotta-dark shrink-0 mt-0.5" />
              <div className="flex-1">
                <span className="font-semibold block">AI Matching Notice:</span>
                <span>{aiMatchError}</span>
              </div>
              <button
                type="button"
                onClick={() => setAiMatchError(null)}
                className="text-terracotta-dark hover:text-charcoal"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Candidate Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-cream-50 border-b border-sage-muted text-charcoal-muted uppercase tracking-wider font-semibold">
                <tr>
                  <th className="px-6 py-3.5">Candidate</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">AI Match Score</th>
                  <th className="px-6 py-3.5">Experience</th>
                  <th className="px-6 py-3.5">Key Skills & Coverage</th>
                  <th className="px-6 py-3.5">AI Assessment</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-sage-muted/60">
                {displayCandidates.map(({ candidate, scored, matchScore, rank }) => (
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

                    {/* Immediate Shortlist Decision Badge */}
                    <td className="px-6 py-4" onClick={(e) => e.stopPropagation()}>
                      <CandidateStatusBadge
                        status={candidate.status || 'unreviewed'}
                        onChange={(newSt) => {
                          if (onUpdateCandidateStatus) {
                            onUpdateCandidateStatus(candidate.candidate_id, newSt);
                          }
                        }}
                      />
                    </td>

                    {/* Prominent Stage 3 AI Match Percentage on Sage/Olive Scale */}
                    <td className="px-6 py-4">
                      {matchScore !== null ? (
                        <div className="space-y-1.5">
                          <div className="flex items-center gap-2">
                            <span
                              className={`px-3 py-1 rounded-xl text-xs font-bold border shadow-2xs ${
                                matchScore >= 80
                                  ? 'bg-olive-light text-olive-dark border-olive/50'
                                  : matchScore >= 60
                                  ? 'bg-sage-light text-charcoal border-sage'
                                  : matchScore >= 40
                                  ? 'bg-cream-200 text-charcoal-muted border-sage-muted'
                                  : 'bg-terracotta-light text-terracotta-dark border-terracotta/40'
                              }`}
                            >
                              {matchScore}% AI Match
                            </span>
                          </div>
                          {scored?.semantic_similarity !== undefined && (
                            <div className="text-[10px] text-charcoal-muted font-medium">
                              Semantic: {Math.round(scored.semantic_similarity * 100)}% similarity
                            </div>
                          )}
                        </div>
                      ) : (
                        <span className="text-charcoal-muted italic text-[11px] flex items-center gap-1">
                          <HelpCircle className="w-3.5 h-3.5 text-charcoal-muted/50" />
                          <span>Run AI Matching</span>
                        </span>
                      )}
                    </td>

                    {/* Accurate Experience */}
                    <td className="px-6 py-4">
                      <div className="font-semibold text-charcoal">
                        {candidate.professional_experience_years !== null && candidate.professional_experience_years !== undefined ? (
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

                    {/* Skills Coverage */}
                    <td className="px-6 py-4 max-w-xs">
                      {scored ? (
                        <div className="space-y-1">
                          <div className="text-[11px] text-charcoal font-medium">
                            <span className="text-olive-dark font-bold">
                              {scored.matched_required_skills.length}
                            </span>{' '}
                            matched /{' '}
                            <span className="text-terracotta-dark font-bold">
                              {scored.missing_required_skills.length}
                            </span>{' '}
                            missing required
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {scored.matched_required_skills.slice(0, 3).map((skill, sIdx) => (
                              <span
                                key={sIdx}
                                className="px-1.5 py-0.5 rounded bg-olive-light text-olive-dark text-[10px] font-semibold border border-olive/30"
                              >
                                {skill}
                              </span>
                            ))}
                            {scored.missing_required_skills.slice(0, 2).map((skill, sIdx) => (
                              <span
                                key={`m-${sIdx}`}
                                className="px-1.5 py-0.5 rounded bg-cream-200 text-charcoal-muted text-[10px] font-medium border border-sage-muted line-through"
                                title="Missing required skill"
                              >
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      ) : candidate.skills && candidate.skills.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {candidate.skills.slice(0, 3).map((skill, sIdx) => (
                            <span
                              key={sIdx}
                              className="px-2 py-0.5 rounded-md bg-cream-100 text-charcoal text-[10px] font-medium border border-sage-muted"
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-charcoal-muted italic text-[11px]">No skills found</span>
                      )}
                    </td>

                    {/* AI Assessment / Strengths & Gaps Preview */}
                    <td className="px-6 py-4 max-w-xs">
                      {scored ? (
                        <div className="space-y-1">
                          {scored.strengths.length > 0 && (
                            <div className="text-[11px] text-charcoal line-clamp-1 flex items-center gap-1">
                              <span className="w-1.5 h-1.5 rounded-full bg-olive shrink-0" />
                              <span>{scored.strengths[0]}</span>
                            </div>
                          )}
                          {scored.gaps.length > 0 && (
                            <div className="text-[11px] text-charcoal-muted line-clamp-1 flex items-center gap-1">
                              <span className="w-1.5 h-1.5 rounded-full bg-terracotta shrink-0" />
                              <span>{scored.gaps[0]}</span>
                            </div>
                          )}
                        </div>
                      ) : (
                        <span className="text-charcoal-muted italic text-[11px]">
                          Pending AI analysis
                        </span>
                      )}
                    </td>

                    {/* Actions: View Details, View Resume, Connect, Remove */}
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
                            jobTitle: jdData?.analyzedData ? 'Target Position' : candidate.jobTitle,
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
                ))}
              </tbody>
            </table>
          </div>

          <div className="p-4 bg-cream-50/50 border-t border-sage-muted/70 flex items-center justify-between text-xs text-charcoal-muted">
            <span>Showing {displayCandidates.length} candidate(s) in session</span>
            <button
              type="button"
              onClick={onNavigateCandidates}
              className="text-olive-dark hover:text-charcoal font-semibold cursor-pointer"
            >
              Open in Candidates Directory &rarr;
            </button>
          </div>
        </section>
      )}

      {/* Candidate Detail Modal */}
      {selectedCandidate && (
        <CandidateDetailModal
          candidate={selectedCandidate}
          scoredCandidate={scoredCandidateMap.get(selectedCandidate.candidate_id)}
          jobTitle={jdData?.analyzedData ? 'Target Position' : ''}
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
