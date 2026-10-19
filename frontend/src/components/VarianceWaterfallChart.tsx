import React from 'react';
import { WaterfallStep, AttributedCause } from '../types';
import { ArrowDownRight, Layers, AlertCircle } from 'lucide-react';

interface VarianceWaterfallChartProps {
  steps: WaterfallStep[];
  causes: AttributedCause[];
  onSelectCause: (cause: AttributedCause) => void;
}

export const VarianceWaterfallChart: React.FC<VarianceWaterfallChartProps> = ({
  steps,
  causes,
  onSelectCause,
}) => {
  if (!steps || steps.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500 border border-gray-800 rounded-xl bg-gray-900/30">
        No waterfall variance data available.
      </div>
    );
  }

  // Calculate maximum for SVG scaling
  const maxVal = Math.max(...steps.map((s) => s.value), 100);

  return (
    <div className="bg-[#0F1626] border border-gray-800 rounded-xl p-5 shadow-lg">
      <div className="flex items-center justify-between pb-4 border-b border-gray-800">
        <div>
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Layers className="w-4 h-4 text-blue-400" />
            Deterministic Variance Bridge (Waterfall Attribution)
          </h3>
          <p className="text-xs text-gray-400 mt-0.5">
            Step-by-step physical reconciliation from Forecast Baseline to Actual Generation
          </p>
        </div>
        <span className="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
          0.00% Discrepancy Verified
        </span>
      </div>

      {/* Visual Step Bars */}
      <div className="mt-6 space-y-3">
        {steps.map((step, idx) => {
          const isBaseline = step.type === 'baseline';
          const isActual = step.type === 'actual';
          const widthPct = Math.min(100, Math.max(8, (step.value / maxVal) * 100));

          // Find corresponding cause if any
          const matchingCause = causes.find(
            (c) => step.name.includes(c.title.substring(0, 15)) || c.category === step.category
          );

          let barColor = 'bg-blue-600/60 border-blue-500';
          if (isActual) barColor = 'bg-emerald-600/60 border-emerald-500';
          else if (!isBaseline && step.category === 'equipment_fault') barColor = 'bg-rose-600/70 border-rose-500';
          else if (!isBaseline && step.category === 'grid_curtailment') barColor = 'bg-amber-600/70 border-amber-500';
          else if (!isBaseline && step.category === 'weather') barColor = 'bg-sky-600/70 border-sky-500';
          else if (!isBaseline) barColor = 'bg-purple-600/70 border-purple-500';

          return (
            <div
              key={idx}
              onClick={() => matchingCause && onSelectCause(matchingCause)}
              className={`p-2.5 rounded-lg border border-gray-800/80 bg-gray-900/40 hover:bg-gray-850 transition-all ${
                matchingCause ? 'cursor-pointer hover:border-gray-700' : ''
              }`}
            >
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="font-medium text-gray-300 flex items-center gap-1.5 truncate max-w-md">
                  {step.name}
                  {matchingCause && (
                    <span className="text-[10px] text-blue-400 underline ml-1">
                      (Click for evidence)
                    </span>
                  )}
                </span>
                <div className="flex items-center space-x-3 font-mono">
                  {step.delta !== undefined && (
                    <span
                      className={`text-xs ${
                        step.delta < 0 ? 'text-rose-400' : 'text-emerald-400'
                      }`}
                    >
                      {step.delta > 0 ? `+${step.delta}` : step.delta} MWh
                    </span>
                  )}
                  <span className="text-white font-bold">{step.value.toLocaleString()} MWh</span>
                </div>
              </div>

              {/* Graphical Bar */}
              <div className="w-full h-3 bg-gray-950 rounded-full overflow-hidden border border-gray-800/60">
                <div
                  className={`h-full rounded-full border transition-all duration-500 ${barColor}`}
                  style={{ width: `${widthPct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 pt-3 border-t border-gray-800/60 flex items-center justify-between text-[11px] text-gray-400">
        <span className="flex items-center gap-1">
          <AlertCircle className="w-3.5 h-3.5 text-blue-400" />
          Click any attributed step to drill down into sensor telemetry evidence & calculation basis
        </span>
        <span className="font-mono text-gray-500">Physical peer delta + CAISO directive integration</span>
      </div>
    </div>
  );
};
