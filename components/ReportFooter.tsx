
import React from 'react';

const ReportFooter: React.FC = () => {
  return (
    <div className="mt-auto pt-6 border-t border-slate-100 flex justify-between items-end w-full">
      <div className="flex items-center gap-4">
        {/* Representación SVG del logo SQM Li */}
        <div className="w-14 h-14 shrink-0">
          <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <circle cx="50" cy="50" r="48" fill="#89B821" />
            <path d="M2 72 C 20 62 80 62 98 72 L 98 90 C 80 100 20 100 2 90 Z" fill="#003595" />
            <text x="50" y="58" fontFamily="Arial, sans-serif" fontWeight="900" fontSize="24" fill="white" textAnchor="middle">SQM</text>
            <rect x="68" y="10" width="22" height="22" rx="4" fill="#89B821" stroke="white" strokeWidth="2.5" />
            <text x="79" y="26" fontFamily="Arial, sans-serif" fontWeight="bold" fontSize="12" fill="white" textAnchor="middle">Li</text>
          </svg>
        </div>
        <div>
          <p className="text-[11px] font-black text-slate-800 tracking-wider uppercase">SQM LITHIUM</p>
          <p className="text-[9px] text-slate-400 font-bold uppercase tracking-[0.2em]">Gerencia de Operaciones Salar</p>
        </div>
      </div>
      <div className="text-right flex flex-col items-end gap-1">
        <p className="text-[9px] text-slate-300 font-black uppercase tracking-widest">Documento Interno - Confidencial</p>
        <div className="h-1 w-24 bg-slate-50 rounded-full overflow-hidden">
          <div className="h-full bg-emerald-500 w-1/3"></div>
        </div>
      </div>
    </div>
  );
};

export default ReportFooter;
