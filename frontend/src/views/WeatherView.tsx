import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import {
  CloudSun,
  Sun,
  Wind,
  Thermometer,
  Cloud,
  RefreshCw,
  Database,
  Loader2,
  Calendar
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

export const WeatherView: React.FC = () => {
  const [weatherData, setWeatherData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

  const fetchWeather = async () => {
    setLoading(true);
    try {
      const data = await api.getWeatherHistory();
      setWeatherData(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWeather();
  }, []);

  const handleSync = async () => {
    setSyncing(true);
    setSyncMessage(null);
    try {
      const res = await api.syncWeather();
      setSyncMessage(res.message);
      await fetchWeather();
    } catch (err: any) {
      setSyncMessage(`Sync Error: ${err.message}`);
    } finally {
      setSyncing(false);
    }
  };

  // Format chart data
  const chartData = weatherData.map((w) => {
    const dt = new Date(w.timestamp);
    return {
      time: `${dt.getMonth() + 1}/${dt.getDate()} ${dt.getHours()}:00`,
      ghi: w.ghi_wm2,
      dni: w.dni_wm2,
      temp: w.ambient_temp_c,
      cellTemp: w.cell_temp_c,
      clouds: w.cloud_cover_pct,
      dataType: w.data_type,
    };
  });

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <CloudSun className="w-5 h-5 text-orange-400" />
            Solar Irradiance & Weather Integration (Open-Meteo)
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">
            On-site Pyranometer MET-01 & Free Open-Meteo Archive/Forecast API with Caching
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleSync}
            disabled={syncing}
            className="px-3.5 py-1.5 bg-orange-600 hover:bg-orange-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm disabled:opacity-50"
          >
            {syncing ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            Sync Open-Meteo API
          </button>
        </div>
      </div>

      {syncMessage && (
        <div className="p-3 bg-blue-950/40 border border-blue-500/30 rounded-xl text-xs text-blue-200">
          {syncMessage}
        </div>
      )}

      {/* Irradiance Telemetry Chart */}
      <div className="bg-[#0F1626] border border-gray-800 rounded-xl p-5 shadow-lg space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Sun className="w-4 h-4 text-amber-400" />
            Solar Radiation Profiles (GHI vs DNI)
          </h3>
          <span className="text-[10px] font-mono text-gray-400">
            Coordinates: 34.0522° N, 117.2437° W
          </span>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid stroke="#1F2937" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="time" stroke="#6B7280" fontSize={11} tickLine={false} interval="preserveStartEnd" />
              <YAxis stroke="#6B7280" fontSize={11} unit=" W/m²" tickLine={false} />
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
              <Line
                type="monotone"
                dataKey="ghi"
                name="Global Horizontal (GHI)"
                stroke="#F59E0B"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="dni"
                name="Direct Normal (DNI)"
                stroke="#3B82F6"
                strokeWidth={1.5}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Ambient vs Cell Temperature Chart */}
      <div className="bg-[#0F1626] border border-gray-800 rounded-xl p-5 shadow-lg space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <Thermometer className="w-4 h-4 text-rose-400" />
          Ambient Temperature vs PV Cell Operating Temperature
        </h3>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid stroke="#1F2937" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="time" stroke="#6B7280" fontSize={11} tickLine={false} interval="preserveStartEnd" />
              <YAxis stroke="#6B7280" fontSize={11} unit="°C" domain={[10, 65]} tickLine={false} />
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
              <Line
                type="monotone"
                dataKey="cellTemp"
                name="PV Module Cell Temp (°C)"
                stroke="#EF4444"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="temp"
                name="Ambient Air Temp (°C)"
                stroke="#10B981"
                strokeWidth={1.5}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Weather Records Provenance Table */}
      <div className="bg-[#0F1626] border border-gray-800 rounded-xl p-5 shadow-lg space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <Database className="w-4 h-4 text-cyan-400" />
          Weather Provenance & Classification Audit
        </h3>

        <div className="overflow-x-auto max-h-72">
          <table className="w-full text-left text-xs">
            <thead className="bg-gray-950 text-gray-400 uppercase text-[10px] font-mono border-b border-gray-800 sticky top-0">
              <tr>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">GHI (W/m²)</th>
                <th className="py-2.5 px-3">DNI (W/m²)</th>
                <th className="py-2.5 px-3">Amb Temp</th>
                <th className="py-2.5 px-3">Cell Temp</th>
                <th className="py-2.5 px-3">Clouds</th>
                <th className="py-2.5 px-3">Classification</th>
                <th className="py-2.5 px-3">Provenance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-850">
              {weatherData.slice(0, 25).map((w, idx) => (
                <tr key={idx} className="hover:bg-gray-900/60 font-mono text-[11px]">
                  <td className="py-2.5 px-3 text-gray-300">{new Date(w.timestamp).toLocaleString()}</td>
                  <td className="py-2.5 px-3 text-amber-400 font-bold">{w.ghi_wm2}</td>
                  <td className="py-2.5 px-3 text-blue-400">{w.dni_wm2}</td>
                  <td className="py-2.5 px-3 text-emerald-400">{w.ambient_temp_c}°C</td>
                  <td className="py-2.5 px-3 text-rose-400">{w.cell_temp_c}°C</td>
                  <td className="py-2.5 px-3 text-gray-400">{w.cloud_cover_pct}%</td>
                  <td className="py-2.5 px-3">
                    <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                      {w.data_type}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-gray-500 truncate max-w-xs font-sans">{w.provenance_notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
