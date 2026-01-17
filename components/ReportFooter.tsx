
import React from 'react';

const LOGO_SQM = "https://www.sqm.com/wp-content/uploads/2021/03/logo-sqm-header.svg";

const ReportFooter: React.FC = () => {
  return (
    <div className="mt-auto pt-6 border-t border-slate-100 flex justify-between items-end w-full">
      <div className="flex items-center gap-4">
        <div className="shrink-0">
          <img 
            src={LOGO_SQM} 
            alt="SQM Lithium" 
            className="h-10 w-auto object-contain" 
            crossOrigin="anonymous"
          />
        </div>
        <div>
          <p className="text-[11px] font-black text-slate-800 tracking-wider uppercase">SQM LITHIUM</p>
          <p className="text-[9px] text-slate-400 font-bold uppercase tracking-[0.2em]">Gerencia de Operaciones Salar</p>
        </div>
      </div>
      <div className="text-right flex flex-col items-end gap-1">
        <p className="text-[9px] text-slate-300 font-black uppercase tracking-widest">Documento Interno - Confidencial</p>
        <div className="h-1.5 w-32 bg-slate-50 rounded-full overflow-hidden flex">
          <div className="h-full bg-[#89B821] w-1/2"></div>
          <div className="h-full bg-[#003595] w-1/2"></div>
        </div>
      </div>
    </div>
  );
};

export default ReportFooter;
