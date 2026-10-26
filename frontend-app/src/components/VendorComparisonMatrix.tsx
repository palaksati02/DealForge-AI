import React, { useEffect, useState } from 'react';
import { ProcurementReport, VendorQuote } from '../types';
import { ApiClient } from '../api/client';
import { Award, CheckCircle2, XCircle, AlertCircle, RefreshCw } from 'lucide-react';

interface Props {
  requestId: string;
}

export const VendorComparisonMatrix: React.FC<Props> = ({ requestId }) => {
  const [report, setReport] = useState<ProcurementReport | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await ApiClient.getReport(requestId);
      setReport(data);
    } catch (err) {
      console.error('Error fetching report:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (requestId) loadData();
  }, [requestId]);

  const vendors: VendorQuote[] = report?.vendor_matrix || [];

  return (
    <div className="space-y-6">
      <div className="bg-brand-800/60 border border-brand-700/60 rounded-xl p-5 backdrop-blur-md flex justify-between items-center">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Award className="w-5 h-5 text-amber-400" />
            Vendor Quotations & Multi-Criteria Ranking Matrix
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic weighted evaluation across Price, Delivery SLA, Warranty, Compliance, and Catalog Specifications
          </p>
        </div>
        <button
          onClick={loadData}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-slate-300 bg-brand-700/80 hover:bg-brand-600 rounded-lg transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      <div className="bg-brand-800/50 border border-brand-700/50 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-brand-900/60 text-slate-400 uppercase font-semibold border-b border-brand-700/50">
              <tr>
                <th className="py-3 px-4">Rank</th>
                <th className="py-3 px-4">Vendor Name</th>
                <th className="py-3 px-4">Unit Price</th>
                <th className="py-3 px-4">Total Quote</th>
                <th className="py-3 px-4">Lead Time</th>
                <th className="py-3 px-4">Warranty</th>
                <th className="py-3 px-4">Compliance Status</th>
                <th className="py-3 px-4">Weighted Score</th>
                <th className="py-3 px-4">Eligibility</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-700/30 text-slate-300">
              {vendors.length > 0 ? (
                vendors.map((v, idx) => {
                  const isWinner = v.rank === 1;
                  const isEligible = v.eligibility_status === 'ELIGIBLE';

                  return (
                    <tr
                      key={v.quote_id}
                      className={`hover:bg-brand-700/20 transition ${
                        isWinner ? 'bg-amber-500/5 border-l-2 border-l-amber-400' : ''
                      }`}
                    >
                      <td className="py-3 px-4 font-bold text-sm">
                        {v.rank ? (
                          <span className={`inline-flex items-center gap-1 ${isWinner ? 'text-amber-400 font-extrabold' : 'text-slate-400'}`}>
                            {isWinner && '👑'} #{v.rank}
                          </span>
                        ) : (
                          <span className="text-slate-500">—</span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-semibold text-white">{v.vendor_name}</div>
                        <div className="text-[10px] text-slate-400">Rating: {v.vendor_rating || 4.5} / 5.0</div>
                      </td>
                      <td className="py-3 px-4 font-mono">
                        ₹{Number(v.unit_price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 font-mono font-semibold text-white">
                        ₹{Number(v.total_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        {v.discount > 0 && (
                          <span className="text-[10px] text-emerald-400 block">
                            (-₹{Number(v.discount).toLocaleString('en-IN')} bulk discount)
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 font-medium">{v.delivery_days} Days</td>
                      <td className="py-3 px-4 font-medium">{v.warranty_months} Months</td>
                      <td className="py-3 px-4">
                        {v.eligibility_status === 'ELIGIBLE' ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400">
                            <CheckCircle2 className="w-3.5 h-3.5" /> PASS
                          </span>
                        ) : (
                          <div>
                            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-400">
                              <XCircle className="w-3.5 h-3.5" /> FAIL
                            </span>
                            {v.exclusion_reason && (
                              <div className="text-[10px] text-rose-300 max-w-xs mt-0.5 truncate" title={v.exclusion_reason}>
                                {v.exclusion_reason}
                              </div>
                            )}
                          </div>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <span className="font-bold text-sky-400 text-sm">
                          {Number(v.final_score).toFixed(1)}
                        </span>
                        <span className="text-[10px] text-slate-500"> / 100</span>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                            isEligible
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                              : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          }`}
                        >
                          {v.eligibility_status || 'UNKNOWN'}
                        </span>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-500">
                    No vendor quotations evaluated yet. Run workflow from the Dashboard or New Request view.
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
