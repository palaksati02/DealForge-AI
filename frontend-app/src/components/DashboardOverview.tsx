import React, { useEffect, useState } from 'react';
import { DashboardSummary } from '../types';
import { ApiClient } from '../api/client';
import { 
  FileText, 
  RefreshCw, 
  Clock, 
  CheckCircle2, 
  DollarSign, 
  TrendingUp, 
  Star, 
  PlusCircle, 
  ArrowRight,
  ShieldAlert
} from 'lucide-react';

interface Props {
  onSelectRequest: (requestId: string) => void;
  onNavigateNew: () => void;
}

export const DashboardOverview: React.FC<Props> = ({ onSelectRequest, onNavigateNew }) => {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const summary = await ApiClient.getDashboardSummary();
      setData(summary);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to backend API');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'FINALIZED':
      case 'COMPLETED':
      case 'APPROVED':
        return 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30';
      case 'AWAITING_APPROVAL':
      case 'WAITING_FOR_APPROVAL':
      case 'PAUSED':
        return 'bg-amber-500/20 text-amber-400 border border-amber-500/30';
      case 'REJECTED':
      case 'FAILED':
        return 'bg-rose-500/20 text-rose-400 border border-rose-500/30';
      default:
        return 'bg-sky-500/20 text-sky-400 border border-sky-500/30';
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner Actions */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-brand-800/60 border border-brand-700/60 p-4 rounded-xl backdrop-blur-md">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            Procurement Operations Cockpit
          </h2>
          <p className="text-xs text-slate-400">
            Real-time multi-agent orchestration backed by Google ADK, CrewAI, MCP tools & MySQL
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 bg-brand-700/80 hover:bg-brand-600 rounded-lg transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={onNavigateNew}
            className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold text-white bg-sky-500 hover:bg-sky-400 rounded-lg shadow-lg shadow-sky-500/20 transition"
          >
            <PlusCircle className="w-4 h-4" />
            New Purchase Request
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 text-rose-400 rounded-xl text-sm flex items-center gap-3">
          <ShieldAlert className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* KPI Metrics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-brand-800/50 border border-brand-700/50 rounded-xl p-4">
          <div className="flex justify-between items-center text-slate-400 text-xs mb-1">
            <span>Total Requests</span>
            <FileText className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold text-white">{data?.total_requests ?? 0}</div>
          <div className="text-[10px] text-slate-500 mt-1">Submitted to system</div>
        </div>

        <div className="bg-brand-800/50 border border-brand-700/50 rounded-xl p-4">
          <div className="flex justify-between items-center text-slate-400 text-xs mb-1">
            <span>Active Workflows</span>
            <RefreshCw className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold text-sky-400">{data?.active_workflows ?? 0}</div>
          <div className="text-[10px] text-slate-500 mt-1">ADK Pipeline active</div>
        </div>

        <div className="bg-brand-800/50 border border-brand-700/50 rounded-xl p-4">
          <div className="flex justify-between items-center text-slate-400 text-xs mb-1">
            <span>Pending Approvals</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400">{data?.pending_approvals ?? 0}</div>
          <div className="text-[10px] text-slate-500 mt-1">Awaiting sign-off</div>
        </div>

        <div className="bg-brand-800/50 border border-brand-700/50 rounded-xl p-4">
          <div className="flex justify-between items-center text-slate-400 text-xs mb-1">
            <span>Purchase Orders</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400">{data?.issued_purchase_orders ?? 0}</div>
          <div className="text-[10px] text-slate-500 mt-1">Committed in MySQL</div>
        </div>

        <div className="bg-brand-800/50 border border-brand-700/50 rounded-xl p-4">
          <div className="flex justify-between items-center text-slate-400 text-xs mb-1">
            <span>Approved Spend</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-white">
            ₹{Number(data?.total_spend_approved || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
          </div>
          <div className="text-[10px] text-slate-500 mt-1">Total committed value</div>
        </div>

        <div className="bg-brand-800/50 border border-brand-700/50 rounded-xl p-4">
          <div className="flex justify-between items-center text-slate-400 text-xs mb-1">
            <span>Projected Savings</span>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-emerald-400">
            ₹{Number(data?.estimated_savings || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
          </div>
          <div className="text-[10px] text-slate-500 mt-1">Negotiated delta</div>
        </div>
      </div>

      {/* Recent Requests Table */}
      <div className="bg-brand-800/50 border border-brand-700/50 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-brand-700/50 flex justify-between items-center">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <span>🕒 Recent Purchase Requests</span>
          </h3>
          <span className="text-xs text-slate-400">Live MySQL Relational Records</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-brand-900/60 text-slate-400 uppercase font-semibold border-b border-brand-700/50">
              <tr>
                <th className="py-3 px-4">Request ID</th>
                <th className="py-3 px-4">Requirement / Description</th>
                <th className="py-3 px-4">Requester</th>
                <th className="py-3 px-4">Qty</th>
                <th className="py-3 px-4">Budget Ceiling</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-700/30 text-slate-300">
              {data?.recent_requests && data.recent_requests.length > 0 ? (
                data.recent_requests.map((r) => (
                  <tr key={r.request_id} className="hover:bg-brand-700/20 transition">
                    <td className="py-3 px-4 font-mono text-[11px] text-sky-400">
                      {r.request_id.slice(0, 8)}...
                    </td>
                    <td className="py-3 px-4 max-w-xs truncate font-medium text-white" title={r.raw_request_text}>
                      {r.raw_request_text}
                    </td>
                    <td className="py-3 px-4">{r.requester}</td>
                    <td className="py-3 px-4 font-semibold">{r.quantity}</td>
                    <td className="py-3 px-4 font-mono font-medium">
                      ₹{Number(r.budget_limit).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${getStatusBadge(r.status)}`}>
                        {r.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => onSelectRequest(r.request_id)}
                        className="inline-flex items-center gap-1 text-xs text-sky-400 hover:text-sky-300 font-medium transition"
                      >
                        View Flow <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No procurement requests recorded yet. Click '+ New Purchase Request' to initiate.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
