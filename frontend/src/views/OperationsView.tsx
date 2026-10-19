import React, { useState } from 'react';
import { OperationsDashboardResponse, AttributedCause } from '../types';
import { KPICard } from '../components/KPICard';
import { GenerationChart } from '../components/GenerationChart';
import { VarianceWaterfallChart } from '../components/VarianceWaterfallChart';
import { AIIntelligencePanel } from '../components/AIIntelligencePanel';
import { EvidenceModal } from '../components/EvidenceModal';
import {
  Sliders,
  Activity,
  Zap,
  Clock,
  Layers,
  Search,
  Users,
  Radio,
  AlertTriangle
} from 'lucide-react';

interface OperationsViewProps {
  data: OperationsDashboardResponse | null;
  onRefresh: () => void;
  onNavigateToInvestigations: () => void;
}

export const OperationsView: React.FC<OperationsViewProps> = ({
  data,
  onRefresh,
  onNavigateToInvestigations,
}) => {
  const [selectedCause, setSelectedCause] = useState<AttributedCause | null>(null);

  if (!data) {
    return (
      <div className="p-8 text-center text-gray-500 text-sm">
        Loading Operations Management Dashboard...
      </div>
    );
  }

  const {
    kpi,
    time_series,
    attribution,
    active_investigations,
    grid_and_weather_events,
    workforce_status,
    ai_insights,
  } = data;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Sliders className="w-5 h-5 text-blue-400" />
            Operations Management & Dispatch Intelligence
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Real-time generation telemetry · Deterministic variance waterfall · Root cause tracking · Fleet availability
          </p>
        </div>
        <div className="flex items-center space-x-2 text-xs font-mono">
          <span className="px-2.5 py-1 rounded-md bg-blue-950/60 text-blue-300 border border-blue-800">
            Active Fleet: 10 Inverters (50 MW)
          </span>
          <span className="px-2.5 py-1 rounded-md bg-emerald-950/60 text-emerald-300 border border-emerald-800">
            Availability: {kpi.availability_pct}%
          </span>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Actual Output"
          value={kpi.actual_generation_mwh.toLocaleString()}
          unit="MWh"
          subValue={`Target: ${kpi.expected_generation_mwh.toLocaleString()} MWh`}
          status={kpi.variance_mwh >= 0 ? 'success' : 'warning'}
          icon={<Zap className="w-4 h-4 text-emerald-400" />}
          comparisonText="7-Day Generation Total"
        />

        <KPICard
          title="Net Variance"
          value={`${kpi.variance_mwh > 0 ? '+' : ''}${kpi.variance_mwh.toLocaleString()}`}
          unit="MWh"
          subValue={`${kpi.variance_pct}% deviation`}
          status={kpi.variance_mwh >= -5.0 ? 'success' : 'danger'}
          icon={<Activity className="w-4 h-4 text-rose-400" />}
          comparisonText="Day-Ahead Forecast Benchmark"
        />

        <KPICard
          title="Fleet Availability"
          value={`${kpi.availability_pct}%`}
          subValue={`${kpi.downtime_hours}h total downtime`}
          status={kpi.availability_pct >= 95 ? 'success' : 'danger'}
          icon={<Clock className="w-4 h-4 text-blue-400" />}
          comparisonText="Inverter Operating Uptime"
        />

        <KPICard
          title="Grid Curtailment"
          value={kpi.curtailment_mwh.toLocaleString()}
          unit="MWh"
          subValue="ISO Dispatch Directive"
          status={kpi.curtailment_mwh > 0 ? 'warning' : 'neutral'}
          icon={<Radio className="w-4 h-4 text-amber-400" />}
          comparisonText="CAISO-DIR-9921 Export Limit"
        />
      </div>

      {/* Generation Chart: Expected vs Actual Composed */}
      <GenerationChart data={time_series} />

      {/* Deterministic Variance Bridge (Waterfall) */}
      <VarianceWaterfallChart
        steps={attribution.waterfall_steps}
        causes={attribution.causes}
        onSelectCause={(cause) => setSelectedCause(cause)}
      />

      {/* Investigations and Operational Events Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Investigations */}
        <div className="bg-[#0F1626] border border-gray-800 rounded-xl p-5 shadow-lg space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Search className="w-4 h-4 text-rose-400" />
              Active Root Cause Investigations ({active_investigations.length})
            </h3>
            <button
              onClick={onNavigateToInvestigations}
              className="text-xs text-blue-400 hover:text-blue-300 font-semibold"
            >
              View Tracker →
            </button>
          </div>

          <div className="space-y-3">
            {active_investigations.map((inv: any) => (
              <div key={inv.id} className="p-3 bg-gray-950 rounded-xl border border-gray-800 text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-gray-200">{inv.title}</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase ${
                    inv.priority === 'critical' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-gray-800 text-gray-300'
                  }`}>
                    {inv.priority}
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px] text-gray-400">
                  <span>Owner: <strong className="text-gray-300">{inv.owner}</strong></span>
                  <span>Status: <strong className="text-amber-400 uppercase font-mono">{inv.status}</strong></span>
                </div>
                {inv.deadline && (
                  <p className="text-[10px] text-gray-500 font-mono">
                    Deadline: {new Date(inv.deadline).toLocaleDateString()}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Grid & External Events */}
        <div className="bg-[#0F1626] border border-gray-800 rounded-xl p-5 shadow-lg space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Radio className="w-4 h-4 text-amber-400" />
            Grid Directives & Environmental Events ({grid_and_weather_events.length})
          </h3>

          <div className="space-y-3">
            {grid_and_weather_events.map((ev: any) => (
              <div key={ev.id} className="p-3 bg-gray-950 rounded-xl border border-gray-800 text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-gray-200 font-mono">{ev.directive_code || 'ISO Directive'}</span>
                  <span className="text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded font-mono">
                    {ev.curtailed_capacity_mw} MW Curtailed
                  </span>
                </div>
                <p className="text-gray-400 text-[11px]">{ev.notes}</p>
                <div className="text-[10px] text-gray-500 font-mono">
                  Window: {new Date(ev.start).toLocaleString()} to {new Date(ev.end).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI Operations Intelligence Panel */}
      <AIIntelligencePanel initialInsights={ai_insights} currentRole="OPERATIONS" />

      {/* Evidence Drill Down Modal */}
      <EvidenceModal cause={selectedCause} onClose={() => setSelectedCause(null)} />
    </div>
  );
};
