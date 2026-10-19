import React from 'react';
import { AttributedCause } from '../types';
import { X, ShieldAlert, CheckCircle, Database, HelpCircle, Activity } from 'lucide-react';

interface EvidenceModalProps {
  cause: AttributedCause | null;
  onClose: () => void;
}

export const EvidenceModal: React.FC<EvidenceModalProps> = ({ cause, onClose }) => {
  if (!cause) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      <div className="bg-[#0D1424] border border-gray-700 rounded-2xl max-w-2xl w-full shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="p-5 border-b border-gray-800 flex items-start justify-between bg-gray-900/60">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
                {cause.category.replace('_', ' ')}
              </span>
              <span
                className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded font-mono ${
                  cause.severity === 'critical'
                    ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                    : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                }`}
              >
                {cause.severity} SEVERITY
              </span>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-gray-800 text-gray-300 font-mono">
                {cause.controllability}
              </span>
            </div>
            <h2 className="text-base font-bold text-white mt-2">{cause.title}</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-5 max-h-[75vh] overflow-y-auto">
          {/* Summary Box */}
          <div className="bg-gray-900/40 p-4 rounded-xl border border-gray-800">
            <p className="text-xs text-gray-300 leading-relaxed">{cause.description}</p>
          </div>

          {/* Metric Badges */}
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 bg-gray-950 rounded-lg border border-gray-800">
              <span className="text-[10px] text-gray-400 uppercase font-semibold">Attributed Energy Loss</span>
              <p className="text-lg font-bold text-rose-400 font-mono mt-0.5">{cause.attributed_loss_mwh.toLocaleString()} MWh</p>
              <span className="text-[10px] text-gray-500 font-mono">{cause.share_of_variance_pct}% of total variance</span>
            </div>
            <div className="p-3 bg-gray-950 rounded-lg border border-gray-800">
              <span className="text-[10px] text-gray-400 uppercase font-semibold">Financial Loss Impact</span>
              <p className="text-lg font-bold text-amber-400 font-mono mt-0.5">${cause.attributed_financial_loss_usd.toLocaleString()}</p>
              <span className="text-[10px] text-gray-500 font-mono">PPA Tariff @ $48.50/MWh</span>
            </div>
            <div className="p-3 bg-gray-950 rounded-lg border border-gray-800">
              <span className="text-[10px] text-gray-400 uppercase font-semibold">Attribution Confidence</span>
              <p className="text-lg font-bold text-emerald-400 font-mono mt-0.5">{(cause.confidence_score * 100).toFixed(0)}%</p>
              <span className="text-[10px] text-gray-500 truncate">{cause.confidence_basis.replace(/_/g, ' ')}</span>
            </div>
          </div>

          {/* Attribution Methodology */}
          <div className="border border-gray-800 rounded-xl p-4 bg-gray-900/20 space-y-2 text-xs">
            <div className="flex items-center space-x-2 text-gray-300 font-medium">
              <Activity className="w-4 h-4 text-blue-400" />
              <span>Calculation Method:</span>
              <code className="text-blue-300 bg-blue-950/60 px-2 py-0.5 rounded font-mono">
                {cause.calculation_method}
              </code>
            </div>
            <p className="text-gray-400 text-[11px]">
              Calculated using peer asset generation benchmark delta during active fault hours to prevent double-counting.
            </p>
          </div>

          {/* Concrete Evidence References */}
          <div>
            <h4 className="text-xs font-bold text-gray-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-emerald-400" />
              Verifiable Evidence Records ({cause.evidence.length})
            </h4>

            {cause.evidence.length === 0 ? (
              <p className="text-xs text-gray-500 italic p-3 bg-gray-950 rounded-lg">No direct telemetry records linked.</p>
            ) : (
              <div className="space-y-2">
                {cause.evidence.map((ev, idx) => (
                  <div key={idx} className="p-3 bg-gray-950 rounded-lg border border-gray-800 text-xs space-y-1.5">
                    <div className="flex items-center justify-between text-gray-400">
                      <span className="font-mono text-blue-400 font-semibold">{ev.source_id}</span>
                      <span className="text-[10px]">{ev.source_type}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                      <div>
                        <span className="text-gray-500">Observed Metric: </span>
                        <strong className="text-rose-400 font-mono">{String(ev.metric_value)}</strong>
                      </div>
                      {ev.baseline_value && (
                        <div>
                          <span className="text-gray-500">Benchmark Baseline: </span>
                          <strong className="text-emerald-400 font-mono">{String(ev.baseline_value)}</strong>
                        </div>
                      )}
                    </div>
                    <p className="text-gray-400 text-[11px] pt-0.5">{ev.description}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-800 bg-gray-900/60 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white text-xs font-semibold rounded-lg transition-colors"
          >
            Close Drill-Down
          </button>
        </div>
      </div>
    </div>
  );
};
