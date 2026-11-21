import React from 'react';
import {
  LayoutDashboard,
  FilePlus2,
  Users,
  History,
  CheckCircle2,
  Sparkles,
  X,
  LogOut,
  User,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Sidebar({
  activeTab,
  onSelectTab,
  isOpen,
  onClose,
}) {
  const { recruiter, logout } = useAuth();

  const navigationItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
    },
    {
      id: 'new-analysis',
      label: 'New Analysis',
      icon: FilePlus2,
    },
    {
      id: 'history',
      label: 'Analysis History',
      icon: History,
    },
    {
      id: 'candidates',
      label: 'Candidates',
      icon: Users,
    },
    {
      id: 'shortlist',
      label: 'Shortlist',
      icon: CheckCircle2,
    },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-charcoal/50 backdrop-blur-xs lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Deep Olive Editorial Sidebar Container */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-olive-dark text-cream-100 border-r border-olive-darker flex flex-col transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="h-18 px-5 flex items-center justify-between border-b border-olive/40">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-sage flex items-center justify-center text-charcoal-dark shadow-xs font-semibold">
              <Sparkles className="w-4 h-4" />
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="font-semibold text-base tracking-tight text-white">
                TalentRank
              </span>
              <span className="text-xs font-medium px-1.5 py-0.5 rounded bg-sage/20 text-sage-light tracking-wide">
                AI
              </span>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-cream-200/70 hover:text-white hover:bg-olive lg:hidden"
            title="Close sidebar"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Recruiter Workspace Pill */}
        {recruiter && (
          <div className="px-4 py-3 mx-3 mt-4 rounded-xl bg-olive/50 border border-olive/60 flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-sage text-charcoal font-bold text-xs flex items-center justify-center shrink-0">
              {recruiter.full_name ? recruiter.full_name.charAt(0).toUpperCase() : 'R'}
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-xs font-bold text-white truncate">
                {recruiter.full_name}
              </div>
              <div className="text-[10px] text-cream-200/70 truncate">
                {recruiter.email}
              </div>
            </div>
          </div>
        )}

        {/* Simplified Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1.5 overflow-y-auto">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  onSelectTab(item.id);
                  if (onClose) onClose();
                }}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs sm:text-sm transition-all duration-150 cursor-pointer ${
                  isActive
                    ? 'bg-sage text-charcoal font-semibold shadow-xs'
                    : 'text-cream-200/80 hover:text-white hover:bg-olive/60 font-medium'
                }`}
              >
                <Icon
                  className={`w-4 h-4 transition-colors ${
                    isActive ? 'text-charcoal' : 'text-cream-200/70'
                  }`}
                />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Logout Action in Footer */}
        <div className="p-3 border-t border-olive/30">
          <button
            type="button"
            onClick={logout}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs text-cream-200/80 hover:text-white hover:bg-olive/50 transition cursor-pointer"
            title="Sign out of recruiter workspace"
          >
            <LogOut className="w-4 h-4 text-cream-200/60" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>
    </>
  );
}
