import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 120s timeout for neural embedding generation & bulk file processing
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token to all outgoing requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('talentrank_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to catch 401 unauthorized errors and trigger logout
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !error.config.url.includes('/api/auth/login')) {
      // Clear token and fire session expired event if appropriate
      localStorage.removeItem('talentrank_token');
      localStorage.removeItem('talentrank_recruiter');
      window.dispatchEvent(new Event('talentrank_auth_expired'));
    }
    return Promise.reject(error);
  }
);

// -------------------------------------------------------------
// Authentication APIs
// -------------------------------------------------------------

export async function registerRecruiter(payload) {
  try {
    const response = await apiClient.post('/api/auth/register', payload);
    return response.data;
  } catch (error) {
    const msg = error.response?.data?.detail || error.response?.data?.error?.message || error.message || 'Registration failed';
    throw new Error(msg);
  }
}

export async function loginRecruiter(payload) {
  try {
    const response = await apiClient.post('/api/auth/login', payload);
    return response.data;
  } catch (error) {
    const msg = error.response?.data?.detail || error.response?.data?.error?.message || error.message || 'Login failed';
    throw new Error(msg);
  }
}

export async function getMyProfile() {
  try {
    const response = await apiClient.get('/api/auth/me');
    return response.data;
  } catch (error) {
    const msg = error.response?.data?.detail || error.message || 'Failed to fetch recruiter profile';
    throw new Error(msg);
  }
}

export async function logoutRecruiterApi() {
  try {
    await apiClient.post('/api/auth/logout');
  } catch (e) {
    // Ignore network error on logout
  }
}

// -------------------------------------------------------------
// Health Check API
// -------------------------------------------------------------

export async function checkBackendHealth() {
  const startTime = performance.now();
  try {
    const response = await apiClient.get('/api/health');
    const latencyMs = Math.round(performance.now() - startTime);

    return {
      connected: true,
      status: response.data.status || 'ok',
      service: response.data.service || 'TalentRank AI',
      version: response.data.version || '1.0.0',
      environment: response.data.environment || 'development',
      serverTimestamp: response.data.timestamp,
      latencyMs,
      checkedAt: new Date().toISOString(),
      raw: response.data,
    };
  } catch (error) {
    return {
      connected: false,
      status: 'disconnected',
      error: error.response?.data?.error?.message || error.message || 'Cannot reach backend service',
      latencyMs: null,
      checkedAt: new Date().toISOString(),
    };
  }
}

// -------------------------------------------------------------
// Job Description & Resumes APIs
// -------------------------------------------------------------

export async function analyzeJobDescription(text) {
  if (!text || !text.trim()) {
    throw new Error('Job description text cannot be empty.');
  }

  try {
    const response = await apiClient.post('/api/jd/analyze', { text });
    return response.data;
  } catch (error) {
    const errorMessage =
      error.response?.data?.error?.message ||
      error.response?.data?.detail ||
      error.message ||
      'Failed to analyze job description.';
    throw new Error(errorMessage);
  }
}

export async function parseResumes(files) {
  if (!files || files.length === 0) {
    throw new Error('Please select at least one resume file to upload.');
  }

  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }

  try {
    const response = await apiClient.post('/api/resumes/parse', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    const errorMessage =
      error.response?.data?.error?.message ||
      error.response?.data?.detail ||
      error.message ||
      'Failed to parse uploaded resumes.';
    throw new Error(errorMessage);
  }
}

export function getResumeViewUrl(candidateId) {
  const token = localStorage.getItem('talentrank_token');
  const tokenParam = token ? `?token=${encodeURIComponent(token)}` : '';
  return `${API_BASE_URL}/api/resumes/${encodeURIComponent(candidateId)}/view${tokenParam}`;
}

export function getResumeDownloadUrl(candidateId) {
  const token = localStorage.getItem('talentrank_token');
  const tokenParam = token ? `?token=${encodeURIComponent(token)}` : '';
  return `${API_BASE_URL}/api/resumes/${encodeURIComponent(candidateId)}/download${tokenParam}`;
}

export async function deleteCandidateResume(candidateId) {
  try {
    const response = await apiClient.delete(`/api/resumes/${encodeURIComponent(candidateId)}`);
    return response.data;
  } catch (error) {
    const errorMessage =
      error.response?.data?.error?.message ||
      error.response?.data?.detail ||
      error.message ||
      'Failed to remove candidate resume';
    throw new Error(errorMessage);
  }
}

export async function evaluateAIMatching({ jdText, jdAnalysis, candidates }) {
  if (!candidates || candidates.length === 0) {
    throw new Error('At least one candidate is required for AI matching evaluation.');
  }

  if (!jdText && !jdAnalysis) {
    throw new Error('A job description is required to run the AI matching engine.');
  }

  try {
    const response = await apiClient.post(
      '/api/match/evaluate',
      {
        jd_text: jdText || undefined,
        jd_analysis: jdAnalysis || undefined,
        candidates,
      },
      {
        timeout: 120000,
      }
    );
    return response.data;
  } catch (error) {
    const errorMessage =
      error.response?.data?.error?.message ||
      error.response?.data?.detail ||
      error.message ||
      'Failed to evaluate AI matching for candidates.';
    throw new Error(errorMessage);
  }
}

// -------------------------------------------------------------
// Persistent Recruiter Analysis & Shortlist APIs
// -------------------------------------------------------------

export async function saveJobAnalysis(payload) {
  try {
    const response = await apiClient.post('/api/analyses', payload);
    return response.data;
  } catch (error) {
    const msg = error.response?.data?.detail || error.message || 'Failed to save analysis to workspace';
    throw new Error(msg);
  }
}

export async function listSavedAnalyses() {
  try {
    const response = await apiClient.get('/api/analyses');
    return response.data;
  } catch (error) {
    const msg = error.response?.data?.detail || error.message || 'Failed to load analysis history';
    throw new Error(msg);
  }
}

export async function getAnalysisById(analysisId, statusFilter = null) {
  try {
    const params = statusFilter ? { status_filter: statusFilter } : {};
    const response = await apiClient.get(`/api/analyses/${encodeURIComponent(analysisId)}`, { params });
    return response.data;
  } catch (error) {
    const msg = error.response?.data?.detail || error.message || 'Failed to load analysis';
    throw new Error(msg);
  }
}

export async function deleteSavedAnalysis(analysisId) {
  try {
    const response = await apiClient.delete(`/api/analyses/${encodeURIComponent(analysisId)}`);
    return response.data;
  } catch (error) {
    const msg = error.response?.data?.detail || error.message || 'Failed to delete analysis';
    throw new Error(msg);
  }
}

export async function updateCandidateDecisionStatus(analysisId, candidateId, status) {
  try {
    const response = await apiClient.patch(
      `/api/analyses/${encodeURIComponent(analysisId)}/candidates/${encodeURIComponent(candidateId)}/status`,
      { status }
    );
    return response.data;
  } catch (error) {
    const msg = error.response?.data?.detail || error.message || 'Failed to update candidate status';
    throw new Error(msg);
  }
}

export async function deleteAnalysisCandidate(analysisId, candidateId) {
  try {
    const response = await apiClient.delete(
      `/api/analyses/${encodeURIComponent(analysisId)}/candidates/${encodeURIComponent(candidateId)}`
    );
    return response.data;
  } catch (error) {
    const msg = error.response?.data?.detail || error.message || 'Failed to delete candidate';
    throw new Error(msg);
  }
}
