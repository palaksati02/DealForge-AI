import React, { useEffect, useState } from 'react';
import { ApprovalItem, User } from '../types';
import { ApiClient } from '../api/client';
import { ShieldCheck, CheckCircle2, XCircle, AlertTriangle, RefreshCw, FileText, UserCheck } from 'lucide-react';

interface Props {
  currentUser: User | null;
  onApprovalComplete: (requestId: string) => void;
}

export const ApprovalCenter: React.FC<Props> = ({ currentUser, onApprovalComplete }) => {
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [commentMap, setCommentMap] = useState<Record<string, string>>({});
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<{ id: string; text: string; type: 'success' | 'error' } | null>(null);

  const loadApprovals = async () => {
    setLoading(true);
    try {
      const data = await ApiClient.getPendingApprovals();
      setApprovals(data);
    } catch (err) {
      console.error('Error fetching pending approvals:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApprovals();
  }, []);

  const handleDecision = async (approval: ApprovalItem, decision: 'APPROVED' | 'REJECTED') => {
    setProcessingId(approval.approval_id);
    setActionMessage(null);
    try {
      const decider = currentUser?.full_name || 'Authorized Finance Reviewer';
      const comments = commentMap[approval.approval_id] || '';

      await ApiClient.submitApprovalDecision(
        approval.request_id,
        decision,
        decider,
        comments
      );

      setActionMessage({
        id: approval.approval_id,
        text: `Decision '${decision}' recorded successfully. Purchase order generated.`,
        type: 'success',
      });

      setTimeout(() => {
        loadApprovals();
        onApprovalComplete(approval.request_id);
      }, 1500);
    } catch (err: any) {
      setActionMessage({
        id: approval.approval_id,
        text: err.message || 'Approval action failed',
        type: 'error',
      });
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="bg-brand-800/60 border border-brand-700/60 rounded-xl p-5 backdrop-blur-md flex justify-between items-center">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-amber-400" />
            Human-in-the-Loop Governance & Approval Center
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Role-gated authorization for transactions exceeding enterprise thresholds or requiring governance exception sign-off
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-3 py-1 bg-brand-900/80 border border-brand-700 rounded-lg text-xs">
            <UserCheck className="w-3.5 h-3.5 text-sky-400" />
            <span className="text-slate-400">Current Signer: </span>
            <span className="font-semibold text-white">{currentUser?.role_name || 'Procurement Manager'}</span>
          </div>
          <button
            onClick={loadApprovals}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-slate-300 bg-brand-700/80 hover:bg-brand-600 rounded-lg transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {approvals.length > 0 ? (
        <div className="space-y-4">
          {approvals.map((appr) => {
            const comments = commentMap[appr.approval_id] || '';
            const isProcessing = processingId === appr.approval_id;

            return (
              <div
                key={appr.approval_id}
                className="bg-brand-800/50 border border-brand-700/60 rounded-xl p-5 space-y-4 shadow-lg backdrop-blur-md"
              >
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 pb-3 border-b border-brand-700/50">
                  <div>
                    <span className="text-xs font-bold text-white uppercase tracking-wider">
                      Approval Request #{appr.approval_id.slice(0, 8)}
                    </span>
                    <span className="text-xs text-slate-400 ml-2 font-mono">
                      (Req ID: {appr.request_id.slice(0, 8)}...)
                    </span>
                  </div>
                  <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
                    AWAITING SIGN-OFF
                  </span>
                </div>

                {/* Evidence Metrics */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-brand-900/60 p-3 rounded-lg border border-brand-700/40">
                  <div>
                    <div className="text-[11px] text-slate-400">Vendor Recommended</div>
                    <div className="text-xs font-bold text-white mt-0.5">{appr.vendor_name || 'Top Rank Supplier'}</div>
                  </div>
                  <div>
                    <div className="text-[11px] text-slate-400">Total Commitment Value</div>
                    <div className="text-xs font-bold text-emerald-400 font-mono mt-0.5">
                      ₹{Number(appr.total_amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </div>
                  </div>
                  <div>
                    <div className="text-[11px] text-slate-400">Budget Limit Authorized</div>
                    <div className="text-xs font-bold text-slate-200 font-mono mt-0.5">
                      ₹{Number(appr.budget_limit || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </div>
                  </div>
                </div>

                {/* Risk Assessment & Trigger */}
                <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg text-xs text-slate-200 space-y-1">
                  <div className="flex items-center gap-1.5 font-bold text-amber-400">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Governance Policy Trigger:
                  </div>
                  <div className="text-slate-300 leading-relaxed">
                    {appr.approval_reason}
                  </div>
                </div>

                {/* Comments Input */}
                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                    Approver Comments & Decision Justification
                  </label>
                  <textarea
                    value={comments}
                    onChange={(e) =>
                      setCommentMap({ ...commentMap, [appr.approval_id]: e.target.value })
                    }
                    placeholder="e.g. Approved as all technical specifications, warranties and budget limits have been audited."
                    rows={2}
                    className="w-full bg-brand-900/80 border border-brand-700 rounded-lg p-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                  />
                </div>

                {actionMessage && actionMessage.id === appr.approval_id && (
                  <div
                    className={`p-2.5 rounded-lg text-xs ${
                      actionMessage.type === 'success'
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                    }`}
                  >
                    {actionMessage.text}
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex justify-end gap-3 pt-2">
                  <button
                    type="button"
                    disabled={isProcessing}
                    onClick={() => handleDecision(appr, 'REJECTED')}
                    className="flex items-center gap-1.5 px-4 py-2 bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/40 text-rose-300 font-semibold text-xs rounded-lg transition disabled:opacity-50"
                  >
                    <XCircle className="w-4 h-4" />
                    Reject / Request Replan
                  </button>

                  <button
                    type="button"
                    disabled={isProcessing}
                    onClick={() => handleDecision(appr, 'APPROVED')}
                    className="flex items-center gap-1.5 px-5 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-900 font-bold text-xs rounded-lg shadow-lg shadow-emerald-500/20 transition disabled:opacity-50"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    {isProcessing ? 'Recording Commitment...' : 'Approve & Issue Purchase Order'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="bg-brand-800/40 border border-brand-700/40 rounded-xl p-12 text-center text-slate-500">
          <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-60" />
          No pending approvals requiring sign-off. All active workflows are either auto-approved or running smoothly.
        </div>
      )}
    </div>
  );
};
