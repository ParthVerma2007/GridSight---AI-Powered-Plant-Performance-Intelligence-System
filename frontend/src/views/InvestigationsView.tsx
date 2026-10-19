import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import {
  Search,
  Plus,
  Clock,
  CheckCircle,
  AlertCircle,
  User,
  Calendar,
  Layers,
  RefreshCw,
  Loader2
} from 'lucide-react';

export const InvestigationsView: React.FC = () => {
  const [investigations, setInvestigations] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);

  // New Investigation form state
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('equipment_fault');
  const [owner, setOwner] = useState('Carlos Mendez (Operations Lead)');
  const [priority, setPriority] = useState('high');
  const [deadline, setDeadline] = useState('');
  const [description, setDescription] = useState('');
  const [actionPlan, setActionPlan] = useState('');
  const [creating, setCreating] = useState(false);

  const fetchInvestigations = async () => {
    setLoading(true);
    try {
      const data = await api.getInvestigations();
      setInvestigations(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvestigations();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await api.createInvestigation({
        title,
        cause_category: category,
        owner,
        priority,
        deadline: deadline ? new Date(deadline).toISOString() : null,
        description,
        action_plan: actionPlan,
      });
      setShowModal(false);
      setTitle('');
      setDescription('');
      setActionPlan('');
      await fetchInvestigations();
    } catch (err: any) {
      alert(`Error creating investigation: ${err.message}`);
    } finally {
      setCreating(false);
    }
  };

  const handleStatusChange = async (id: number, newStatus: string) => {
    try {
      await api.updateInvestigation(id, { status: newStatus });
      await fetchInvestigations();
    } catch (err: any) {
      alert(`Error updating status: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Search className="w-5 h-5 text-rose-400" />
            Root Cause Investigation & Corrective Action Tracker
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Operations ownership · Action items · Deadlines · Recurrence mitigation
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowModal(true)}
            className="px-3.5 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            New Investigation
          </button>
          <button
            onClick={fetchInvestigations}
            className="p-1.5 bg-gray-900 hover:bg-gray-800 text-gray-300 rounded-lg border border-gray-800"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Kanban / Cards List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {investigations.map((inv) => {
          const isCritical = inv.priority === 'critical';
          const isResolved = inv.status === 'resolved' || inv.status === 'closed';

          return (
            <div
              key={inv.id}
              className={`p-5 rounded-xl border bg-[#0F1626] shadow-lg space-y-3.5 flex flex-col justify-between ${
                isCritical ? 'border-rose-500/30' : 'border-gray-800'
              }`}
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase font-bold px-2 py-0.5 rounded bg-gray-900 border border-gray-800 text-gray-400">
                    {inv.cause_category.replace('_', ' ')}
                  </span>
                  <span
                    className={`text-[10px] font-mono uppercase font-bold px-2 py-0.5 rounded ${
                      isCritical
                        ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                    }`}
                  >
                    {inv.priority}
                  </span>
                </div>

                <h3 className="text-sm font-bold text-white leading-snug">{inv.title}</h3>
                <p className="text-xs text-gray-400 leading-relaxed">{inv.description}</p>

                {inv.action_plan && (
                  <div className="p-3 bg-gray-950 rounded-lg border border-gray-800/80 text-[11px] space-y-1">
                    <strong className="text-gray-300 font-semibold block">Action Plan:</strong>
                    <p className="text-gray-400 whitespace-pre-line">{inv.action_plan}</p>
                  </div>
                )}
              </div>

              <div className="pt-3 border-t border-gray-850 space-y-2 text-xs">
                <div className="flex items-center justify-between text-gray-400 text-[11px]">
                  <span className="flex items-center gap-1">
                    <User className="w-3.5 h-3.5 text-gray-500" />
                    {inv.owner}
                  </span>
                  {inv.deadline && (
                    <span className="flex items-center gap-1 text-amber-400 font-mono">
                      <Calendar className="w-3.5 h-3.5" />
                      {new Date(inv.deadline).toLocaleDateString()}
                    </span>
                  )}
                </div>

                {/* Status Switcher */}
                <div className="flex items-center justify-between pt-1">
                  <span className="text-[10px] uppercase font-mono text-gray-500">Status:</span>
                  <select
                    value={inv.status}
                    onChange={(e) => handleStatusChange(inv.id, e.target.value)}
                    className="bg-gray-950 border border-gray-800 rounded px-2 py-1 text-[11px] text-gray-300 focus:outline-none font-mono"
                  >
                    <option value="open">OPEN</option>
                    <option value="in_progress">IN PROGRESS</option>
                    <option value="resolved">RESOLVED</option>
                    <option value="closed">CLOSED</option>
                  </select>
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
              <Search className="w-4 h-4 text-rose-400" />
              Launch Root Cause Investigation
            </h2>

            <form onSubmit={handleCreate} className="space-y-3 text-xs">
              <div>
                <label className="block text-gray-300 font-semibold mb-1">Investigation Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Inverter 04 Thermal Cutout Root Cause"
                  className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-rose-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Category</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-white"
                  >
                    <option value="equipment_fault">Equipment Fault</option>
                    <option value="grid_curtailment">Grid Curtailment</option>
                    <option value="weather">Weather Deficit</option>
                    <option value="maintenance">Maintenance</option>
                  </select>
                </div>

                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Priority</label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-white"
                  >
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Assignee / Owner</label>
                  <input
                    type="text"
                    required
                    value={owner}
                    onChange={(e) => setOwner(e.target.value)}
                    className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-white"
                  />
                </div>

                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Resolution Deadline</label>
                  <input
                    type="date"
                    value={deadline}
                    onChange={(e) => setDeadline(e.target.value)}
                    className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Description</label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Detail observed symptoms, alarm codes, and impacted assets..."
                  className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-white"
                />
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Remediation Action Plan</label>
                <textarea
                  rows={3}
                  value={actionPlan}
                  onChange={(e) => setActionPlan(e.target.value)}
                  placeholder="Numbered corrective actions and verification steps..."
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
                  disabled={creating}
                  className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-lg font-semibold flex items-center gap-1.5"
                >
                  {creating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                  Initiate Investigation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
