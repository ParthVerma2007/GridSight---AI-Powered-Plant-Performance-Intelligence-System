import React, { useState } from 'react';
import { TechnicianDashboardResponse } from '../types';
import { api } from '../services/api';
import { AIIntelligencePanel } from '../components/AIIntelligencePanel';
import {
  Wrench,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Lock,
  Thermometer,
  Zap,
  Activity,
  FileText,
  Clock,
  Check
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend
} from 'recharts';

interface TechnicianViewProps {
  data: TechnicianDashboardResponse | null;
  onRefresh: () => void;
}

export const TechnicianView: React.FC<TechnicianViewProps> = ({ data, onRefresh }) => {
  const [verifyingId, setVerifyingId] = useState<number | null>(null);

  if (!data) {
    return (
      <div className="p-8 text-center text-gray-500 text-sm">
        Loading Field Technician Dashboard...
      </div>
    );
  }

  const {
    asset_status_list,
    active_alarms,
    sensor_trends,
    work_orders,
    maintenance_history,
    ai_troubleshooting,
    safety_interlock_notice,
  } = data;

  const handleVerifySafety = async (woId: number) => {
    setVerifyingId(woId);
    try {
      await api.verifySafetyAndLOTO(woId);
      onRefresh();
    } catch (err: any) {
      alert(`Error verifying safety: ${err.message}`);
    } finally {
      setVerifyingId(null);
    }
  };

  // Prepare sensor trends data (comparing INV-04 with healthy INV-01)
  const inv4Trends = sensor_trends['INV-04'] || [];
  const inv1Trends = sensor_trends['INV-01'] || [];

  const trendChartData = inv4Trends.map((t, idx) => {
    const peer = inv1Trends[idx] || {};
    const dt = new Date(t.timestamp);
    return {
      time: `${dt.getMonth() + 1}/${dt.getDate()} ${dt.getHours()}:00`,
      inv4_temp: t.temp_c,
      inv1_temp: peer.temp_c,
      inv4_kw: t.ac_power_kw,
      inv1_kw: peer.ac_power_kw,
      threshold_temp: 70.0,
    };
  });

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Wrench className="w-5 h-5 text-amber-400" />
            Field Engineering & Asset Troubleshooting Center
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Component health · Sensor diagnostics · Work order execution · Safety isolation compliance
          </p>
        </div>
        <div className="flex items-center space-x-2 text-xs font-mono">
          <span className="px-2.5 py-1 rounded-md bg-amber-950/60 text-amber-300 border border-amber-800">
            Field Safety Protocol: SOP-ELEC-01 LOTO Active
          </span>
        </div>
      </div>

      {/* Mandatory Safety Interlock Warning Notice */}
      <div className="p-4 bg-rose-950/30 border border-rose-500/40 rounded-xl flex items-start space-x-3 text-rose-200 shadow-md">
        <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
        <div className="text-xs space-y-1">
          <p className="font-bold text-rose-300 uppercase tracking-wide">
            Mandatory Electrical Safety Compliance Notice (NFPA 70E / OSHA 1910.147)
          </p>
          <p className="leading-relaxed text-gray-300">{safety_interlock_notice}</p>
        </div>
      </div>

      {/* Asset Status Fleet Grid */}
      <div className="bg-[#0F1626] border border-gray-800 rounded-xl p-5 shadow-lg space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            Solar Inverter Fleet Operating Status (10 Units · 50 MW Total)
          </h3>
          <span className="text-[11px] font-mono text-gray-400">
            Updated live from equipment telemetry
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {asset_status_list.map((asset) => {
            const isFault = asset.status === 'fault_trip' || asset.status === 'offline';
            const isDegraded = asset.status === 'degraded';

            return (
              <div
                key={asset.asset_id}
                className={`p-3 rounded-xl border transition-all text-xs space-y-1.5 ${
                  isFault
                    ? 'bg-rose-950/20 border-rose-500/40'
                    : isDegraded
                    ? 'bg-amber-950/20 border-amber-500/30'
                    : 'bg-gray-950 border-gray-800'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white font-mono">{asset.asset_id}</span>
                  <span
                    className={`w-2 h-2 rounded-full ${
                      isFault ? 'bg-rose-500 animate-ping' : isDegraded ? 'bg-amber-400' : 'bg-emerald-400'
                    }`}
                  />
                </div>
                <div className="flex justify-between text-[11px] text-gray-400">
                  <span>Output:</span>
                  <strong className="text-gray-200 font-mono">
                    {asset.latest_ac_kw !== undefined && asset.latest_ac_kw !== null ? `${asset.latest_ac_kw} kW` : '0 kW'}
                  </strong>
                </div>
                <div className="flex justify-between text-[11px] text-gray-400">
                  <span>Temp:</span>
                  <strong className={`font-mono ${isFault || isDegraded ? 'text-rose-400' : 'text-gray-300'}`}>
                    {asset.latest_temp_c !== undefined && asset.latest_temp_c !== null ? `${asset.latest_temp_c}°C` : '--'}
                  </strong>
                </div>
                <div className="pt-1 text-[10px] font-mono uppercase truncate text-gray-500">
                  {asset.latest_alarm ? (
                    <span className="text-rose-400 font-bold">{asset.latest_alarm}</span>
                  ) : (
                    'Normal Operation'
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Sensor Trends Diagnostic Chart (Thermal Fault Inspection) */}
      <div className="bg-[#0F1626] border border-gray-800 rounded-xl p-5 shadow-lg space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Thermometer className="w-4 h-4 text-rose-400" />
              Thermal Trip Diagnostics: Faulted Inverter INV-04 vs Healthy Peer INV-01
            </h3>
            <p className="text-xs text-gray-400 mt-0.5">
              Demonstrating thermal divergence reaching 74°C trip threshold vs 50°C baseline
            </p>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
            Trip Setpoint: 70.0°C
          </span>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trendChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid stroke="#1F2937" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="time" stroke="#6B7280" fontSize={11} tickLine={false} interval="preserveStartEnd" />
              <YAxis stroke="#6B7280" fontSize={11} domain={[20, 85]} unit="°C" tickLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#111827',
                  borderColor: '#374151',
                  borderRadius: '8px',
                  fontSize: '12px',
                  color: '#F9FAFB',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              {/* Trip Threshold Line */}
              <Line
                type="monotone"
                dataKey="threshold_temp"
                name="70°C Trip Setpoint"
                stroke="#EF4444"
                strokeWidth={1.5}
                strokeDasharray="4 4"
                dot={false}
              />
              {/* Faulted Inverter INV-04 Temp */}
              <Line
                type="monotone"
                dataKey="inv4_temp"
                name="INV-04 Heatsink Temp (°C)"
                stroke="#F43F5E"
                strokeWidth={2.5}
                dot={false}
              />
              {/* Peer Inverter INV-01 Temp */}
              <Line
                type="monotone"
                dataKey="inv1_temp"
                name="INV-01 Peer Benchmark Temp (°C)"
                stroke="#10B981"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Work Orders & Alarms Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Work Orders with LOTO Button */}
        <div className="bg-[#0F1626] border border-gray-800 rounded-xl p-5 shadow-lg space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <FileText className="w-4 h-4 text-blue-400" />
            Field Work Orders & LOTO Verification ({work_orders.length})
          </h3>

          <div className="space-y-3">
            {work_orders.map((wo: any) => (
              <div key={wo.id} className="p-3.5 bg-gray-950 rounded-xl border border-gray-800 text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white font-mono">{wo.work_order_number}</span>
                  <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20 font-mono text-[10px]">
                    {wo.priority}
                  </span>
                </div>
                <h4 className="font-semibold text-gray-200">{wo.title}</h4>
                <p className="text-[11px] text-gray-400">{wo.description}</p>
                <div className="flex items-center justify-between text-[11px] text-gray-400 pt-1">
                  <span>Assigned: <strong className="text-gray-300">{wo.assigned_technician}</strong></span>
                  <span>Procedure: <strong className="text-blue-300 font-mono">{wo.procedure_code}</strong></span>
                </div>

                {/* Safety LOTO Action */}
                <div className="pt-2 border-t border-gray-850 flex items-center justify-between">
                  {wo.safety_interlock_verified ? (
                    <span className="text-emerald-400 text-xs font-semibold flex items-center gap-1 font-mono">
                      <Check className="w-4 h-4" /> LOTO Verified & Locked Out
                    </span>
                  ) : (
                    <button
                      onClick={() => handleVerifySafety(wo.id)}
                      disabled={verifyingId === wo.id}
                      className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
                    >
                      <Lock className="w-3.5 h-3.5" />
                      {verifyingId === wo.id ? 'Verifying...' : 'Verify LOTO Isolation'}
                    </button>
                  )}
                  <span className="text-[10px] text-gray-500 uppercase font-mono">{wo.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Alarms History */}
        <div className="bg-[#0F1626] border border-gray-800 rounded-xl p-5 shadow-lg space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400" />
            Active & Recent Fault Alarms ({active_alarms.length})
          </h3>

          <div className="space-y-2 max-h-96 overflow-y-auto">
            {active_alarms.map((al: any) => (
              <div key={al.id} className="p-3 bg-gray-950 rounded-lg border border-gray-800 text-xs space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-rose-400 font-mono">{al.alarm_code}</span>
                  <span className="text-[10px] text-gray-500 font-mono">
                    {new Date(al.timestamp).toLocaleString()}
                  </span>
                </div>
                <p className="text-gray-300 text-[11px]">{al.description}</p>
                <div className="flex items-center justify-between text-[10px] text-gray-500 font-mono">
                  <span>Asset: <strong className="text-white">{al.asset_id}</strong></span>
                  <span>Recorded Temp: <strong className="text-rose-400">{al.inverter_temp_c}°C</strong></span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI Technician Troubleshooting & Checklist Panel */}
      <AIIntelligencePanel initialInsights={ai_troubleshooting} currentRole="TECHNICIAN" />
    </div>
  );
};
