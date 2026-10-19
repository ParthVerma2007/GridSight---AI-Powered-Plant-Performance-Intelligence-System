import React, { useState } from 'react';
import { ExecutiveDashboardResponse, AttributedCause } from '../types';
import { KPICard } from '../components/KPICard';
import { AIIntelligencePanel } from '../components/AIIntelligencePanel';
import { EvidenceModal } from '../components/EvidenceModal';
import {
  DollarSign,
  TrendingDown,
  TrendingUp,
  AlertOctagon,
  CheckCircle,
  FileCheck,
  Building,
  Zap,
  Clock
} from 'lucide-react';

interface ExecutiveViewProps {
  data: ExecutiveDashboardResponse | null;
  onRefresh: () => void;
}

export const ExecutiveView: React.FC<ExecutiveViewProps> = ({ data, onRefresh }) => {
  const [selectedCause, setSelectedCause] = useState<AttributedCause | null>(null);
  const [approvals, setApprovals] = useState<Record<string, boolean>>({});

  if (!data) {
    return (
      <div className="p-8 text-center text-gray-500 text-sm">
        Loading Executive Dashboard...
      </div>
    );
  }

  const { kpi, revenue_vs_budget, recurring_losses_summary, strategic_risks, decisions_requiring_approval, ai_insights, high_level_causes } = data;

  const handleApprove = (id: string) => {
    setApprovals((prev) => ({ ...prev, [id]: true }));
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Building className="w-5 h-5 text-purple-400" />
            Executive Financial & Performance Dashboard
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">
            CEO / CFO Strategic Perspective · Revenue Realization · Contractual PPA Compliance · Risk Exposure
          </p>
        </div>
        <div className="flex items-center space-x-2 text-xs font-mono">
          <span className="px-2.5 py-1 rounded-md bg-purple-950/60 text-purple-300 border border-purple-800">
            Reporting Window: 7 Days
          </span>
          <span className="px-2.5 py-1 rounded-md bg-gray-900 text-gray-300 border border-gray-800">
            PPA: $48.50 / MWh
          </span>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Realized Energy Revenue"
          value={`$${kpi.realized_revenue_usd.toLocaleString()}`}
          unit="USD"
          subValue={`${revenue_vs_budget.target_achievement_pct}% of budget`}
          status={revenue_vs_budget.target_achievement_pct >= 95 ? 'success' : 'warning'}
          icon={<DollarSign className="w-4 h-4 text-emerald-400" />}
          comparisonText={`Budget: $${kpi.budgeted_revenue_usd.toLocaleString()}`}
        />

        <KPICard
          title="Unrealized Revenue Drag"
          value={`-$${kpi.lost_revenue_usd.toLocaleString()}`}
          unit="USD"
          subValue={`Δ ${kpi.variance_mwh.toLocaleString()} MWh`}
          status="danger"
          icon={<TrendingDown className="w-4 h-4 text-rose-400" />}
          comparisonText="Lost to equipment & curtailment"
        />

        <KPICard
          title="Net Generation Output"
          value={kpi.actual_generation_mwh.toLocaleString()}
          unit="MWh"
          subValue={`${kpi.variance_pct > 0 ? '+' : ''}${kpi.variance_pct}% vs DA Forecast`}
          status={kpi.variance_pct >= -3 ? 'success' : 'warning'}
          icon={<Zap className="w-4 h-4 text-amber-400" />}
          comparisonText={`Baseline: ${kpi.expected_generation_mwh.toLocaleString()} MWh`}
        />

        <KPICard
          title="Contractual Availability"
          value={`${kpi.availability_pct}%`}
          subValue={kpi.availability_pct >= 95.0 ? 'PPA Compliant' : 'Penalty Risk'}
          status={kpi.availability_pct >= 95.0 ? 'success' : 'danger'}
          icon={<Clock className="w-4 h-4 text-blue-400" />}
          comparisonText="Min Contractual: 95.0%"
        />
      </div>

      {/* Financial Impact & Recurring Losses Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Revenue vs Budget Breakdown */}
        <div className="bg-[#0F1626] border border-gray-800 rounded-xl p-5 shadow-lg space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-emerald-400" />
            Budget vs Actual Revenue Realization
          </h3>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-gray-900/60 border border-gray-800">
              <span className="text-gray-400">Budgeted Revenue</span>
              <span className="font-mono font-bold text-white">${revenue_vs_budget.budgeted_revenue_usd.toLocaleString()}</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-gray-900/60 border border-gray-800">
              <span className="text-gray-400">Realized Energy Sales</span>
              <span className="font-mono font-bold text-emerald-400">${revenue_vs_budget.realized_revenue_usd.toLocaleString()}</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-gray-900/60 border border-gray-800">
              <span className="text-gray-400">O&M Operations Incurred</span>
              <span className="font-mono font-bold text-amber-400">${revenue_vs_budget.opex_incurred_usd.toLocaleString()}</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-purple-950/20 border border-purple-500/30">
              <span className="text-purple-300 font-semibold">Net Operating Margin</span>
              <span className="font-mono font-bold text-purple-200">${revenue_vs_budget.net_operating_margin_usd.toLocaleString()}</span>
            </div>
          </div>
        </div>

        {/* Recurring Losses Spotlight */}
        <div className="bg-[#0F1626] border border-rose-500/20 rounded-xl p-5 shadow-lg space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <TrendingDown className="w-4 h-4 text-rose-400" />
              Recurring Controllable Losses
            </h3>
            <span className="text-[10px] font-mono uppercase bg-rose-500/10 text-rose-400 px-2 py-0.5 rounded border border-rose-500/20">
              High Priority
            </span>
          </div>

          <div className="p-3.5 bg-gray-950 rounded-xl border border-gray-800 space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-gray-400">Primary Impacted Asset</span>
              <strong className="text-white font-mono">{recurring_losses_summary.primary_asset_impacted}</strong>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-gray-400">Recurring Generation Loss</span>
              <strong className="text-rose-400 font-mono">{recurring_losses_summary.recurring_loss_mwh} MWh</strong>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-gray-400">Current Period Drag</span>
              <strong className="text-rose-400 font-mono">${recurring_losses_summary.recurring_loss_usd.toLocaleString()}</strong>
            </div>
            <div className="flex justify-between items-center text-xs pt-2 border-t border-gray-800">
              <span className="text-gray-400">Annualized Financial Exposure</span>
              <strong className="text-amber-400 font-mono text-sm">${recurring_losses_summary.annualized_risk_usd.toLocaleString()} / yr</strong>
            </div>
          </div>
          <p className="text-[11px] text-gray-400">
            Root Driver: {recurring_losses_summary.recurrence_driver}. Remediating this defect avoids recurring availability penalty risk.
          </p>
        </div>

        {/* Decisions Requiring Executive Approval */}
        <div className="bg-[#0F1626] border border-gray-800 rounded-xl p-5 shadow-lg space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <FileCheck className="w-4 h-4 text-blue-400" />
            Decisions Requiring Approval
          </h3>

          <div className="space-y-3">
            {decisions_requiring_approval.map((dec) => {
              const isApproved = approvals[dec.id];
              return (
                <div key={dec.id} className="p-3 bg-gray-950 rounded-xl border border-gray-800 text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-gray-200">{dec.title}</span>
                    <span className="text-[10px] font-mono text-amber-400 uppercase">{dec.urgency}</span>
                  </div>
                  <div className="flex justify-between text-[11px] text-gray-400 font-mono">
                    <span>
                      {dec.estimated_cost_usd ? `Cost: $${dec.estimated_cost_usd}` : `Est. Recovery: $${dec.estimated_recovery_usd}`}
                    </span>
                    {dec.projected_payback_days && <span>Payback: {dec.projected_payback_days} days</span>}
                  </div>
                  <div className="pt-1 flex justify-end">
                    {isApproved ? (
                      <span className="text-emerald-400 text-xs font-semibold flex items-center gap-1">
                        <CheckCircle className="w-3.5 h-3.5" /> Approved
                      </span>
                    ) : (
                      <button
                        onClick={() => handleApprove(dec.id)}
                        className="px-3 py-1 bg-purple-600 hover:bg-purple-500 text-white rounded text-[11px] font-semibold transition-colors"
                      >
                        Sign & Approve
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Top Attributed Causes Overview (High Level) */}
      <div className="bg-[#0F1626] border border-gray-800 rounded-xl p-5 shadow-lg space-y-4">
        <h3 className="text-sm font-bold text-white">Executive Variance Attribution Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {high_level_causes.map((c, idx) => (
            <div key={idx} className="p-4 bg-gray-950 rounded-xl border border-gray-800 text-xs space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-gray-200 truncate max-w-[200px]">{c.title}</span>
                <span className="font-mono text-gray-400">{c.share_pct}%</span>
              </div>
              <div className="flex justify-between items-baseline font-mono">
                <span className="text-rose-400 font-bold">-{c.loss_mwh} MWh</span>
                <span className="text-amber-400 font-bold">-${c.loss_usd.toLocaleString()}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AI Financial & Strategic Explanation Panel */}
      <AIIntelligencePanel initialInsights={ai_insights} currentRole="CEO" />

      {/* Drill-down modal if cause is clicked */}
      <EvidenceModal cause={selectedCause} onClose={() => setSelectedCause(null)} />
    </div>
  );
};
