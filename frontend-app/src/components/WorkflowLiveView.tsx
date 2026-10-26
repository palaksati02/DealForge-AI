import React, { useEffect, useState } from 'react';
import { WorkflowStatus, AgentLog } from '../types';
import { ApiClient } from '../api/client';
import { 
  Bot, 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  ShieldCheck, 
  FileSearch, 
  Cpu, 
  DollarSign, 
  Shield, 
  Scale, 
  MessageSquare,
  ArrowRight,
  Terminal
} from 'lucide-react';

interface Props {
  requestId: string;
  onNavigateApprovals: () => void;
  onNavigateReport: () => void;
  onNavigateVendors: () => void;
}

export const WorkflowLiveView: React.FC<Props> = ({
  requestId,
  onNavigateApprovals,
  onNavigateReport,
  onNavigateVendors,
}) => {
  const [statusData, setStatusData] = useState<WorkflowStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
    try {
      const data = await ApiClient.getWorkflowStatus(requestId);
      setStatusData(data);
    } catch (err) {
      console.error('Error fetching workflow status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!requestId) {
      setLoading(false);
      return;
    }
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, [requestId]);

  const logs = statusData?.logs || [];
  const currentStep = statusData?.current_step || 'IDLE';
  const isPaused = statusData?.status === 'PAUSED' || currentStep.includes('APPROVAL');
  const isFinalized = statusData?.status === 'COMPLETED' || currentStep === 'FINALIZED';

  const getAgentStatus = (agentIdentifier: string) => {
    const hasLog = logs.some((l) => l.agent_name.toLowerCase().includes(agentIdentifier.toLowerCase()));
    if (hasLog) {
      const errorLog = logs.some((l) => l.agent_name.toLowerCase().includes(agentIdentifier.toLowerCase()) && l.status === 'ERROR');
      if (errorLog) return { label: 'Failed', color: 'text-rose-400 bg-rose-500/10 border-rose-500/30' };
      return { label: 'Completed', color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' };
    }
    return { label: 'Pending', color: 'text-slate-400 bg-slate-800/40 border-slate-700/50' };
  };

  return (
    <div className="space-y-6">
      {/* Paused for Approval Notification */}
      {isPaused && (
        <div className="bg-amber-500/10 border border-amber-500/40 rounded-xl p-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
            <div>
              <div className="text-sm font-bold text-amber-300">
                Workflow Paused: Human Approval Required
              </div>
              <div className="text-xs text-slate-300 mt-0.5">
                Financial and governance risk thresholds have paused automatic issuance until authorized sign-off.
              </div>
            </div>
          </div>
          <button
            onClick={onNavigateApprovals}
            className="flex items-center gap-1.5 px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold text-xs rounded-lg shadow-lg shadow-amber-500/20 transition whitespace-nowrap"
          >
            Review in Approval Center <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Completed Success Banner */}
      {isFinalized && (
        <div className="bg-emerald-500/10 border border-emerald-500/40 rounded-xl p-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
            <div>
              <div className="text-sm font-bold text-emerald-300">
                Procurement Completed — Purchase Order Generated
              </div>
              <div className="text-xs text-slate-300 mt-0.5">
                The transaction has been fully committed to MySQL with verified audit trail.
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={onNavigateVendors}
              className="px-3 py-1.5 bg-brand-700 hover:bg-brand-600 text-white text-xs rounded-lg transition"
            >
              Vendor Matrix
            </button>
            <button
              onClick={onNavigateReport}
              className="flex items-center gap-1.5 px-4 py-1.5 bg-emerald-500 hover:bg-emerald-400 text-slate-900 font-semibold text-xs rounded-lg shadow-lg shadow-emerald-500/20 transition"
            >
              View Executive Report <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Pipeline Header */}
      <div className="bg-brand-800/60 border border-brand-700/60 rounded-xl p-5 backdrop-blur-md">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 pb-4 border-b border-brand-700/50 mb-4">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Bot className="w-5 h-5 text-sky-400" />
              Multi-Agent Orchestration Stepper
            </h2>
            <div className="text-xs text-slate-400 mt-1">
              Req ID: <span className="font-mono text-sky-400">{requestId}</span>
              {statusData?.workflow_id && (
                <> • WF ID: <span className="font-mono text-slate-400">{statusData.workflow_id.slice(0, 8)}...</span></>
              )}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400">Status:</span>
            <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${
              isFinalized ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' :
              isPaused ? 'bg-amber-500/20 text-amber-300 border-amber-500/30' :
              'bg-sky-500/20 text-sky-300 border-sky-500/30'
            }`}>
              {statusData?.status || 'INITIALIZING'}
            </span>
          </div>
        </div>

        {/* 8 Agent Cards Pipeline */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* 1. Requirement Analysis Agent */}
          <div className="bg-brand-900/60 border border-brand-700/50 rounded-lg p-3">
            <div className="flex justify-between items-center mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-sky-400">Google ADK</span>
              {(() => {
                const s = getAgentStatus('Requirement');
                return <span className={`text-[10px] px-2 py-0.5 rounded border font-semibold ${s.color}`}>{s.label}</span>;
              })()}
            </div>
            <div className="text-xs font-bold text-white flex items-center gap-1.5 mt-1">
              <FileSearch className="w-3.5 h-3.5 text-sky-400" />
              1. Requirement Agent
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Extracts specs, constraints & budget limits.
            </div>
          </div>

          {/* 2. Vendor Research Agent */}
          <div className="bg-brand-900/60 border border-brand-700/50 rounded-lg p-3">
            <div className="flex justify-between items-center mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-sky-400">Google ADK + MCP</span>
              {(() => {
                const s = getAgentStatus('Vendor');
                return <span className={`text-[10px] px-2 py-0.5 rounded border font-semibold ${s.color}`}>{s.label}</span>;
              })()}
            </div>
            <div className="text-xs font-bold text-white flex items-center gap-1.5 mt-1">
              <Cpu className="w-3.5 h-3.5 text-sky-400" />
              2. Vendor Research Agent
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Discovers catalog items via FastMCP tools.
            </div>
          </div>

          {/* 3. Price Analysis Specialist */}
          <div className="bg-brand-900/60 border border-brand-700/50 rounded-lg p-3">
            <div className="flex justify-between items-center mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400">CrewAI A2A</span>
              {(() => {
                const s = getAgentStatus('Price');
                return <span className={`text-[10px] px-2 py-0.5 rounded border font-semibold ${s.color}`}>{s.label}</span>;
              })()}
            </div>
            <div className="text-xs font-bold text-white flex items-center gap-1.5 mt-1">
              <DollarSign className="w-3.5 h-3.5 text-purple-400" />
              3. Price Specialist
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Applies tiered discounts, GST & logistics.
            </div>
          </div>

          {/* 4. Compliance Specialist */}
          <div className="bg-brand-900/60 border border-brand-700/50 rounded-lg p-3">
            <div className="flex justify-between items-center mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400">CrewAI A2A</span>
              {(() => {
                const s = getAgentStatus('Compliance');
                return <span className={`text-[10px] px-2 py-0.5 rounded border font-semibold ${s.color}`}>{s.label}</span>;
              })()}
            </div>
            <div className="text-xs font-bold text-white flex items-center gap-1.5 mt-1">
              <Shield className="w-3.5 h-3.5 text-purple-400" />
              4. Compliance Specialist
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Verifies ISO, warranty & lead-time rules.
            </div>
          </div>

          {/* 5. Deal Evaluation Specialist */}
          <div className="bg-brand-900/60 border border-brand-700/50 rounded-lg p-3">
            <div className="flex justify-between items-center mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400">CrewAI A2A</span>
              {(() => {
                const s = getAgentStatus('Evaluation');
                return <span className={`text-[10px] px-2 py-0.5 rounded border font-semibold ${s.color}`}>{s.label}</span>;
              })()}
            </div>
            <div className="text-xs font-bold text-white flex items-center gap-1.5 mt-1">
              <Scale className="w-3.5 h-3.5 text-purple-400" />
              5. Deal Evaluation
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Multi-criteria weighted rank computation.
            </div>
          </div>

          {/* 6. Negotiation Specialist */}
          <div className="bg-brand-900/60 border border-brand-700/50 rounded-lg p-3">
            <div className="flex justify-between items-center mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400">CrewAI A2A</span>
              {(() => {
                const s = getAgentStatus('Negotiation');
                return <span className={`text-[10px] px-2 py-0.5 rounded border font-semibold ${s.color}`}>{s.label}</span>;
              })()}
            </div>
            <div className="text-xs font-bold text-white flex items-center gap-1.5 mt-1">
              <MessageSquare className="w-3.5 h-3.5 text-purple-400" />
              6. Negotiation Specialist
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Formulates counter-offer within bounds.
            </div>
          </div>

          {/* 7. ADK Risk Agent */}
          <div className="bg-brand-900/60 border border-brand-700/50 rounded-lg p-3">
            <div className="flex justify-between items-center mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-sky-400">Google ADK</span>
              {(() => {
                const s = getAgentStatus('Risk');
                return <span className={`text-[10px] px-2 py-0.5 rounded border font-semibold ${s.color}`}>{s.label}</span>;
              })()}
            </div>
            <div className="text-xs font-bold text-white flex items-center gap-1.5 mt-1">
              <ShieldCheck className="w-3.5 h-3.5 text-sky-400" />
              7. Governance Risk Agent
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Evaluates policy threshold & approval gate.
            </div>
          </div>

          {/* 8. Purchase Order Commitment */}
          <div className="bg-brand-900/60 border border-brand-700/50 rounded-lg p-3">
            <div className="flex justify-between items-center mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">MySQL Ledger</span>
              <span className={`text-[10px] px-2 py-0.5 rounded border font-semibold ${
                isFinalized ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' : 'text-slate-400 bg-slate-800/40 border-slate-700/50'
              }`}>
                {isFinalized ? 'Committed' : 'Pending'}
              </span>
            </div>
            <div className="text-xs font-bold text-white flex items-center gap-1.5 mt-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              8. Purchase Order
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Generated upon authorized approval.
            </div>
          </div>
        </div>
      </div>

      {/* Real-time Chronological Agent Audit Log Stream */}
      <div className="bg-brand-800/60 border border-brand-700/60 rounded-xl overflow-hidden backdrop-blur-md">
        <div className="px-5 py-3 border-b border-brand-700/50 flex justify-between items-center bg-brand-900/40">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-sky-400" />
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              Live Agent Execution Stream (MySQL Database Event Log)
            </h3>
          </div>
          <span className="text-[11px] text-slate-400 font-mono">
            {logs.length} Recorded Events
          </span>
        </div>

        <div className="p-4 max-h-96 overflow-y-auto space-y-2 font-mono text-xs">
          {logs.length > 0 ? (
            logs.map((log) => (
              <div
                key={log.log_id}
                className="flex items-start gap-3 p-2 bg-brand-900/70 border border-brand-700/30 rounded"
              >
                <span className="text-slate-500 text-[10px] whitespace-nowrap mt-0.5">
                  {new Date(log.started_at).toLocaleTimeString()}
                </span>
                <span className="text-sky-400 font-semibold whitespace-nowrap text-[11px]">
                  [{log.agent_name}]
                </span>
                <span className={`text-[10px] px-1.5 py-0.2 rounded font-bold uppercase whitespace-nowrap ${
                  log.status === 'SUCCESS' ? 'text-emerald-400 bg-emerald-500/10' :
                  log.status === 'WARNING' ? 'text-amber-400 bg-amber-500/10' :
                  log.status === 'ERROR' ? 'text-rose-400 bg-rose-500/10' :
                  'text-slate-400 bg-slate-800'
                }`}>
                  {log.event_type}
                </span>
                <span className="text-slate-300 text-[11px] flex-1">
                  {log.output_summary || log.input_summary || '-'}
                </span>
              </div>
            ))
          ) : (
            <div className="text-center py-6 text-slate-500">
              Workflow pipeline initializing. Connecting to Google ADK orchestrator...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
