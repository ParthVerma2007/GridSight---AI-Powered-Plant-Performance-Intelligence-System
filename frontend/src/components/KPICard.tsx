import React from 'react';

interface KPICardProps {
  title: string;
  value: string | number;
  unit?: string;
  subValue?: string;
  status?: 'success' | 'warning' | 'danger' | 'neutral';
  icon?: React.ReactNode;
  comparisonText?: string;
}

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  unit,
  subValue,
  status = 'neutral',
  icon,
  comparisonText,
}) => {
  const statusStyles = {
    success: 'border-emerald-500/20 text-emerald-400 bg-emerald-500/5',
    warning: 'border-amber-500/20 text-amber-400 bg-amber-500/5',
    danger: 'border-rose-500/20 text-rose-400 bg-rose-500/5',
    neutral: 'border-gray-800 text-gray-200 bg-gray-900/40',
  };

  const badgeStyles = {
    success: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
    warning: 'bg-amber-500/10 text-amber-400 border border-amber-500/20',
    danger: 'bg-rose-500/10 text-rose-400 border border-rose-500/20',
    neutral: 'bg-gray-800 text-gray-400',
  };

  return (
    <div className={`p-4 rounded-xl border ${statusStyles[status]} transition-all hover:border-gray-700`}>
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-gray-400 tracking-wide uppercase">{title}</p>
        {icon && <div className="text-gray-400">{icon}</div>}
      </div>

      <div className="mt-2 flex items-baseline space-x-1.5">
        <span className="text-2xl font-bold tracking-tight text-white font-mono">{value}</span>
        {unit && <span className="text-xs font-medium text-gray-400">{unit}</span>}
      </div>

      {(subValue || comparisonText) && (
        <div className="mt-2 flex items-center justify-between text-[11px]">
          {subValue && (
            <span className={`px-2 py-0.5 rounded font-mono ${badgeStyles[status]}`}>
              {subValue}
            </span>
          )}
          {comparisonText && (
            <span className="text-gray-400 truncate">{comparisonText}</span>
          )}
        </div>
      )}
    </div>
  );
};
