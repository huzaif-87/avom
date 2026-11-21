import React from 'react';
import { Menu, User, LogOut } from 'lucide-react';
import ConnectionStatusBadge from './ConnectionStatusBadge';
import { useAuth } from '../context/AuthContext';

export default function Header({
  activeTab,
  onOpenSidebar,
  backendStatus,
  onRefreshHealth,
  isRefreshing,
}) {
  const { recruiter, logout } = useAuth();

  const titles = {
    dashboard: {
      title: 'Dashboard',
      subtitle: 'Overview of persistent assessments and active recruitment pipelines',
    },
    'new-analysis': {
      title: 'New Analysis',
      subtitle: 'Configure target job criteria and applicant resumes',
    },
    history: {
      title: 'Analysis History',
      subtitle: 'Review, reopen, and manage previously saved role assessments',
    },
    candidates: {
      title: 'Candidates Directory',
      subtitle: 'Directory of evaluated talent, shortlist decisions, and communication',
    },
    shortlist: {
      title: 'Shortlisted Talent',
      subtitle: 'Dedicated workspace for top evaluated candidates ready for interview',
    },
  };

  const current = titles[activeTab] || titles.dashboard;

  return (
    <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-md border-b border-sage-muted/70 px-4 sm:px-8 py-4 flex items-center justify-between transition-all">
      {/* Left side: Mobile Toggle & Page Title */}
      <div className="flex items-center gap-3 sm:gap-4">
        <button
          onClick={onOpenSidebar}
          className="p-1.5 rounded-lg text-charcoal-muted hover:text-charcoal hover:bg-cream-100 lg:hidden focus:outline-hidden cursor-pointer"
          title="Open menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div>
          <h1 className="text-base sm:text-lg font-bold text-charcoal tracking-tight leading-tight">
            {current.title}
          </h1>
          <p className="text-xs text-charcoal-muted hidden sm:block leading-none mt-1">
            {current.subtitle}
          </p>
        </div>
      </div>

      {/* Right side: Recruiter Profile & Connection Indicator */}
      <div className="flex items-center gap-3">
        <ConnectionStatusBadge
          status={backendStatus}
          onRefresh={onRefreshHealth}
          isRefreshing={isRefreshing}
        />

        {recruiter && (
          <div className="hidden sm:flex items-center gap-2 pl-3 border-l border-sage-muted">
            <div className="text-right">
              <div className="text-xs font-bold text-charcoal leading-tight">
                {recruiter.full_name}
              </div>
              <div className="text-[10px] text-charcoal-muted leading-tight">
                {recruiter.email}
              </div>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
