import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import DashboardPage from './pages/DashboardPage';
import NewAnalysisPage from './pages/NewAnalysisPage';
import CandidatesPage from './pages/CandidatesPage';
import AnalysisHistoryPage from './pages/AnalysisHistoryPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import { AuthProvider, useAuth } from './context/AuthContext';
import {
  checkBackendHealth,
  getAnalysisById,
  listSavedAnalyses,
  updateCandidateDecisionStatus,
} from './services/api';
import { Loader2 } from 'lucide-react';

function MainApp() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [authView, setAuthView] = useState('login'); // 'login' | 'register'
  const [activeTab, setActiveTab] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Active Workspace Analysis Record ID
  const [activeAnalysisId, setActiveAnalysisId] = useState(null);
  const [activeAnalysisTitle, setActiveAnalysisTitle] = useState('');

  // Backend Health State
  const [backendStatus, setBackendStatus] = useState({
    loading: true,
    connected: false,
    status: 'checking',
    error: null,
    latencyMs: null,
    checkedAt: null,
    version: null,
  });
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Active Analysis Working State
  const [jdData, setJdData] = useState(null);
  const [parsedCandidates, setParsedCandidates] = useState([]);
  const [batchSummary, setBatchSummary] = useState(null);
  const [aiMatchResults, setAiMatchResults] = useState(null);
  const [isAiMatching, setIsAiMatching] = useState(false);
  const [aiMatchError, setAiMatchError] = useState(null);

  const fetchHealth = useCallback(async (manual = false) => {
    if (manual) setIsRefreshing(true);
    try {
      const result = await checkBackendHealth();
      setBackendStatus({
        loading: false,
        ...result,
      });
    } catch (err) {
      setBackendStatus({
        loading: false,
        connected: false,
        status: 'disconnected',
        error: err.message || 'Health check failed',
        latencyMs: null,
        checkedAt: new Date().toISOString(),
      });
    } finally {
      if (manual) setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(() => fetchHealth(false), 30000);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  // Automatically restore recruiter's latest analysis on page reload or login
  useEffect(() => {
    if (!isAuthenticated) return;

    let isMounted = true;
    const restoreLastSession = async () => {
      try {
        const lastId = localStorage.getItem('talentrank_last_analysis_id');
        if (lastId) {
          try {
            const data = await getAnalysisById(lastId);
            if (isMounted && data) {
              setActiveAnalysisId(data.id);
              setActiveAnalysisTitle(data.job_title);
              setJdData({
                text: data.jd_text,
                analyzedData: data.jd_analysis,
              });
              setParsedCandidates(data.candidates || []);
              setAiMatchResults(data.ai_matching_results || null);
              return;
            }
          } catch (e) {
            console.warn('Could not restore last analysis by ID:', e);
          }
        }

        // If no lastId or failed, restore latest analysis from recruiter's saved history
        const list = await listSavedAnalyses();
        if (isMounted && list && list.length > 0) {
          const latest = await getAnalysisById(list[0].id);
          if (isMounted && latest) {
            setActiveAnalysisId(latest.id);
            setActiveAnalysisTitle(latest.job_title);
            localStorage.setItem('talentrank_last_analysis_id', latest.id);
            setJdData({
              text: latest.jd_text,
              analyzedData: latest.jd_analysis,
            });
            setParsedCandidates(latest.candidates || []);
            setAiMatchResults(latest.ai_matching_results || null);
          }
        }
      } catch (err) {
        console.warn('Auto-restore of saved analysis skipped:', err);
      }
    };

    restoreLastSession();
    return () => {
      isMounted = false;
    };
  }, [isAuthenticated]);

  const handleUpdateJDData = (data) => {
    setJdData(data);
    setAiMatchResults(null);
    setAiMatchError(null);
  };

  const handleUpdateParsedCandidates = (newCandidates, summary) => {
    setParsedCandidates(newCandidates);
    setBatchSummary(summary);
    setAiMatchResults(null);
    setAiMatchError(null);
  };

  const handleClearSession = () => {
    setJdData(null);
    setParsedCandidates([]);
    setBatchSummary(null);
    setAiMatchResults(null);
    setAiMatchError(null);
    setActiveAnalysisId(null);
    setActiveAnalysisTitle('');
    localStorage.removeItem('talentrank_last_analysis_id');
  };

  const handleRemoveCandidate = (candidateId) => {
    setParsedCandidates((prev) => prev.filter((c) => c.candidate_id !== candidateId));
    if (aiMatchResults?.ranked_candidates) {
      setAiMatchResults((prev) => ({
        ...prev,
        ranked_candidates: prev.ranked_candidates.filter((c) => c.candidate_id !== candidateId),
      }));
    }
  };

  // Reopen a saved analysis from MongoDB
  const handleOpenAnalysis = async (analysisId) => {
    try {
      const data = await getAnalysisById(analysisId);
      setActiveAnalysisId(data.id);
      setActiveAnalysisTitle(data.job_title);
      localStorage.setItem('talentrank_last_analysis_id', data.id);
      setJdData({
        text: data.jd_text,
        analyzedData: data.jd_analysis,
      });
      setParsedCandidates(data.candidates || []);
      setAiMatchResults(data.ai_matching_results || null);
      setActiveTab('candidates');
    } catch (err) {
      alert('Failed to load saved analysis: ' + err.message);
    }
  };

  // Update candidate shortlist decision status
  const handleUpdateCandidateStatus = async (candidateId, newStatus) => {
    // Optimistic frontend state update
    setParsedCandidates((prev) =>
      prev.map((c) => (c.candidate_id === candidateId ? { ...c, status: newStatus } : c))
    );

    // If an analysis is saved in MongoDB, persist immediately to the database
    if (activeAnalysisId) {
      try {
        await updateCandidateDecisionStatus(activeAnalysisId, candidateId, newStatus);
      } catch (err) {
        console.error('Failed to persist status to MongoDB:', err);
      }
    }
  };

  const handleStartNewAnalysis = () => {
    handleClearSession();
    setActiveTab('new-analysis');
  };

  // Initial Auth Loading Screen
  if (authLoading) {
    return (
      <div className="min-h-screen bg-cream-100 flex flex-col items-center justify-center">
        <Loader2 className="w-10 h-10 text-olive animate-spin mb-3" />
        <h3 className="text-sm font-semibold text-charcoal">Loading Recruiter Workspace...</h3>
      </div>
    );
  }

  // Unauthenticated: Show Login or Register
  if (!isAuthenticated) {
    if (authView === 'register') {
      return <RegisterPage onSwitchToLogin={() => setAuthView('login')} />;
    }
    return <LoginPage onSwitchToRegister={() => setAuthView('register')} />;
  }

  return (
    <div className="min-h-screen bg-cream-100 text-charcoal flex">
      {/* Deep Olive Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main Workspace Area (Soft Cream Background) */}
      <div className="flex-1 flex flex-col min-w-0 lg:pl-64">
        <Header
          activeTab={activeTab}
          onOpenSidebar={() => setSidebarOpen(true)}
          backendStatus={backendStatus}
          onRefreshHealth={() => fetchHealth(true)}
          isRefreshing={isRefreshing}
        />

        <main className="flex-1 p-4 sm:p-8">
          {activeTab === 'dashboard' && (
            <DashboardPage
              onStartNewAnalysis={handleStartNewAnalysis}
              onNavigateCandidates={() => setActiveTab('candidates')}
              onNavigateHistory={() => setActiveTab('history')}
              onNavigateShortlist={() => setActiveTab('shortlist')}
              onOpenAnalysis={handleOpenAnalysis}
              jdData={jdData}
              parsedCandidates={parsedCandidates}
              aiMatchResults={aiMatchResults}
              activeAnalysisId={activeAnalysisId}
              onUpdateCandidateStatus={handleUpdateCandidateStatus}
            />
          )}

          {activeTab === 'new-analysis' && (
            <NewAnalysisPage
              onBackToDashboard={() => setActiveTab('dashboard')}
              onNavigateCandidates={() => setActiveTab('candidates')}
              jdData={jdData}
              onUpdateJDData={handleUpdateJDData}
              parsedCandidates={parsedCandidates}
              onUpdateParsedCandidates={handleUpdateParsedCandidates}
              batchSummary={batchSummary}
              onClearSession={handleClearSession}
              onRemoveCandidate={handleRemoveCandidate}
              aiMatchResults={aiMatchResults}
              onUpdateAiMatchResults={setAiMatchResults}
              isAiMatching={isAiMatching}
              setIsAiMatching={setIsAiMatching}
              aiMatchError={aiMatchError}
              setAiMatchError={setAiMatchError}
              onUpdateCandidateStatus={handleUpdateCandidateStatus}
              activeAnalysisId={activeAnalysisId}
              setActiveAnalysisId={setActiveAnalysisId}
            />
          )}

          {activeTab === 'history' && (
            <AnalysisHistoryPage
              onOpenAnalysis={handleOpenAnalysis}
              onStartNewAnalysis={handleStartNewAnalysis}
            />
          )}

          {activeTab === 'candidates' && (
            <CandidatesPage
              parsedCandidates={parsedCandidates}
              onStartNewAnalysis={handleStartNewAnalysis}
              jobTitle={activeAnalysisTitle || (jdData?.analyzedData ? 'Target Position' : '')}
              jdData={jdData}
              aiMatchResults={aiMatchResults}
              onRemoveCandidate={handleRemoveCandidate}
              onUpdateCandidateStatus={handleUpdateCandidateStatus}
              activeAnalysisTitle={activeAnalysisTitle}
              filterOnlyShortlisted={false}
            />
          )}

          {activeTab === 'shortlist' && (
            <CandidatesPage
              parsedCandidates={parsedCandidates.filter((c) => c.status === 'shortlisted')}
              onStartNewAnalysis={handleStartNewAnalysis}
              jobTitle={activeAnalysisTitle || (jdData?.analyzedData ? 'Target Position' : '')}
              jdData={jdData}
              aiMatchResults={aiMatchResults}
              onRemoveCandidate={handleRemoveCandidate}
              onUpdateCandidateStatus={handleUpdateCandidateStatus}
              activeAnalysisTitle={activeAnalysisTitle}
              filterOnlyShortlisted={true}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return <MainApp />;
}
