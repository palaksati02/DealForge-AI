import React, { useState, useEffect } from 'react';
import { User } from './types';
import { ApiClient } from './api/client';
import { DashboardOverview } from './components/DashboardOverview';
import { NewRequestView } from './components/NewRequestView';
import { WorkflowLiveView } from './components/WorkflowLiveView';
import { VendorComparisonMatrix } from './components/VendorComparisonMatrix';
import { NegotiationWorkspace } from './components/NegotiationWorkspace';
import { ApprovalCenter } from './components/ApprovalCenter';
import { ProcurementReportView } from './components/ProcurementReportView';
import { 
  BarChart3, 
  PlusCircle, 
  Bot, 
  Building2, 
  MessageSquare, 
  ShieldCheck, 
  FileText, 
  Sparkles,
  UserCheck,
  Zap
} from 'lucide-react';

export const App: React.FC = () => {
  const [activeView, setActiveView] = useState<string>('overview');
  const [activeRequestId, setActiveRequestId] = useState<string>('');
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [pendingApprovalsCount, setPendingApprovalsCount] = useState<number>(0);

  // Authenticate as default seeded user (Rajesh Sharma, Procurement Manager)
  useEffect(() => {
    const initAuth = async () => {
      try {
        const authRes = await ApiClient.login('manager@dealforge.ai', 'Manager@123');
        setCurrentUser(authRes.user);
      } catch (err) {
        console.error('Initial login failed:', err);
      }
    };
    initAuth();
  }, []);

  // Update pending approval count periodically
  useEffect(() => {
    const updateApprovals = async () => {
      try {
        const apps = await ApiClient.getPendingApprovals();
        setPendingApprovalsCount(apps.length);
      } catch (e) {
        // quiet fallback
      }
    };
    updateApprovals();
    const interval = setInterval(updateApprovals, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleRoleSwitch = async (email: string, pwd: string) => {
    try {
      const authRes = await ApiClient.login(email, pwd);
      setCurrentUser(authRes.user);
    } catch (err) {
      alert('Failed to switch user: ' + err);
    }
  };

  const handleWorkflowLaunched = (reqId: string) => {
    setActiveRequestId(reqId);
    setActiveView('workflow');
  };

  return (
    <div className="flex h-screen bg-brand-900 text-slate-100 overflow-hidden font-sans">
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-brand-800/90 border-r border-brand-700/60 flex flex-col justify-between p-4 flex-shrink-0 z-20">
        <div>
          {/* Logo & Brand Header */}
          <div className="flex items-center gap-3 px-2 py-3 mb-6 border-b border-brand-700/50">
            <div className="w-8 h-8 rounded-lg bg-sky-500 flex items-center justify-center font-black text-slate-950 text-base shadow-lg shadow-sky-500/30">
              ⚡
            </div>
            <div>
              <div className="font-extrabold text-sm tracking-tight text-white flex items-center gap-1.5">
                DealForge AI
              </div>
              <div className="text-[10px] uppercase tracking-wider text-sky-400 font-semibold">
                Multi-Agent Engine
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1 text-xs font-medium">
            <button
              onClick={() => setActiveView('overview')}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg transition ${
                activeView === 'overview'
                  ? 'bg-sky-500 text-white font-semibold shadow-md shadow-sky-500/20'
                  : 'text-slate-300 hover:bg-brand-700/60 hover:text-white'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              <span>Dashboard Overview</span>
            </button>

            <button
              onClick={() => setActiveView('new-request')}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg transition ${
                activeView === 'new-request'
                  ? 'bg-sky-500 text-white font-semibold shadow-md shadow-sky-500/20'
                  : 'text-slate-300 hover:bg-brand-700/60 hover:text-white'
              }`}
            >
              <PlusCircle className="w-4 h-4" />
              <span>New Purchase Request</span>
            </button>

            <button
              onClick={() => setActiveView('workflow')}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg transition ${
                activeView === 'workflow'
                  ? 'bg-sky-500 text-white font-semibold shadow-md shadow-sky-500/20'
                  : 'text-slate-300 hover:bg-brand-700/60 hover:text-white'
              }`}
            >
              <Bot className="w-4 h-4" />
              <span>Live Agent Workflow</span>
            </button>

            <button
              onClick={() => setActiveView('vendors')}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg transition ${
                activeView === 'vendors'
                  ? 'bg-sky-500 text-white font-semibold shadow-md shadow-sky-500/20'
                  : 'text-slate-300 hover:bg-brand-700/60 hover:text-white'
              }`}
            >
              <Building2 className="w-4 h-4" />
              <span>Vendor Matrix</span>
            </button>

            <button
              onClick={() => setActiveView('negotiations')}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg transition ${
                activeView === 'negotiations'
                  ? 'bg-sky-500 text-white font-semibold shadow-md shadow-sky-500/20'
                  : 'text-slate-300 hover:bg-brand-700/60 hover:text-white'
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              <span>Negotiation Centre</span>
            </button>

            <button
              onClick={() => setActiveView('approvals')}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-lg transition ${
                activeView === 'approvals'
                  ? 'bg-sky-500 text-white font-semibold shadow-md shadow-sky-500/20'
                  : 'text-slate-300 hover:bg-brand-700/60 hover:text-white'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <ShieldCheck className="w-4 h-4" />
                <span>Approval Centre</span>
              </div>
              {pendingApprovalsCount > 0 && (
                <span className="px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500 text-slate-950">
                  {pendingApprovalsCount}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveView('report')}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg transition ${
                activeView === 'report'
                  ? 'bg-sky-500 text-white font-semibold shadow-md shadow-sky-500/20'
                  : 'text-slate-300 hover:bg-brand-700/60 hover:text-white'
              }`}
            >
              <FileText className="w-4 h-4" />
              <span>Executive Report</span>
            </button>
          </nav>
        </div>

        {/* User Role Switcher (RBAC) */}
        <div className="pt-4 border-t border-brand-700/50 space-y-3">
          <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
            RBAC Authenticated Persona
          </div>
          <div className="bg-brand-900/80 border border-brand-700/60 rounded-lg p-2.5 text-xs">
            <div className="font-semibold text-white truncate">{currentUser?.full_name || 'Loading...'}</div>
            <div className="text-[11px] text-sky-400 font-medium">{currentUser?.role_name || 'Procurement Manager'}</div>
          </div>

          <div className="flex flex-col gap-1">
            <span className="text-[10px] text-slate-400">Switch Role (Demonstration):</span>
            <div className="grid grid-cols-3 gap-1 text-[10px]">
              <button
                onClick={() => handleRoleSwitch('manager@dealforge.ai', 'Manager@123')}
                className="px-2 py-1 bg-brand-700/80 hover:bg-brand-600 rounded text-slate-200 truncate"
                title="Procurement Manager"
              >
                Manager
              </button>
              <button
                onClick={() => handleRoleSwitch('finance@dealforge.ai', 'Finance@123')}
                className="px-2 py-1 bg-brand-700/80 hover:bg-brand-600 rounded text-slate-200 truncate"
                title="Finance Reviewer"
              >
                Finance
              </button>
              <button
                onClick={() => handleRoleSwitch('admin@dealforge.ai', 'Admin@123')}
                className="px-2 py-1 bg-brand-700/80 hover:bg-brand-600 rounded text-slate-200 truncate"
                title="System Administrator"
              >
                Admin
              </button>
            </div>
          </div>

          <div className="text-[10px] text-slate-400 pt-1 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>MySQL 8.4 • ADK • A2A Online</span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden bg-brand-900">
        {/* Top Header */}
        <header className="h-14 border-b border-brand-700/50 px-6 flex items-center justify-between bg-brand-800/40 backdrop-blur-md flex-shrink-0">
          <div className="flex items-center gap-3">
            <h1 className="text-sm font-bold text-white capitalize">
              {activeView.replace('-', ' ')}
            </h1>
            {activeRequestId && (
              <span className="text-xs text-slate-400 font-mono bg-brand-700/40 px-2 py-0.5 rounded">
                Active Req: {activeRequestId.slice(0, 8)}...
              </span>
            )}
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 px-3 py-1 bg-sky-500/10 border border-sky-500/30 rounded-full text-[11px] text-sky-300 font-medium">
              <Zap className="w-3.5 h-3.5 text-sky-400" />
              <span>Deterministic Demo Mode Active</span>
            </div>
          </div>
        </header>

        {/* View Content Body */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeView === 'overview' && (
            <DashboardOverview
              onSelectRequest={(reqId) => {
                setActiveRequestId(reqId);
                setActiveView('workflow');
              }}
              onNavigateNew={() => setActiveView('new-request')}
            />
          )}

          {activeView === 'new-request' && (
            <NewRequestView onWorkflowLaunched={handleWorkflowLaunched} />
          )}

          {activeView === 'workflow' && (
            <WorkflowLiveView
              requestId={activeRequestId}
              onNavigateApprovals={() => setActiveView('approvals')}
              onNavigateReport={() => setActiveView('report')}
              onNavigateVendors={() => setActiveView('vendors')}
            />
          )}

          {activeView === 'vendors' && (
            <VendorComparisonMatrix requestId={activeRequestId} />
          )}

          {activeView === 'negotiations' && (
            <NegotiationWorkspace requestId={activeRequestId} />
          )}

          {activeView === 'approvals' && (
            <ApprovalCenter
              currentUser={currentUser}
              onApprovalComplete={(reqId) => {
                setActiveRequestId(reqId);
                setActiveView('report');
              }}
            />
          )}

          {activeView === 'report' && (
            <ProcurementReportView requestId={activeRequestId} />
          )}
        </div>
      </main>
    </div>
  );
};

export default App;
