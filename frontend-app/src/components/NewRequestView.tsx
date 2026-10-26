import React, { useState } from 'react';
import { ApiClient } from '../api/client';
import { Sparkles, Send, Laptop, Server, AlertTriangle, ArrowRight } from 'lucide-react';

interface Props {
  onWorkflowLaunched: (requestId: string) => void;
}

export const NewRequestView: React.FC<Props> = ({ onWorkflowLaunched }) => {
  const [rawText, setRawText] = useState('');
  const [qty, setQty] = useState<number | ''>('');
  const [budget, setBudget] = useState<number | ''>('');
  const [deadline, setDeadline] = useState<number | ''>('');
  const [warranty, setWarranty] = useState<number | ''>('');
  const [category, setCategory] = useState<string>('Laptops');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fillScenario = (scenario: string) => {
    if (scenario === 'standard-laptops') {
      setRawText('Purchase 50 laptops with at least 16 GB RAM and 512 GB SSD, a maximum budget of ₹38,00,000, delivery within 14 days, and a minimum two-year warranty.');
      setQty(50);
      setBudget(3800000);
      setDeadline(14);
      setWarranty(24);
      setCategory('Laptops');
    } else if (scenario === 'budget-overrun') {
      setRawText('Procure 50 high-end laptops with 32 GB RAM, maximum total budget capped strictly at ₹25,00,000, delivery in 10 days.');
      setQty(50);
      setBudget(2500000);
      setDeadline(10);
      setWarranty(24);
      setCategory('Laptops');
    } else if (scenario === 'servers') {
      setRawText('Procure 4 rackmount PowerEdge servers with 128 GB ECC RAM, a maximum budget of ₹20,00,000, delivery within 14 days, and 3-year warranty.');
      setQty(4);
      setBudget(2000000);
      setDeadline(14);
      setWarranty(36);
      setCategory('Servers');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rawText.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      const res = await ApiClient.createRequest({
        requester: 'Procurement Specialist',
        raw_request_text: rawText,
        quantity_override: qty ? Number(qty) : undefined,
        budget_override: budget ? Number(budget) : undefined,
        deadline_override_days: deadline ? Number(deadline) : undefined,
        warranty_override_months: warranty ? Number(warranty) : undefined,
        category_override: category || undefined,
      });

      onWorkflowLaunched(res.request_id);
    } catch (err: any) {
      setError(err.message || 'Failed to submit procurement request');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="bg-brand-800/60 border border-brand-700/60 rounded-xl p-6 backdrop-blur-md">
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className="w-5 h-5 text-sky-400" />
          <h2 className="text-lg font-bold text-white">Natural Language Procurement Submission</h2>
        </div>
        <p className="text-xs text-slate-400 mb-6">
          DealForge AI automatically extracts specifications, quantities, budget constraints, and SLA parameters via the Google ADK Requirement Agent.
        </p>

        {error && (
          <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/30 text-rose-400 rounded-lg text-xs">
            {error}
          </div>
        )}

        {/* Quick Fill Scenarios */}
        <div className="mb-6">
          <div className="text-xs font-semibold text-slate-400 mb-2">Pre-Configured Scenarios:</div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => fillScenario('standard-laptops')}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-brand-700/60 hover:bg-brand-700 border border-brand-600/50 rounded-lg text-xs text-slate-200 transition"
            >
              <Laptop className="w-3.5 h-3.5 text-sky-400" />
              Standard 50 Laptops (Within Budget)
            </button>
            <button
              type="button"
              onClick={() => fillScenario('budget-overrun')}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-brand-700/60 hover:bg-brand-700 border border-brand-600/50 rounded-lg text-xs text-slate-200 transition"
            >
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              50 Laptops (Budget Overrun Trigger)
            </button>
            <button
              type="button"
              onClick={() => fillScenario('servers')}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-brand-700/60 hover:bg-brand-700 border border-brand-600/50 rounded-lg text-xs text-slate-200 transition"
            >
              <Server className="w-3.5 h-3.5 text-emerald-400" />
              4 Rackmount PowerEdge Servers
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Natural Language Request Prompt
            </label>
            <textarea
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              placeholder="e.g. Purchase 50 laptops with at least 16 GB RAM and 512 GB SSD, a maximum budget of ₹38,00,000, delivery within 14 days, and a minimum two-year warranty."
              rows={4}
              required
              className="w-full bg-brand-900/80 border border-brand-700 rounded-lg p-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 transition"
            />
          </div>

          <div className="pt-2">
            <span className="text-xs font-semibold text-slate-400">Structured Parameters (Auto-derived or Overridden):</span>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-2">
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Quantity</label>
                <input
                  type="number"
                  value={qty}
                  onChange={(e) => setQty(e.target.value ? parseInt(e.target.value) : '')}
                  placeholder="50"
                  className="w-full bg-brand-900/80 border border-brand-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Budget Ceiling (INR)</label>
                <input
                  type="number"
                  value={budget}
                  onChange={(e) => setBudget(e.target.value ? parseFloat(e.target.value) : '')}
                  placeholder="3800000"
                  className="w-full bg-brand-900/80 border border-brand-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Delivery SLA (Days)</label>
                <input
                  type="number"
                  value={deadline}
                  onChange={(e) => setDeadline(e.target.value ? parseInt(e.target.value) : '')}
                  placeholder="14"
                  className="w-full bg-brand-900/80 border border-brand-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Warranty SLA (Months)</label>
                <input
                  type="number"
                  value={warranty}
                  onChange={(e) => setWarranty(e.target.value ? parseInt(e.target.value) : '')}
                  placeholder="24"
                  className="w-full bg-brand-900/80 border border-brand-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
                />
              </div>
            </div>
          </div>

          <div className="pt-4 flex justify-end">
            <button
              type="submit"
              disabled={submitting || !rawText.trim()}
              className="inline-flex items-center gap-2 px-6 py-2.5 bg-sky-500 hover:bg-sky-400 disabled:opacity-50 text-white font-medium text-xs rounded-lg shadow-lg shadow-sky-500/20 transition"
            >
              {submitting ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Initiating Multi-Agent Pipeline...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  Launch Multi-Agent Procurement Workflow
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
