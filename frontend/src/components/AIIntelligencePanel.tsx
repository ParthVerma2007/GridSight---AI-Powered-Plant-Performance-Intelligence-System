import React, { useState } from 'react';
import { AIExplanationResponse, UserRole } from '../types';
import { api } from '../services/api';
import {
  Sparkles,
  CheckCircle2,
  HelpCircle,
  AlertTriangle,
  Lightbulb,
  Send,
  Loader2,
  FileText,
  ShieldAlert,
  ArrowRight
} from 'lucide-react';

interface AIIntelligencePanelProps {
  initialInsights: AIExplanationResponse | null;
  currentRole: UserRole;
}

export const AIIntelligencePanel: React.FC<AIIntelligencePanelProps> = ({
  initialInsights,
  currentRole,
}) => {
  const [insights, setInsights] = useState<AIExplanationResponse | null>(initialInsights);
  const [query, setQuery] = useState('');
  const [isQuerying, setIsQuerying] = useState(false);
  const [activeTab, setActiveTab] = useState<'facts' | 'hypotheses' | 'actions' | 'risks'>('facts');

  React.useEffect(() => {
    setInsights(initialInsights);
  }, [initialInsights]);

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isQuerying) return;

    setIsQuerying(true);
    try {
      const resp = await api.queryAI(query.trim(), currentRole);
      setInsights(resp);
      setQuery('');
    } catch (err: any) {
      alert(`AI Query Error: ${err.message}`);
    } finally {
      setIsQuerying(false);
    }
  };

  if (!insights) {
    return (
      <div className="p-6 bg-gray-900/30 border border-gray-800 rounded-xl text-center text-gray-500 text-xs">
        Loading AI role-specific intelligence...
      </div>
    );
  }

  return (
    <div className="bg-[#0F1626] border border-blue-500/20 rounded-xl p-5 shadow-xl space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-gray-800">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              AI Plant Intelligence Architect
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                ROLE: {insights.role}
              </span>
            </h3>
            <p className="text-[11px] text-gray-400">
              Ground-truthed causal interpretation · Strict distinction of facts vs hypotheses
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-[10px] font-mono text-gray-400">
          <span className="px-2 py-0.5 rounded bg-gray-900 border border-gray-800">
            Provider: <strong className="text-gray-300">{insights.provider_used}</strong>
          </span>
          <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            {insights.validation_status}
          </span>
        </div>
      </div>

      {/* Primary Narrative Summary */}
      <div className="p-4 bg-gradient-to-r from-blue-950/20 to-purple-950/20 rounded-xl border border-blue-500/20">
        <p className="text-xs text-gray-200 leading-relaxed font-sans">
          {insights.summary}
        </p>
      </div>

      {/* Segment Navigation */}
      <div className="flex items-center space-x-2 border-b border-gray-800 pb-2">
        <button
          onClick={() => setActiveTab('facts')}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 ${
            activeTab === 'facts'
              ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          Verified Facts ({insights.verified_facts.length})
        </button>

        <button
          onClick={() => setActiveTab('hypotheses')}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 ${
            activeTab === 'hypotheses'
              ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <HelpCircle className="w-3.5 h-3.5" />
          Hypotheses & Unknowns ({insights.hypotheses.length + insights.unknowns.length})
        </button>

        <button
          onClick={() => setActiveTab('actions')}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 ${
            activeTab === 'actions'
              ? 'bg-blue-500/15 text-blue-300 border border-blue-500/30'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <Lightbulb className="w-3.5 h-3.5" />
          Recommended Actions ({insights.recommended_actions.length})
        </button>

        <button
          onClick={() => setActiveTab('risks')}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 ${
            activeTab === 'risks'
              ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <AlertTriangle className="w-3.5 h-3.5" />
          Risks ({insights.strategic_or_operational_risks.length})
        </button>
      </div>

      {/* Tab Panels */}
      <div className="min-h-[140px] text-xs">
        {activeTab === 'facts' && (
          <div className="space-y-2">
            <h5 className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">
              Mathematical & Physical Verified Ground Truth
            </h5>
            <ul className="space-y-1.5">
              {insights.verified_facts.map((fact, idx) => (
                <li key={idx} className="flex items-start gap-2 text-gray-300 bg-gray-900/40 p-2 rounded-lg border border-gray-800/60">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                  <span>{fact}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {activeTab === 'hypotheses' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="space-y-2">
              <h5 className="text-[11px] font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1">
                <HelpCircle className="w-3 h-3" />
                Working Hypotheses
              </h5>
              <ul className="space-y-1.5">
                {insights.hypotheses.map((h, idx) => (
                  <li key={idx} className="text-gray-300 bg-gray-900/40 p-2 rounded-lg border border-amber-500/20">
                    {h}
                  </li>
                ))}
              </ul>
            </div>

            <div className="space-y-2">
              <h5 className="text-[11px] font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1">
                <FileText className="w-3 h-3" />
                Unknowns & Information Gaps
              </h5>
              <ul className="space-y-1.5">
                {insights.unknowns.map((u, idx) => (
                  <li key={idx} className="text-gray-300 bg-gray-900/40 p-2 rounded-lg border border-gray-800">
                    {u}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {activeTab === 'actions' && (
          <div className="space-y-2">
            <div className="space-y-2">
              {insights.recommended_actions.map((act, idx) => (
                <div key={idx} className="p-3 bg-gray-900/60 rounded-xl border border-gray-800 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-mono">
                      {act.priority} · {act.owner_role}
                    </span>
                  </div>
                  <p className="text-xs font-semibold text-white mt-1">{act.action}</p>
                  <p className="text-[11px] text-gray-400">{act.rationale}</p>
                  {act.safety_precaution && (
                    <div className="mt-1 flex items-center gap-1 text-[11px] text-rose-400 bg-rose-950/30 p-1.5 rounded border border-rose-500/20">
                      <ShieldAlert className="w-3.5 h-3.5 shrink-0" />
                      <span>{act.safety_precaution}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'risks' && (
          <div className="space-y-2">
            <ul className="space-y-2">
              {insights.strategic_or_operational_risks.map((risk, idx) => (
                <li key={idx} className="flex items-start gap-2 p-2.5 bg-rose-950/20 rounded-lg border border-rose-500/20 text-rose-200">
                  <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                  <span>{risk}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Interactive Question Input */}
      <form onSubmit={handleAsk} className="pt-2 border-t border-gray-800 flex items-center gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={`Ask the AI Architect a question as ${insights.role}... (e.g. "What is our financial payback on replacing Inverter 4?")`}
          className="flex-1 bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
        />
        <button
          type="submit"
          disabled={isQuerying || !query.trim()}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 transition-colors"
        >
          {isQuerying ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
          Ask AI
        </button>
      </form>
    </div>
  );
};
