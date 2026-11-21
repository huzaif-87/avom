import React from 'react';

export default function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  badgeText,
}) {
  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs hover:shadow-sm transition-all">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          {title}
        </span>
        {Icon && (
          <div className="w-9 h-9 rounded-lg bg-violet-50 text-violet-600 flex items-center justify-center border border-violet-100/60">
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      <div className="flex items-baseline gap-2 mb-1">
        <span className="text-3xl font-bold tracking-tight text-slate-900">
          {value}
        </span>
        {badgeText && (
          <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
            {badgeText}
          </span>
        )}
      </div>

      <p className="text-xs text-slate-500 flex items-center gap-1.5">
        <span className="w-1.5 h-1.5 rounded-full bg-slate-300"></span>
        {subtitle}
      </p>
    </div>
  );
}
