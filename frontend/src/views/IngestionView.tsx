import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { IngestionBatch, QuarantineItem } from '../types';
import {
  UploadCloud,
  FileCheck,
  AlertOctagon,
  History,
  FileText,
  CheckCircle,
  RefreshCw,
  Loader2,
  FileCode
} from 'lucide-react';

export const IngestionView: React.FC = () => {
  const [batches, setBatches] = useState<IngestionBatch[]>([]);
  const [quarantineItems, setQuarantineItems] = useState<QuarantineItem[]>([]);
  const [fileType, setFileType] = useState('generation');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const loadBatchesAndQuarantine = async () => {
    setLoadingHistory(true);
    try {
      const [bList, qList] = await Promise.all([
        api.getBatches(),
        api.getQuarantinedRecords(),
      ]);
      setBatches(bList);
      setQuarantineItems(qList);
    } catch (err: any) {
      console.error('Error loading ingestion data:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    loadBatchesAndQuarantine();
  }, []);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      alert('Please select a CSV file to upload.');
      return;
    }

    setUploading(true);
    setUploadResult(null);
    try {
      const res = await api.uploadCsv(file, fileType);
      setUploadResult(res);
      setFile(null);
      await loadBatchesAndQuarantine();
    } catch (err: any) {
      alert(`Upload Failed: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <UploadCloud className="w-5 h-5 text-cyan-400" />
            Data Ingestion, Validation & Quarantine Pipeline
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Strict schema parsing · Timestamp and unit normalization · Non-destructive duplicate & quarantine handling
          </p>
        </div>
        <button
          onClick={loadBatchesAndQuarantine}
          className="px-3 py-1.5 bg-gray-900 hover:bg-gray-800 text-gray-300 rounded-lg text-xs flex items-center gap-1.5 border border-gray-800 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loadingHistory ? 'animate-spin' : ''}`} />
          Refresh Reports
        </button>
      </div>

      {/* Upload Box & Guidelines */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Form */}
        <div className="lg:col-span-2 bg-[#0F1626] border border-gray-800 rounded-xl p-5 shadow-lg space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <FileText className="w-4 h-4 text-cyan-400" />
            Upload Plant Dataset (.csv)
          </h3>

          <form onSubmit={handleUpload} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1">
                  Target Dataset Type
                </label>
                <select
                  value={fileType}
                  onChange={(e) => setFileType(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="generation">Actual Generation (MW / MWh)</option>
                  <option value="forecast">Versioned Forecasts (Day-Ahead / Intraday)</option>
                  <option value="equipment">Equipment Telemetry & Sensor Alarms</option>
                  <option value="weather">Weather Observations & Irradiance</option>
                  <option value="maintenance">Maintenance Logs & Work Orders</option>
                  <option value="workforce">Workforce Staffing & Shifts</option>
                  <option value="external_events">Grid Directives & Curtailment</option>
                  <option value="financial">Financial Tariffs & Budgets</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1">
                  Plant Identifier
                </label>
                <input
                  type="text"
                  value="helios-50 (Helios-50 Solar Farm)"
                  disabled
                  className="w-full bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-xs text-gray-400"
                />
              </div>
            </div>

            {/* File Drop Area */}
            <div className="border-2 border-dashed border-gray-800 hover:border-cyan-500/50 rounded-xl p-6 text-center bg-gray-950/40 transition-colors">
              <input
                type="file"
                accept=".csv"
                id="csvFile"
                onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
                className="hidden"
              />
              <label htmlFor="csvFile" className="cursor-pointer space-y-2 block">
                <UploadCloud className="w-8 h-8 text-cyan-400 mx-auto" />
                <p className="text-xs text-gray-300 font-medium">
                  {file ? file.name : 'Click to browse or drop CSV file here'}
                </p>
                <p className="text-[11px] text-gray-500">
                  Accepts standard RFC-4180 CSV with headers
                </p>
              </label>
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={uploading || !file}
                className="px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg flex items-center gap-2 transition-colors"
              >
                {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <UploadCloud className="w-4 h-4" />}
                {uploading ? 'Validating & Ingesting...' : 'Ingest Dataset'}
              </button>
            </div>
          </form>

          {/* Upload Result Alert */}
          {uploadResult && (
            <div className={`p-4 rounded-xl border text-xs space-y-1 ${
              uploadResult.report.quarantined_records > 0
                ? 'bg-amber-950/20 border-amber-500/30 text-amber-200'
                : 'bg-emerald-950/20 border-emerald-500/30 text-emerald-200'
            }`}>
              <div className="flex items-center justify-between font-bold">
                <span>{uploadResult.message}</span>
                <span className="font-mono">Batch: {uploadResult.batch_id}</span>
              </div>
              <p className="text-[11px] text-gray-300">{uploadResult.report.summary}</p>
            </div>
          )}
        </div>

        {/* Ingestion Rules & Standards */}
        <div className="bg-[#0F1626] border border-gray-800 rounded-xl p-5 shadow-lg space-y-3 text-xs">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
            Integrity Safeguards
          </h3>
          <ul className="space-y-2 text-gray-400 text-[11px] leading-relaxed">
            <li className="flex items-start gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-1 shrink-0" />
              <span><strong>No Silent Discarding:</strong> Malformed rows are quarantined with exact row index and raw content preserved.</span>
            </li>
            <li className="flex items-start gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-1 shrink-0" />
              <span><strong>Immutable Forecasts:</strong> Previous forecast versions are never overwritten; multiple versions coexist.</span>
            </li>
            <li className="flex items-start gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-1 shrink-0" />
              <span><strong>Unit Normalization:</strong> Automatically converts kW to MW and cleans asset identifiers (e.g. inv04 → INV-04).</span>
            </li>
            <li className="flex items-start gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-1 shrink-0" />
              <span><strong>Referential Integrity:</strong> Rejects telemetry referencing uncommissioned asset IDs.</span>
            </li>
          </ul>
        </div>
      </div>

      {/* Quarantine Inspector Table */}
      <div className="bg-[#0F1626] border border-gray-800 rounded-xl p-5 shadow-lg space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <AlertOctagon className="w-4 h-4 text-rose-400" />
            Quarantine Records Inspector ({quarantineItems.length} Quarantined Rows)
          </h3>
          <span className="text-xs text-gray-400">
            Records quarantined during ingestion validation
          </span>
        </div>

        {quarantineItems.length === 0 ? (
          <p className="text-xs text-gray-500 italic p-4 text-center bg-gray-950 rounded-lg">
            Quarantine clean. No invalid records detected in recent batches.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-950 text-gray-400 uppercase text-[10px] font-mono border-b border-gray-800">
                <tr>
                  <th className="py-2.5 px-3">Batch & File</th>
                  <th className="py-2.5 px-3">Row #</th>
                  <th className="py-2.5 px-3">Error Category</th>
                  <th className="py-2.5 px-3">Reason / Diagnostic</th>
                  <th className="py-2.5 px-3">Raw Content JSON</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-850">
                {quarantineItems.slice(0, 15).map((q) => (
                  <tr key={q.id} className="hover:bg-gray-900/60 font-mono text-[11px]">
                    <td className="py-2.5 px-3 text-cyan-400 font-semibold">{q.source_file}</td>
                    <td className="py-2.5 px-3 text-white">Row {q.row_index}</td>
                    <td className="py-2.5 px-3">
                      <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
                        {q.error_type}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-gray-300 font-sans">{q.error_detail}</td>
                    <td className="py-2.5 px-3 text-gray-500 max-w-xs truncate">{q.raw_content}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recent Ingestion Batches */}
      <div className="bg-[#0F1626] border border-gray-800 rounded-xl p-5 shadow-lg space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <History className="w-4 h-4 text-blue-400" />
          Ingestion Batch Audit History ({batches.length})
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-gray-950 text-gray-400 uppercase text-[10px] font-mono border-b border-gray-800">
              <tr>
                <th className="py-2.5 px-3">Batch ID</th>
                <th className="py-2.5 px-3">Source File</th>
                <th className="py-2.5 px-3">Type</th>
                <th className="py-2.5 px-3">Valid / Total</th>
                <th className="py-2.5 px-3">Quarantined</th>
                <th className="py-2.5 px-3">Success Rate</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-850">
              {batches.map((b) => (
                <tr key={b.batch_id} className="hover:bg-gray-900/60 font-mono text-[11px]">
                  <td className="py-2.5 px-3 text-blue-400 font-bold">{b.batch_id}</td>
                  <td className="py-2.5 px-3 text-gray-300">{b.source_file}</td>
                  <td className="py-2.5 px-3 uppercase text-gray-400">{b.file_type}</td>
                  <td className="py-2.5 px-3 text-emerald-400 font-bold">{b.valid_records} / {b.total_records}</td>
                  <td className="py-2.5 px-3 text-rose-400 font-bold">{b.quarantined_records}</td>
                  <td className="py-2.5 px-3 text-white">{b.success_rate_pct}%</td>
                  <td className="py-2.5 px-3">
                    <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                      b.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'
                    }`}>
                      {b.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-gray-500">{new Date(b.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
