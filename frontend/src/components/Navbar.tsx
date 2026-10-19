import React from 'react';
import { UserRole } from '../types';
import { ShieldCheck, Activity, Sun, RefreshCw, Zap } from 'lucide-react';

interface NavbarProps {
  currentRole: UserRole;
  onRoleChange: (role: UserRole) => void;
  onRefresh: () => void;
  isLoading: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentRole,
  onRoleChange,
  onRefresh,
  isLoading,
}) => {
  return (
    <header className="h-16 bg-[#0D131F] border-b border-gray-800 px-6 flex items-center justify-between sticky top-0 z-40">
      {/* Brand & Plant Overview */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <div className="w-9 h-9 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
            <Sun className="w-5 h-5 animate-spin-slow" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-white text-base tracking-wide">Helios-50 Solar Farm</span>
              <span className="bg-emerald-500/10 text-emerald-400 text-xs px-2 py-0.5 rounded border border-emerald-500/20 flex items-center gap-1 font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                GRID-TIED
              </span>
            </div>
            <p className="text-xs text-gray-400">50.0 MW AC Nominal · SMA Central Inverters · Southern California</p>
          </div>
        </div>
      </div>

      {/* Center status indicators */}
      <div className="hidden lg:flex items-center space-x-6 text-xs text-gray-400">
        <div className="flex items-center space-x-2 bg-gray-900/60 px-3 py-1.5 rounded-md border border-gray-800">
          <Zap className="w-3.5 h-3.5 text-amber-400" />
          <span>PPA Tariff: <strong className="text-gray-200">$48.50 / MWh</strong></span>
        </div>
        <div className="flex items-center space-x-2 bg-gray-900/60 px-3 py-1.5 rounded-md border border-gray-800">
          <Activity className="w-3.5 h-3.5 text-blue-400" />
          <span>Analytics Engine: <strong className="text-emerald-400">Deterministic Active</strong></span>
        </div>
      </div>

      {/* Role Switcher & Actions */}
      <div className="flex items-center space-x-3">
        {/* Role Selector Badge */}
        <div className="flex items-center bg-gray-950 p-1 rounded-lg border border-gray-800">
          <button
            onClick={() => onRoleChange('CEO')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              currentRole === 'CEO'
                ? 'bg-purple-600 text-white shadow-sm'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            CEO / CFO
          </button>
          <button
            onClick={() => onRoleChange('OPERATIONS')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              currentRole === 'OPERATIONS'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Operations
          </button>
          <button
            onClick={() => onRoleChange('TECHNICIAN')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              currentRole === 'TECHNICIAN'
                ? 'bg-amber-600 text-white shadow-sm'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Technician
          </button>
        </div>

        {/* Refresh button */}
        <button
          onClick={onRefresh}
          disabled={isLoading}
          title="Refresh telemetry & calculation engine"
          className="p-2 bg-gray-900 hover:bg-gray-800 border border-gray-800 text-gray-300 hover:text-white rounded-lg transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-blue-400' : ''}`} />
        </button>
      </div>
    </header>
  );
};
