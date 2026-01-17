
import React from 'react';
import { Truck, FileBarChart, ChevronRight } from 'lucide-react';

interface MainMenuProps {
  onSelectView: (view: 'informe' | 'llegada') => void;
}

const LOGO_SQM = "https://www.sqm.com/wp-content/uploads/2021/03/logo-sqm-header.svg";

const MainMenu: React.FC<MainMenuProps> = ({ onSelectView }) => {
  return (
    <div className="min-h-screen bg-[#f8fafc] flex flex-col items-center justify-center p-8">
      <div className="text-center mb-16 space-y-6">
        <div className="flex flex-col justify-center items-center gap-4 mb-2">
          <div className="bg-white p-4 rounded-3xl shadow-xl border border-slate-100 mb-4 transition-transform hover:scale-105 duration-500">
            <img 
              src={LOGO_SQM} 
              alt="SQM Lithium Logo" 
              className="h-16 w-auto object-contain"
              onError={(e) => {
                e.currentTarget.src = "https://placehold.co/200x80/89B821/white?text=SQM+LITHIUM";
              }}
            />
          </div>
          <h1 className="text-4xl font-black text-slate-800 tracking-tighter">SISTEMA DE GESTIÓN LOGÍSTICA</h1>
        </div>
        <p className="text-slate-400 font-bold tracking-[0.3em] uppercase text-xs">Módulos Inteligentes de Operación</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-10 max-w-5xl w-full">
        {/* Card: Llegada de Equipos */}
        <button 
          onClick={() => onSelectView('llegada')}
          className="group relative bg-white border border-slate-100 p-12 rounded-[2.5rem] shadow-sm hover:shadow-2xl transition-all duration-500 flex flex-col items-center text-center space-y-8 overflow-hidden active:scale-95"
        >
          <div className="absolute top-0 right-0 w-32 h-32 bg-slate-50 rounded-bl-[5rem] -mr-10 -mt-10 group-hover:scale-110 transition-transform duration-500 opacity-50" />
          
          <div className="w-24 h-24 bg-slate-50 rounded-3xl flex items-center justify-center text-slate-400 group-hover:bg-blue-50 group-hover:text-blue-500 transition-colors duration-500">
            <Truck size={48} strokeWidth={1.5} />
          </div>
          
          <div className="space-y-3 relative z-10">
            <h2 className="text-3xl font-black text-slate-800 tracking-tight">Llegada de Equipos</h2>
            <p className="text-slate-500 text-sm leading-relaxed max-w-[200px] mx-auto">Control de ingresos, pesaje y turnos de transportistas en tiempo real.</p>
          </div>

          <div className="flex items-center gap-2 text-xs font-black tracking-widest uppercase text-slate-300 group-hover:text-blue-500 transition-colors">
            Acceder módulo <ChevronRight size={14} />
          </div>
        </button>

        {/* Card: Informe Operativo */}
        <button 
          onClick={() => onSelectView('informe')}
          className="group relative bg-white border border-slate-100 p-12 rounded-[2.5rem] shadow-sm hover:shadow-2xl transition-all duration-500 flex flex-col items-center text-center space-y-8 overflow-hidden active:scale-95"
        >
          <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-50 rounded-bl-[5rem] -mr-10 -mt-10 group-hover:scale-110 transition-transform duration-500 opacity-50" />
          
          <div className="w-24 h-24 bg-slate-50 rounded-3xl flex items-center justify-center text-slate-400 group-hover:bg-emerald-50 group-hover:text-emerald-500 transition-colors duration-500">
            <FileBarChart size={48} strokeWidth={1.5} />
          </div>
          
          <div className="space-y-3 relative z-10">
            <h2 className="text-3xl font-black text-slate-800 tracking-tight">Informe Operativo</h2>
            <p className="text-slate-500 text-sm leading-relaxed max-w-[200px] mx-auto">Dashboard inteligente, análisis de tonelaje y generación de reportes PDF.</p>
          </div>

          <div className="flex items-center gap-2 text-xs font-black tracking-widest uppercase text-slate-300 group-hover:text-emerald-500 transition-colors">
            Acceder módulo <ChevronRight size={14} />
          </div>
        </button>
      </div>

      <div className="mt-20 text-[10px] text-slate-300 font-bold uppercase tracking-[0.4em]">
        SQM S.A. &bull; Gerencia Logística &bull; {new Date().getFullYear()}
      </div>
    </div>
  );
};

export default MainMenu;
