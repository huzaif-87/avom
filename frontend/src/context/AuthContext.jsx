import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getMyProfile, loginRecruiter, registerRecruiter, logoutRecruiterApi } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [recruiter, setRecruiter] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('talentrank_token') || null);
  const [loading, setLoading] = useState(true);

  // Load existing session on initial mount
  const checkSession = useCallback(async () => {
    const savedToken = localStorage.getItem('talentrank_token');
    if (!savedToken) {
      setRecruiter(null);
      setLoading(false);
      return;
    }

    try {
      const profile = await getMyProfile();
      setRecruiter(profile);
      setToken(savedToken);
    } catch (err) {
      console.warn('Session expired or invalid token:', err.message);
      localStorage.removeItem('talentrank_token');
      localStorage.removeItem('talentrank_recruiter');
      localStorage.removeItem('talentrank_last_analysis_id');
      setToken(null);
      setRecruiter(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkSession();

    // Listen for 401 session expiry from api interceptor
    const handleAuthExpired = () => {
      setToken(null);
      setRecruiter(null);
    };

    window.addEventListener('talentrank_auth_expired', handleAuthExpired);
    return () => window.removeEventListener('talentrank_auth_expired', handleAuthExpired);
  }, [checkSession]);

  const login = async (email, password) => {
    const data = await loginRecruiter({ email, password });
    localStorage.setItem('talentrank_token', data.access_token);
    localStorage.setItem('talentrank_recruiter', JSON.stringify(data.recruiter));
    setToken(data.access_token);
    setRecruiter(data.recruiter);
    return data.recruiter;
  };

  const register = async (fullName, email, password, confirmPassword) => {
    const data = await registerRecruiter({
      full_name: fullName,
      email,
      password,
      confirm_password: confirmPassword,
    });
    localStorage.setItem('talentrank_token', data.access_token);
    localStorage.setItem('talentrank_recruiter', JSON.stringify(data.recruiter));
    setToken(data.access_token);
    setRecruiter(data.recruiter);
    return data.recruiter;
  };

  const logout = async () => {
    await logoutRecruiterApi();
    localStorage.removeItem('talentrank_token');
    localStorage.removeItem('talentrank_recruiter');
    localStorage.removeItem('talentrank_last_analysis_id');
    setToken(null);
    setRecruiter(null);
  };

  const value = {
    recruiter,
    token,
    isAuthenticated: Boolean(token && recruiter),
    loading,
    login,
    register,
    logout,
    refreshProfile: checkSession,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
