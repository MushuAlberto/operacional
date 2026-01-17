
import React, { useState, useCallback, useMemo, useEffect } from 'react';
import * as XLSX from 'xlsx';
import { 
  Upload, Brain, Loader2, 
  Download, Home, ArrowLeft, Truck
} from 'lucide-react';
import { analyzeLogisticsWithGemini } from './services/geminiService';
import ChartCard from './components/ChartCard';
import ProductDetailSection from './components/ProductDetailSection';
import MainMenu from './components/MainMenu';
import LlegadaEquipos from './components/LlegadaEquipos';

interface UserChartConfig {
  type: 'bar' | 'line' | 'pie' | 'area';
  xAxis: string;
  yAxis: string | string[];
  title: string;
}

const FIXED_CHARTS: UserChartConfig[] = [
  { 
    type: 'bar', 
    xAxis: 'Producto', 
    yAxis: ['Ton_Prog', 'Ton_Real'], 
    title: 'Comparativa Tonelaje: Programado vs Real' 
  },
  { 
    type: 'bar', 
    xAxis: 'Producto', 
    yAxis: 'Eq_Real', 
    title: 'Equipos Reales por Tipo de Producto' 
  },
  { 
    type: 'pie', 
    xAxis: 'Destino', 
    yAxis: 'Ton_Real', 
    title: 'Distribución de Carga por Destino' 
  },
];

const App: React.FC = () => {
  const [view, setView] = useState<'menu' | 'informe' | 'llegada'>('menu');
  const [rawData, setRawData] = useState<any[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [config, setConfig] = useState<any>(null);
  const [userCharts, setUserCharts] = useState<UserChartConfig[]>(FIXED_CHARTS);
  
  const [exportingPDF, setExportingPDF] = useState(false);

  const isRunning = loading || analyzing || exportingPDF;

  useEffect(() => {
    if (selectedDate && rawData.length > 0 && view === 'informe') {
      const dayData = rawData.filter(r => r.Fecha === selectedDate);
      if (dayData.length > 0) {
        triggerAnalysis(dayData, selectedDate);
      }
    }
  }, [selectedDate, view]);

  const processFile = useCallback(async (file: File) => {
    setLoading(true);
    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const data = e.target?.result;
        const workbook = XLSX.read(data, { type: 'binary', cellDates: true });
        const sheetName = workbook.SheetNames.find(n => n === "Base de Datos") || workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 }) as any[][];
        
        if (jsonData.length < 2) throw new Error("Archivo vacío.");

        const headers = jsonData[0].map(h => String(h).toUpperCase().trim());
        const getIdx = (name: string, fallback: number) => {
          const found = headers.findIndex(h => h.includes(name.toUpperCase()));
          return found !== -1 ? found : fallback;
        };

        const idx = {
          fecha: getIdx("FECHA", 1),
          producto: getIdx("PRODUCTO", 31),
          destino: getIdx("DESTINO", 32),
          tonProg: getIdx("TON_PROG", 33),
          tonReal: getIdx("TON_REAL", 34),
          eqProg: getIdx("EQ_PROG", 35),
          eqReal: getIdx("EQ_REAL", 36),
          regReal: getIdx("REGULACION", 46)
        };

        const processed = jsonData.slice(1).map((row) => {
          if (!row || row.length < 2) return null;
          let dateVal = null;
          let rawDate = row[idx.fecha];
          if (rawDate instanceof Date) dateVal = rawDate.toISOString().split('T')[0];
          else if (typeof rawDate === 'number') {
            const d = new Date((rawDate - 25569) * 86400 * 1000);
            if (!isNaN(d.getTime())) dateVal = d.toISOString().split('T')[0];
          }
          if (!dateVal) return null;

          return {
            Fecha: dateVal,
            Producto: String(row[idx.producto] || 'SIN PRODUCTO').toUpperCase().trim(),
            Destino: String(row[idx.destino] || 'S/D').trim(),
            Ton_Prog: Number(row[idx.tonProg]) || 0,
            Ton_Real: Number(row[idx.tonReal]) || 0,
            Eq_Prog: Number(row[idx.eqProg]) || 0,
            Eq_Real: Number(row[idx.eqReal]) || 0,
            Regulacion_Real: Number(row[idx.regReal]) || 0
          };
        }).filter(r => r !== null);

        setRawData(processed);
        const dates = [...new Set(processed.map(r => r.Fecha))].sort().reverse();
        if (dates.length > 0) setSelectedDate(dates[0]);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    reader.readAsBinaryString(file);
  }, []);

  const triggerAnalysis = async (dayData: any[], date: string) => {
    setAnalyzing(true);
    setConfig(null); 
    try {
      const aiConfig = await analyzeLogisticsWithGemini(dayData, date);
      setConfig(aiConfig);
    } catch (err) { 
      console.error(err); 
    } finally { 
      setAnalyzing(false); 
    }
  };

  const filteredData = useMemo(() => rawData.filter(r => r.Fecha === selectedDate), [rawData, selectedDate]);
  const productList = useMemo(() => [...new Set(filteredData.map(r => r.Producto))].sort(), [filteredData]);

  const confirmExportPDF = async () => {
    const html2pdfLib = (window as any).html2pdf;
    if (!html2pdfLib) return;
    
    setExportingPDF(true);
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const element = document.getElementById('dashboard-report');
    if (!element) return;

    const opt = {
      margin: [5, 5, 5, 5],
      filename: `informe_litio_${selectedDate}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { 
        scale: 1.5,
        useCORS: true, 
        backgroundColor: '#ffffff',
        logging: false,
        allowTaint: false,
        scrollX: 0,
        scrollY: 0
      },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'landscape' },
      pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
    };

    try {
      await html2pdfLib().set(opt).from(element).save();
    } catch (err) {
      console.error("Error al exportar PDF:", err);
    } finally {
      setExportingPDF(false);
    }
  };

  if (view === 'menu') {
    return <MainMenu onSelectView={(v) => setView(v)} />;
  }

  if (view === 'llegada') {
    return <LlegadaEquipos onBack={() => setView('menu')} />;
  }

  return (
    <div className="flex h-screen bg-white font-sans text-slate-800 overflow-hidden">
      
      {/* SIDEBAR */}
      <aside className="w-[300px] bg-[#f0f2f6] border-r border-slate-200 flex flex-col no-print shrink-0">
        <div className="p-6 overflow-y-auto flex-1 space-y-8">
          <button 
            onClick={() => setView('menu')}
            className="flex items-center gap-2 text-slate-400 hover:text-slate-600 font-black text-[10px] uppercase tracking-widest transition-colors mb-4 group"
          >
            <Home size={14} className="group-hover:-translate-x-1 transition-transform" /> Menú Principal
          </button>

          <div className="flex items-center gap-2 mb-2">
            <span className="text-3xl">📊</span>
            <h1 className="font-bold text-xl tracking-tight">Litio Dashboard</h1>
          </div>

          <div className="space-y-2">
            <p className="text-sm font-medium text-slate-700">Cargar base de datos</p>
            <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-slate-300 rounded-lg cursor-pointer bg-white hover:bg-slate-50 transition-colors">
              <div className="flex flex-col items-center justify-center pt-5 pb-6">
                <Upload className="w-8 h-8 text-slate-400 mb-2" />
                <p className="text-[10px] text-slate-500 uppercase font-bold">Arrastrar archivo Excel</p>
              </div>
              <input type="file" className="hidden" accept=".xlsx,.xlsm" onChange={e => e.target.files?.[0] && processFile(e.target.files[0])} />
            </label>
            <p className="text-[10px] text-slate-400">Formatos: .xlsx, .xlsm (Máx 200MB)</p>
          </div>

          {rawData.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium text-slate-700">Seleccionar Fecha</p>
              <select 
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-md px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#ff4b4b]/20"
              >
                {[...new Set(rawData.map(r => r.Fecha))].sort().reverse().map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
          )}

          <div className="pt-4 border-t border-slate-200">
            <button 
              disabled={rawData.length === 0 || isRunning}
              onClick={confirmExportPDF}
              className="w-full bg-[#ff4b4b] hover:bg-[#e03a3a] text-white py-2.5 rounded-md font-medium text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-50"
            >
              <Download className="w-4 h-4" /> Download Report PDF
            </button>
          </div>
        </div>

        <div className="p-4 border-t border-slate-200 text-[10px] text-slate-400 flex items-center justify-between">
          <span>v3.2.0-Multi-Module</span>
          <div className="flex items-center gap-1">
            <span>Made with</span>
            <span className="text-rose-500">❤️</span>
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="flex-1 overflow-y-auto relative bg-white">
        
        {isRunning && (
          <div className="absolute top-4 right-8 z-50 flex items-center gap-2 bg-white px-3 py-1.5 rounded-full shadow-sm border border-slate-100 animate-in fade-in slide-in-from-top-2 no-print">
            <Loader2 className="w-3 h-3 animate-spin text-[#ff4b4b]" />
            <span className="text-[11px] font-medium text-slate-500">Procesando...</span>
          </div>
        )}

        <div className="max-w-5xl mx-auto p-8 space-y-12 pdf-export-container" id="dashboard-report">
          
          {rawData.length === 0 ? (
            <div className="py-20 flex flex-col items-center text-center space-y-6">
              <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center">
                <Upload className="w-8 h-8 text-slate-400" />
              </div>
              <div className="space-y-2">
                <h2 className="text-2xl font-bold">Esperando datos...</h2>
                <p className="text-slate-500 max-w-sm">Carga un archivo Excel para ver el informe operativo de la jornada.</p>
              </div>
              <button 
                onClick={() => setView('menu')}
                className="text-slate-400 hover:text-slate-800 text-[10px] font-black uppercase tracking-[0.2em] transition-colors flex items-center gap-2"
              >
                <ArrowLeft size={14} /> Volver al menú de módulos
              </button>
            </div>
          ) : (
            <>
              {/* --- PAGINA 1: ENCABEZADO + RESUMEN --- */}
              <div className="no-page-break space-y-8 bg-white">
                {/* Header */}
                <div className="flex justify-between items-start pb-6 border-b-2 border-slate-100">
                  <div className="flex flex-col">
                    <h1 className="text-4xl font-[900] text-[#1e293b] tracking-tighter leading-none mb-1">
                      INFORME OPERATIVO
                    </h1>
                    <p className="text-slate-400 font-bold text-[9px] tracking-[0.3em] uppercase">
                      Despacho Litio - Gerencia de Operaciones
                    </p>
                  </div>
                  <div className="text-right flex flex-col items-end">
                    <p className="text-slate-400 font-bold text-[8px] tracking-widest uppercase mb-0.5">
                      Fecha Reporte
                    </p>
                    <p className="text-3xl font-black text-emerald-600 tracking-tight">
                      {selectedDate}
                    </p>
                  </div>
                </div>

                {/* Resumen Ejecutivo */}
                {config && (
                  <div className="bg-white rounded-[1.5rem] p-8 border-2 border-emerald-500/30 border-l-[10px] space-y-6 relative overflow-hidden">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-emerald-500">
                        <Brain className="w-4 h-4" />
                        <span className="font-bold uppercase tracking-[0.2em] text-[9px]">
                          Resumen de Gestión
                        </span>
                      </div>
                      <h2 className="text-3xl font-black text-[#1e293b] tracking-tighter">
                        Estado de Operación
                      </h2>
                    </div>

                    <p className="text-lg font-medium leading-snug italic text-slate-600 max-w-4xl">
                      "{config.summary}"
                    </p>

                    <div className="grid grid-cols-4 gap-4">
                      {config.suggestedKPIs.slice(0, 4).map((kpi: any, idx: number) => (
                        <div key={idx} className="bg-slate-50 p-4 rounded-xl border border-slate-100 flex flex-col gap-1">
                          <span className="text-[8px] font-black text-slate-400 uppercase tracking-widest">
                            {kpi.label}
                          </span>
                          <span className="text-xl font-black text-emerald-600 tracking-tight">
                            {kpi.value}
                          </span>
                        </div>
                      ))}
                    </div>

                    <div className="flex justify-between items-center pt-4 border-t border-slate-100">
                      <div className="flex items-center gap-2">
                        <div className="bg-emerald-500 text-white font-black text-[9px] w-6 h-6 flex items-center justify-center rounded shadow-sm">
                          DL
                        </div>
                        <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">
                          Jornada {selectedDate}
                        </span>
                      </div>
                      <div className="bg-emerald-50 px-3 py-1 rounded-full">
                         <span className="text-emerald-600 text-[8px] font-black uppercase tracking-widest">
                          Vistaprevia Ejecutiva
                         </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* --- PAGINA 2: COMPARATIVA TONELAJE --- */}
              <div className="space-y-6 pt-10 page-break-before bg-white">
                <h2 className="text-lg font-black text-slate-400 uppercase tracking-[0.2em] border-b border-slate-100 pb-2">Distribución de Tonelaje</h2>
                <div className="grid grid-cols-1 gap-6">
                  <div className="no-page-break bg-white">
                    <ChartCard {...userCharts[0]} data={filteredData} />
                  </div>
                </div>
              </div>

              {/* --- PAGINA 3: EQUIPOS Y DESTINOS --- */}
              <div className="space-y-6 pt-10 page-break-before bg-white">
                <h2 className="text-lg font-black text-slate-400 uppercase tracking-[0.2em] border-b border-slate-100 pb-2">Equipos y Logística por Destino</h2>
                <div className="grid grid-cols-2 gap-6">
                  {userCharts.slice(1).map((c, i) => (
                    <div key={i} className="no-page-break bg-white">
                      <ChartCard {...c} data={filteredData} />
                    </div>
                  ))}
                </div>
              </div>

              {/* --- PAGINAS 4+ EN ADELANTE: DESGLOSE POR PRODUCTO (1 por página) --- */}
              {productList.map((prod, idx) => (
                <div key={prod} className="page-break-before pt-10 bg-white">
                  <ProductDetailSection 
                    product={prod} 
                    data={filteredData.filter(d => d.Producto === prod)} 
                    index={idx + 1} 
                    total={productList.length}
                  />
                </div>
              ))}
            </>
          )}
        </div>
      </main>
    </div>
  );
};

export default App;
