import React, { useEffect, useState } from 'react';
import { ProcurementReport } from '../types';
import { ApiClient } from '../api/client';
import { FileText, Download, CheckCircle2, ShieldAlert, Award, FileCode, RefreshCw } from 'lucide-react';

interface Props {
  requestId: string;
}

export const ProcurementReportView: React.FC<Props> = ({ requestId }) => {
  const [report, setReport] = useState<ProcurementReport | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await ApiClient.getReport(requestId);
      setReport(data);
    } catch (err) {
      console.error('Error fetching procurement report:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (requestId) loadData();
  }, [requestId]);

  const downloadMarkdown = () => {
    if (!report?.markdown_report) return;
    const blob = new Blob([report.markdown_report], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `dealforge-report-${requestId.slice(0, 8)}.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const downloadJSON = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `dealforge-report-${requestId.slice(0, 8)}.json`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const po = report?.purchase_order;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="bg-brand-800/60 border border-brand-700/60 rounded-xl p-5 backdrop-blur-md flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-emerald-400" />
            Executive Procurement & Governance Audit Report
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Tamper-evident, fully traceable decision documentation compiled from MySQL persistence ledger
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={downloadMarkdown}
            disabled={!report}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-brand-700 hover:bg-brand-600 text-xs text-white rounded-lg transition"
          >
            <Download className="w-3.5 h-3.5 text-sky-400" />
            Download Markdown
          </button>
          <button
            onClick={downloadJSON}
            disabled={!report}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-brand-700 hover:bg-brand-600 text-xs text-white rounded-lg transition"
          >
            <FileCode className="w-3.5 h-3.5 text-emerald-400" />
            Download JSON
          </button>
        </div>
      </div>

      {report ? (
        <div className="space-y-6">
          {/* Executive Summary Card */}
          <div className="bg-brand-800/50 border border-brand-700/50 rounded-xl p-6">
            <div className="flex justify-between items-start mb-4 pb-3 border-b border-brand-700/50">
              <div>
                <span className="text-xs font-semibold text-slate-400">Request Identifier</span>
                <div className="text-sm font-bold text-white font-mono mt-0.5">{report.request_id}</div>
              </div>
              <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                {report.status}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <span className="text-slate-400 font-medium">Purchase Description:</span>
                <div className="text-white mt-1 font-medium">{report.request_details?.raw_request_text}</div>
              </div>
              <div>
                <span className="text-slate-400 font-medium">Requester & Budget Ceiling:</span>
                <div className="text-white mt-1">
                  {report.request_details?.requester} • <span className="font-mono font-semibold">₹{Number(report.request_details?.budget_limit || 0).toLocaleString('en-IN')}</span>
                </div>
              </div>
            </div>

            {po && (
              <div className="mt-5 p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl">
                <div className="text-xs font-bold text-emerald-300 uppercase tracking-wider flex items-center gap-2 mb-2">
                  <Award className="w-4 h-4 text-emerald-400" />
                  Final Award & Purchase Commitment
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div>
                    <span className="text-slate-400">Awarded Supplier</span>
                    <div className="font-bold text-white mt-0.5">{po.awarded_vendor_name}</div>
                  </div>
                  <div>
                    <span className="text-slate-400">Order Number</span>
                    <div className="font-bold text-sky-400 font-mono mt-0.5">{po.order_number}</div>
                  </div>
                  <div>
                    <span className="text-slate-400">Authorized Total</span>
                    <div className="font-bold text-emerald-400 font-mono mt-0.5">
                      ₹{Number(po.approved_total).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </div>
                  </div>
                  <div>
                    <span className="text-slate-400">Approved By</span>
                    <div className="font-bold text-white mt-0.5">{po.approved_by}</div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Formatted Markdown Report Preview */}
          <div className="bg-brand-800/50 border border-brand-700/50 rounded-xl p-6">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-4 pb-2 border-b border-brand-700/50">
              Audit-Ready Procurement Dossier (Full Markdown Document)
            </h3>
            <pre className="bg-brand-900/90 border border-brand-700 p-4 rounded-lg font-mono text-xs text-slate-300 overflow-x-auto whitespace-pre-wrap leading-relaxed">
              {report.markdown_report}
            </pre>
          </div>
        </div>
      ) : (
        <div className="bg-brand-800/40 border border-brand-700/40 rounded-xl p-12 text-center text-slate-500">
          Loading comprehensive procurement report...
        </div>
      )}
    </div>
  );
};
