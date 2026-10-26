import React, { useEffect, useState } from 'react';
import { NegotiationItem } from '../types';
import { ApiClient } from '../api/client';
import { MessageSquare, TrendingDown, AlertCircle, Send, CheckCircle2 } from 'lucide-react';

interface Props {
  requestId: string;
}

export const NegotiationWorkspace: React.FC<Props> = ({ requestId }) => {
  const [negotiations, setNegotiations] = useState<NegotiationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [customCounter, setCustomCounter] = useState<string>('');
  const [simulatedResponse, setSimulatedResponse] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const report = await ApiClient.getReport(requestId);
      setNegotiations(report.negotiations || []);
      if (report.negotiations && report.negotiations.length > 0) {
        setCustomCounter(String(report.negotiations[0].counter_offer_amount));
      }
    } catch (err) {
      console.error('Error fetching negotiations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (requestId) loadData();
  }, [requestId]);

  const activeNeg = negotiations[0];

  const handleSimulateResponse = () => {
    const counterVal = Number(customCounter);
    if (!activeNeg) return;

    if (counterVal >= activeNeg.target_amount) {
      setSimulatedResponse(
        `Supplier Acceptance: The supplier reviewed your counter-offer of ₹${counterVal.toLocaleString('en-IN')}. They agreed to the commercial terms with a 5% volume discount applied across subsequent quarterly orders.`
      );
    } else {
      setSimulatedResponse(
        `Supplier Counter-Revision: The supplier noted ₹${counterVal.toLocaleString('en-IN')} falls below manufacturer minimum cost margin. They have proposed a revised compromise total of ₹${(Number(activeNeg.original_amount) * 0.95).toLocaleString('en-IN')}.`
      );
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="bg-brand-800/60 border border-brand-700/60 rounded-xl p-5 backdrop-blur-md">
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-sky-400" />
          Autonomous Negotiation & Commercial Terms Workspace
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          CrewAI Negotiation Specialist establishes mathematically bounded target prices and drafts persuasive data-backed communications.
        </p>
      </div>

      {activeNeg ? (
        <div className="space-y-6">
          {/* Commercial Metrics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="bg-brand-800/50 border border-brand-700/50 rounded-xl p-4">
              <div className="text-xs text-slate-400">Original Supplier Quote</div>
              <div className="text-lg font-bold font-mono text-white mt-1">
                ₹{Number(activeNeg.original_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
            </div>

            <div className="bg-brand-800/50 border border-brand-700/50 rounded-xl p-4">
              <div className="text-xs text-slate-400">Target Benchmark Price</div>
              <div className="text-lg font-bold font-mono text-sky-400 mt-1">
                ₹{Number(activeNeg.target_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
            </div>

            <div className="bg-brand-800/50 border border-brand-700/50 rounded-xl p-4">
              <div className="text-xs text-slate-400">Counter-Offer Proposed</div>
              <div className="text-lg font-bold font-mono text-emerald-400 mt-1">
                ₹{Number(activeNeg.counter_offer_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
            </div>

            <div className="bg-brand-800/50 border border-brand-700/50 rounded-xl p-4">
              <div className="text-xs text-slate-400 flex items-center gap-1">
                <TrendingDown className="w-3.5 h-3.5 text-emerald-400" />
                Projected Savings
              </div>
              <div className="text-lg font-bold font-mono text-emerald-400 mt-1">
                ₹{Number(activeNeg.savings).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
            </div>
          </div>

          {/* Compliance Disclaimer Notice */}
          <div className="p-3 bg-brand-900/80 border border-brand-700/60 rounded-xl text-xs text-slate-300 flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-amber-300">Notice on Financial Projections: </span>
              Projected savings represent algorithmic negotiation targets based on historical order volumes and standard enterprise margins. Consequential financial commitments are recognized only upon bilateral agreement.
            </div>
          </div>

          {/* Negotiation Rationale */}
          <div className="bg-brand-800/50 border border-brand-700/50 rounded-xl p-5">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2">
              Commercial Rationale & Strategy
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              {activeNeg.justification}
            </p>
          </div>

          {/* Draft Communication & Editor */}
          <div className="bg-brand-800/50 border border-brand-700/50 rounded-xl p-5 space-y-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              Negotiation Draft Message
            </h3>

            <div className="bg-brand-900/80 border border-brand-700 rounded-lg p-4 font-mono text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">
              {`Subject: Commercial Clarification & Strategic Pricing — RFQ #${requestId.slice(0, 8)}

Dear Account Director,

Thank you for your comprehensive formal quotation regarding our requirements. We have reviewed your technical specifications, ISO quality standards, and warranty terms.

While your proposal ranks high on technical compliance, our financial parameters benchmark the effective price at ₹${Number(customCounter || activeNeg.counter_offer_amount).toLocaleString('en-IN')} based on corporate procurement thresholds for immediate delivery.

We request your consideration of this revised figure to enable prompt purchase order issuance.

Warm regards,
DealForge AI Autonomous Procurement System`}
            </div>

            <div className="pt-2 flex flex-col sm:flex-row gap-3 items-center">
              <div className="flex-1 w-full">
                <label className="block text-[11px] text-slate-400 mb-1">
                  Adjust Counter-Offer Value (INR)
                </label>
                <input
                  type="number"
                  value={customCounter}
                  onChange={(e) => setCustomCounter(e.target.value)}
                  className="w-full bg-brand-900 border border-brand-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500 font-mono"
                />
              </div>

              <div className="self-end w-full sm:w-auto">
                <button
                  type="button"
                  onClick={handleSimulateResponse}
                  className="w-full sm:w-auto px-4 py-2 bg-sky-500 hover:bg-sky-400 text-white font-medium text-xs rounded-lg shadow-lg shadow-sky-500/20 transition flex items-center justify-center gap-1.5"
                >
                  <Send className="w-3.5 h-3.5" />
                  Simulate Supplier Response
                </button>
              </div>
            </div>

            {simulatedResponse && (
              <div className="p-3 bg-brand-900/90 border border-emerald-500/30 rounded-lg text-xs text-emerald-300 flex items-start gap-2 animate-fadeIn">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                <div>{simulatedResponse}</div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="bg-brand-800/40 border border-brand-700/40 rounded-xl p-12 text-center text-slate-500">
          No negotiation cycle active for the selected request. Initiate or select an active workflow from Dashboard.
        </div>
      )}
    </div>
  );
};
