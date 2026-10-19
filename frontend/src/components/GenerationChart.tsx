import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid
} from 'recharts';
import { TimeSeriesPoint } from '../types';

interface GenerationChartProps {
  data: TimeSeriesPoint[];
}

export const GenerationChart: React.FC<GenerationChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="h-72 flex items-center justify-center text-gray-500 border border-gray-800 rounded-xl bg-gray-900/30">
        No generation telemetry data found for the selected window.
      </div>
    );
  }

  // Format data for chart
  const formatted = data.map((d) => {
    const dt = new Date(d.timestamp);
    return {
      ...d,
      timeLabel: `${dt.getMonth() + 1}/${dt.getDate()} ${dt.getHours()}:00`,
    };
  });

  return (
    <div className="bg-[#0F1626] border border-gray-800 rounded-xl p-5 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-white">
            Hourly Plant Power Output: Expected vs Actual
          </h3>
          <p className="text-xs text-gray-400 mt-0.5">
            50 MW solar generation curve correlated with on-site pyranometer GHI irradiance
          </p>
        </div>
        <div className="flex items-center space-x-4 text-xs font-mono">
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
            <span className="text-gray-300">Actual (MW)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-400"></span>
            <span className="text-gray-300">Expected (MW)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span>
            <span className="text-gray-300">GHI (W/m²)</span>
          </div>
        </div>
      </div>

      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={formatted} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid stroke="#1F2937" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="timeLabel"
              stroke="#6B7280"
              fontSize={11}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              yAxisId="power"
              stroke="#6B7280"
              fontSize={11}
              domain={[0, 55]}
              unit=" MW"
              tickLine={false}
            />
            <YAxis
              yAxisId="ghi"
              orientation="right"
              stroke="#6B7280"
              fontSize={11}
              domain={[0, 1000]}
              unit=" W/m²"
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#111827',
                borderColor: '#374151',
                borderRadius: '8px',
                fontSize: '12px',
                color: '#F9FAFB',
              }}
            />
            {/* Variance Shading */}
            <Area
              yAxisId="power"
              type="monotone"
              dataKey="actual_mw"
              fill="#10B981"
              fillOpacity={0.15}
              stroke="none"
            />
            {/* Expected MW Line */}
            <Line
              yAxisId="power"
              type="monotone"
              dataKey="expected_mw"
              name="Expected MW"
              stroke="#3B82F6"
              strokeWidth={2}
              strokeDasharray="4 4"
              dot={false}
            />
            {/* Actual MW Line */}
            <Line
              yAxisId="power"
              type="monotone"
              dataKey="actual_mw"
              name="Actual MW"
              stroke="#10B981"
              strokeWidth={2.5}
              dot={false}
            />
            {/* GHI Line */}
            <Line
              yAxisId="ghi"
              type="monotone"
              dataKey="ghi_actual"
              name="Observed GHI"
              stroke="#F59E0B"
              strokeWidth={1.5}
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
