'use client';

import React from 'react';
import { ArrowLeft, CheckCircle2, Layers, Clock, ArrowRight } from 'lucide-react';
import { CAMPAIGN_WORKFLOW_STEPS } from '@/lib/data';
import { NavigationTab } from '@/types/moreai';

interface WorkflowProgressViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const WorkflowProgressView: React.FC<WorkflowProgressViewProps> = ({
  onBack,
  onNavigateTab,
}) => {
  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button onClick={onBack} className="p-1 rounded-lg text-slate-400 hover:text-slate-700">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="text-center">
          <h1 className="text-base font-bold text-slate-900 leading-tight">Campaign Launch Project</h1>
          <span className="text-[10px] text-slate-500 font-medium">Orchestrator Progres AI Agent</span>
        </div>
        <div className="w-5" />
      </div>

      {/* Progress Card (Sheet 6 Screen 7) */}
      <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-xs space-y-4">
        <div>
          <div className="flex justify-between text-xs text-slate-500 font-medium mb-1.5">
            <span>Total Progress</span>
            <span className="font-bold text-slate-900">75%</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
            <div
              className="bg-gradient-to-r from-red-600 to-rose-500 h-2.5 rounded-full transition-all duration-700"
              style={{ width: '75%' }}
            />
          </div>
        </div>

        {/* 4 Agent Steppers */}
        <div className="space-y-3 pt-2">
          {CAMPAIGN_WORKFLOW_STEPS.map((step, idx) => (
            <div
              key={step.id}
              className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 flex items-start gap-3"
            >
              <div className="mt-0.5 shrink-0">
                {step.status === 'completed' && (
                  <div className="w-6 h-6 rounded-full bg-emerald-600 text-white flex items-center justify-center text-xs font-bold">
                    ✓
                  </div>
                )}
                {step.status === 'in_progress' && (
                  <div className="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs animate-pulse font-bold">
                    75%
                  </div>
                )}
                {step.status === 'pending' && (
                  <div className="w-6 h-6 rounded-full bg-slate-200 text-slate-600 flex items-center justify-center text-xs font-bold">
                    {idx + 1}
                  </div>
                )}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-slate-900">{step.agentName}</h3>
                  <span
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                      step.status === 'completed'
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : step.status === 'in_progress'
                        ? 'bg-blue-50 text-blue-700 border border-blue-200'
                        : 'bg-slate-100 text-slate-500'
                    }`}
                  >
                    {step.status === 'completed' ? '✓ Selesai' : step.status === 'in_progress' ? '75% Selesai' : 'Menunggu'}
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5 font-medium">{step.role}</p>
                <p className="text-[11px] text-slate-700 mt-1 bg-white p-2.5 rounded-xl border border-slate-100 font-medium">
                  {step.outputSummary}
                </p>
              </div>
            </div>
          ))}
        </div>

        <button
          onClick={() => onNavigateTab('artifacts_result')}
          className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition shadow-xs flex items-center justify-center gap-1.5"
        >
          <span>Lihat Hasil &amp; Artefak Selesai</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
