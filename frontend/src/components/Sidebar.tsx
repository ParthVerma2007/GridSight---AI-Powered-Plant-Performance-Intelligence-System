import React from 'react';
import {
  TrendingUp,
  Sliders,
  Wrench,
  UploadCloud,
  Search,
  ClipboardList,
  CloudSun,
  Layers,
  Database
} from 'lucide-react';
import { UserRole } from '../types';

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  currentRole: UserRole;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  currentRole,
}) => {
  const navItems = [
    {
      id: 'executive',
      label: 'Executive Overview',
      role: 'CEO / CFO',
      icon: TrendingUp,
      color: 'text-purple-400',
    },
    {
      id: 'operations',
      label: 'Operations & Variance',
      role: 'Operations',
      icon: Sliders,
      color: 'text-blue-400',
    },
    {
      id: 'technician',
      label: 'Field Technician',
      role: 'Technician',
      icon: Wrench,
      color: 'text-amber-400',
    },
    {
      id: 'ingestion',
      label: 'Data Ingestion & Quarantine',
      role: 'All Roles',
      icon: UploadCloud,
      color: 'text-cyan-400',
    },
    {
      id: 'investigations',
      label: 'Root Cause Investigations',
      role: 'Operations',
      icon: Search,
      color: 'text-rose-400',
    },
    {
      id: 'workorders',
      label: 'Work Orders & Safety',
      role: 'Technician / Ops',
      icon: ClipboardList,
      color: 'text-emerald-400',
    },
    {
      id: 'weather',
      label: 'Weather & Open-Meteo',
      role: 'All Roles',
      icon: CloudSun,
      color: 'text-orange-400',
    },
  ];

  return (
    <aside className="w-64 bg-[#0A0E18] border-r border-gray-800 flex flex-col justify-between shrink-0">
      <div className="p-4 space-y-6">
        <div className="px-2">
          <p className="text-[10px] font-bold uppercase tracking-wider text-gray-500">
            Control Views
          </p>
        </div>

        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-blue-600/15 text-white border border-blue-500/30 font-semibold'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-900/60'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-blue-400' : item.color}`} />
                <span className="truncate">{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* System Integrity Footer */}
      <div className="p-4 border-t border-gray-900 bg-gray-950/60">
        <div className="flex items-center space-x-2 text-[11px] text-gray-400">
          <Database className="w-3.5 h-3.5 text-emerald-400" />
          <span>Canonical SQLite DB</span>
        </div>
        <p className="text-[10px] text-gray-500 mt-1">
          PostgreSQL Ready Schema · RBAC Active
        </p>
      </div>
    </aside>
  );
};
