import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import {
  ClipboardList,
  Lock,
  Check,
  Plus,
  AlertTriangle,
  User,
  Wrench,
  ShieldCheck,
  RefreshCw,
  Loader2
} from 'lucide-react';

export const WorkOrdersView: React.FC = () => {
  const [workOrders, setWorkOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [verifyingId, setVerifyingId] = useState<number | null>(null);

  // Form state
  const [title, setTitle] = useState('');
  const [assetId, setAssetId] = useState('INV-04');
  const [priority, setPriority] = useState('P2_HIGH');
  const [technician, setTechnician] = useState('Carlos Mendez');
  const [hours, setHours] = useState('2.5');
  const [procedureCode, setProcedureCode] = useState('SOP-INV-02');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchWorkOrders = async () => {
    setLoading(true);
    try {
      const data = await api.getWorkOrders();
      setWorkOrders(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkOrders();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.createWorkOrder({
        asset_id: assetId,
        title,
        priority,
        assigned_technician: technician,
        estimated_hours: parseFloat(hours),
        procedure_code: procedureCode,
        description,
      });
      setShowModal(false);
      setTitle('');
      setDescription('');
      await fetchWorkOrders();
    } catch (err: any) {
      alert(`Error creating work order: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleVerifyLOTO = async (id: number) => {
    setVerifyingId(id);
    try {
      await api.verifySafetyAndLOTO(id);
      await fetchWorkOrders();
    } catch (err: any) {
      alert(`Verification failed: ${err.message}`);
    } finally {
      setVerifyingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <ClipboardList className="w-5 h-5 text-emerald-400" />
            Field Work Orders & Electrical Safety Isolation
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Maintenance assignments · Lockout/Tagout (LOTO) verification · NFPA 70E compliance · Approved procedures
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowModal(true)}
            className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            Create Work Order
          </button>
          <button
            onClick={fetchWorkOrders}
            className="p-1.5 bg-gray-900 hover:bg-gray-800 text-gray-300 rounded-lg border border-gray-800"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Work Orders List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {workOrders.map((wo) => {
          const isLoto = wo.safety_interlock_verified;

          return (
            <div
              key={wo.id}
              className="p-5 rounded-xl border border-gray-800 bg-[#0F1626] shadow-lg space-y-3 flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-white">{wo.work_order_number}</span>
                  <span
                    className={`text-[10px] font-mono uppercase font-bold px-2 py-0.5 rounded ${
                      wo.priority === 'P1_CRITICAL'
                        ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                    }`}
                  >
                    {wo.priority}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-mono text-cyan-400 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/40">
                    Asset: {wo.asset_id}
                  </span>
                  <span className="text-[11px] font-mono text-gray-400">
                    Proc: {wo.procedure_code}
                  </span>
                </div>

                <h3 className="text-sm font-bold text-gray-200">{wo.title}</h3>
                <p className="text-xs text-gray-400">{wo.description}</p>
              </div>

              <div className="pt-3 border-t border-gray-850 space-y-2 text-xs">
                <div className="flex items-center justify-between text-gray-400 text-[11px]">
                  <span>Tech: <strong className="text-gray-200">{wo.assigned_technician}</strong></span>
                  <span>Est: <strong className="text-gray-200">{wo.estimated_hours}h</strong></span>
                </div>

                {/* Safety LOTO Action Box */}
                <div className="pt-1 flex items-center justify-between">
                  {isLoto ? (
                    <span className="text-emerald-400 text-xs font-semibold flex items-center gap-1.5 font-mono">
                      <ShieldCheck className="w-4 h-4" /> LOTO Verified
                    </span>
                  ) : (
                    <button
                      onClick={() => handleVerifyLOTO(wo.id)}
                      disabled={verifyingId === wo.id}
                      className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
                    >
                      <Lock className="w-3.5 h-3.5" />
                      {verifyingId === wo.id ? 'Certifying...' : 'Verify LOTO Isolation'}
                    </button>
                  )}
                  <span className="text-[10px] text-gray-500 uppercase font-mono">{wo.status}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Create Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="bg-[#0D1424] border border-gray-700 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <ClipboardList className="w-4 h-4 text-emerald-400" />
              Issue Field Work Order
            </h2>

            <form onSubmit={handleCreate} className="space-y-3 text-xs">
              <div>
                <label className="block text-gray-300 font-semibold mb-1">Work Order Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Heatsink Air Filter Replacement - INV-04"
                  className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Target Asset ID</label>
                  <select
                    value={assetId}
                    onChange={(e) => setAssetId(e.target.value)}
                    className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-white"
                  >
                    {Array.from({ length: 10 }, (_, i) => `INV-${String(i + 1).padStart(2, '0')}`).map((id) => (
                      <option key={id} value={id}>{id}</option>
                    ))}
                    <option value="MET-01">MET-01 (Weather Station)</option>
                    <option value="TX-01">TX-01 (Main Step-Up Transformer)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Priority Level</label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-white"
                  >
                    <option value="P1_CRITICAL">P1 (Critical - Outage)</option>
                    <option value="P2_HIGH">P2 (High - Degraded)</option>
                    <option value="P3_NORMAL">P3 (Normal - Scheduled)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Assigned Technician</label>
                  <input
                    type="text"
                    required
                    value={technician}
                    onChange={(e) => setTechnician(e.target.value)}
                    className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-white"
                  />
                </div>

                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Procedure Code</label>
                  <input
                    type="text"
                    required
                    value={procedureCode}
                    onChange={(e) => setProcedureCode(e.target.value)}
                    className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Description & Scope of Work</label>
                <textarea
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Specify replacement parts, inspection points, and safety precautions..."
                  className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-white"
                />
              </div>

              <div className="pt-2 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-semibold flex items-center gap-1.5"
                >
                  {submitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                  Issue Work Order
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
