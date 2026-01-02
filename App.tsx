
import React, { useState, useCallback, useMemo, useEffect } from 'react';
import * as XLSX from 'xlsx';
import { 
  FileUp, BrainCircuit, Loader2, Calendar, 
  BarChart3, RefreshCcw, FileText, 
  Package, Truck, Target, CheckSquare, Square,
  Settings2, ChevronDown, ChevronUp, Sparkles
} from 'lucide-react';
import { analyzeLogisticsWithGemini } from './services/geminiService';
import ChartCard from './components/ChartCard';
import ProductDetailSection from './components/ProductDetailSection';

interface UserChartConfig {
  type: 'bar' | 'line' | 'pie' | 'area';
  xAxis: string;
  yAxis: string;
  title: string;
}

const FIXED_CHARTS: UserChartConfig[] = [
  { type: 'bar', xAxis: 'Producto', yAxis: 'Ton_Prog', title: 'Tonelaje Programado por Producto' },
  { type: 'bar', xAxis: 'Producto', yAxis: 'Ton_Real', title: 'Tonelaje Real por Producto' },
  { type: 'bar', xAxis: 'Producto', yAxis: 'Eq_Real', title: 'Equipos Reales por Tipo de Producto' },
  { type: 'pie', xAxis: 'Destino', yAxis: 'Ton_Real', title: 'Distribución de Carga por Destino' },
];

const App: React.FC = () => {
  const [rawData, setRawData] = useState<any[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [config, setConfig] = useState<any>(null);
  const [userCharts, setUserCharts] = useState<UserChartConfig[]>(FIXED_CHARTS);
  const [expandedChartConfig, setExpandedChartConfig] = useState<number | null>(null);
  
  const [exportingPDF, setExportingPDF] = useState(false);
  const [exportingImage, setExportingImage] = useState(false);
  
  const [showExportModal, setShowExportModal] = useState(false);
  const [pdfOptions, setPdfOptions] = useState({
    summary: true,
    charts: true,
    products: true
  });

  useEffect(() => {
    if (selectedDate && rawData.length > 0) {
      const dayData = rawData.filter(r => r.Fecha === selectedDate);
      if (dayData.length > 0) {
        triggerAnalysis(dayData, selectedDate);
      }
    }
  }, [selectedDate]);

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
          } else if (typeof rawDate === 'string') {
            const d = new Date(rawDate);
            if (!isNaN(d.getTime())) dateVal = d.toISOString().split('T')[0];
          }
          if (!dateVal) return null;

          let destinoFinal = String(row[idx.destino] || 'S/D').trim();
          const destUpper = destinoFinal.toUpperCase();
          if (destUpper.includes("ANTOFAGASTA") && (destUpper.includes("LITIO") || destUpper.includes("P DE LITIO"))) {
            destinoFinal = "PQL";
          }

          return {
            Fecha: dateVal,
            Producto: String(row[idx.producto] || 'SIN PRODUCTO').toUpperCase().trim(),
            Destino: destinoFinal,
            Ton_Prog: Number(row[idx.tonProg]) || 0,
            Ton_Real: Number(row[idx.tonReal]) || 0,
            Eq_Prog: Number(row[idx.eqProg]) || 0,
            Eq_Real: Number(row[idx.eqReal]) || 0,
            Regulacion_Real: Number(row[idx.regReal]) || 0
          };
        }).filter(r => r !== null);

        setRawData(processed);
        const dates = [...new Set(processed.map(r => r.Fecha))].sort().reverse();
        if (dates.length > 0) {
          setSelectedDate(dates[0]);
        }
      } catch (err: any) {
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

  const updateChartConfig = (index: number, field: keyof UserChartConfig, value: string) => {
    const newCharts = [...userCharts];
    newCharts[index] = { ...newCharts[index], [field]: value };
    setUserCharts(newCharts);
  };

  const filteredData = useMemo(() => rawData.filter(r => r.Fecha === selectedDate), [rawData, selectedDate]);
  const productList = useMemo(() => [...new Set(filteredData.map(r => r.Producto))].sort(), [filteredData]);

  const stats = useMemo(() => {
    const totalProg = filteredData.reduce((a, b) => a + b.Ton_Prog, 0);
    const totalReal = filteredData.reduce((a, b) => a + b.Ton_Real, 0);
    const totalEqReal = filteredData.reduce((a, b) => a + b.Eq_Real, 0);
    return { 
      totalProg, 
      totalReal, 
      totalEqReal,
      compliance: totalProg > 0 ? (totalReal / totalProg) * 100 : 0,
      productCount: productList.length
    };
  }, [filteredData, productList]);

  const chartChunks = useMemo(() => {
    if (!userCharts.length) return [];
    const chunks = [];
    for (let i = 0; i < userCharts.length; i += 2) {
      chunks.push(userCharts.slice(i, i + 2));
    }
    return chunks;
  }, [userCharts]);

  const confirmExportPDF = async () => {
    setShowExportModal(false);
    const html2pdfLib = (window as any).html2pdf;
    if (!html2pdfLib) return;
    
    window.scrollTo(0, 0);
    setExportingPDF(true);
    
    await new Promise(resolve => setTimeout(resolve, 2000)); 
    const element = document.getElementById('dashboard-report');
    if (!element) {
      setExportingPDF(false);
      return;
    }

    const opt = {
      margin: 0, 
      filename: `REPORTE_LOGISTICA_${selectedDate}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 1.5, useCORS: true, logging: false, backgroundColor: '#ffffff', scrollY: 0, scrollX: 0 },
      jsPDF: { unit: 'px', format: [1056, 816], orientation: 'landscape', compress: true },
      pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
    };

    try { await html2pdfLib().set(opt).from(element).save(); } 
    catch (err) { console.error("Error PDF:", err); } 
    finally { setExportingPDF(false); }
  };

  const exportSummaryImage = async () => {
    const html2canvasLib = (window as any).html2canvas;
    if (!html2canvasLib || !config) return;
    
    setExportingImage(true);
    try {
      const element = document.getElementById('teaser-capture-zone');
      if (!element) throw new Error("Teaser no encontrado");

      const canvas = await html2canvasLib(element, {
        scale: 1.5, backgroundColor: '#ffffff', logging: false, useCORS: true, windowWidth: 1056,
      });
      
      const link = document.createElement('a');
      link.download = `TEASER_LOGISTICA_LITIO_${selectedDate}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    } catch (err) { console.error("Error imagen:", err); } 
    finally { setExportingImage(false); }
  };

  const pdfPageClass = exportingPDF 
    ? "w-[1056px] h-[790px] bg-white relative overflow-hidden p-8 flex flex-col justify-between" 
    : "p-10 flex flex-col gap-6 bg-white min-h-[800px]";

  const renderSummaryPage = () => (
    <div className={pdfPageClass} style={{ pageBreakAfter: 'always' }}>
      <div className="flex justify-between items-start mb-12">
          <div className="flex-1">
            <h1 className="text-5xl font-black text-slate-900 uppercase tracking-tighter mb-1">Informe Operativo</h1>
            <p className="text-sm font-bold text-slate-400 uppercase tracking-[0.3em]">Gerencia de Operaciones Salar</p>
          </div>
          <div className="text-right">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">FECHA REPORTE</p>
            <p className="text-3xl font-black text-emerald-600">{selectedDate}</p>
          </div>
      </div>

      {config ? (
        <div className="flex-1 bg-white rounded-[3rem] p-12 border border-slate-100 shadow-xl flex flex-col relative overflow-hidden bg-gradient-to-br from-white to-slate-50">
          <div className="absolute top-0 left-0 w-3 h-full bg-emerald-500"></div>
          <div className="flex items-center justify-between mb-10">
            <div className="flex items-center gap-3 text-emerald-600">
              <BrainCircuit className="w-6 h-6" />
              <span className="font-black text-xs uppercase tracking-[0.3em]">RESUMEN DE GESTIÓN</span>
            </div>
          </div>
          
          <div className="flex-1 flex flex-col justify-center">
            <p className="text-4xl font-black text-slate-900 leading-tight mb-8">Estado de Operación</p>
            <p className="text-3xl font-medium text-slate-800 italic leading-relaxed mb-12">"{config.summary}"</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {config.suggestedKPIs?.slice(0, 4).map((kpi: any, idx: number) => (
                  <div key={idx} className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm transform hover:scale-105 transition-all">
                    <span className="block text-[9px] font-black text-slate-400 uppercase mb-2 tracking-[0.15em]">{kpi.label}</span>
                    <span className="block text-2xl font-black text-emerald-600">{kpi.value}</span>
                  </div>
              ))}
            </div>
          </div>

          <div className="mt-12 flex justify-between items-center border-t border-slate-100 pt-8">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center text-white font-bold text-xs">DL</div>
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Jornada {selectedDate}</span>
            </div>
            <span className="text-[10px] font-black text-emerald-600 uppercase tracking-[0.2em] bg-emerald-50 px-4 py-1.5 rounded-full">Vista Previa Ejecutiva</span>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center bg-slate-50 rounded-[3rem] border border-slate-200 border-dashed">
            <div className="flex flex-col items-center text-slate-400">
              <RefreshCcw className="w-10 h-10 mb-4 animate-spin text-emerald-500" />
              <p className="text-sm font-bold uppercase tracking-widest">Generando Análisis IA...</p>
            </div>
        </div>
      )}
    </div>
  );

  const renderChartsPage = (chunk: any[], chunkIdx: number, total: number) => (
    <div key={`trend-page-${chunkIdx}`} className={pdfPageClass} style={{ pageBreakAfter: 'always' }}>
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-2xl font-black text-slate-800 uppercase tracking-widest">
            Visualización de Tendencias {total > 1 ? `(${chunkIdx + 1}/${total})` : ''}
          </h2>
        </div>
        <div className={`grid grid-cols-2 ${exportingPDF ? 'gap-4' : 'gap-8'} flex-1`}>
        {chunk.map((c: any, i: number) => (
          <div key={i} className="bg-white rounded-[2rem] border border-slate-100 p-0 overflow-visible flex items-center justify-center">
              <ChartCard {...c} data={filteredData} isPrinting={true} />
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className={`flex h-screen bg-slate-100 overflow-hidden font-sans ${exportingPDF ? 'overflow-visible' : ''}`}>
      {!exportingPDF && (
        <aside className="w-80 bg-slate-950 text-white flex flex-col border-r border-slate-800 no-print overflow-y-auto">
          <div className="p-6 border-b border-slate-800 sticky top-0 bg-slate-950 z-10">
            <div className="flex items-center gap-3 mb-10">
              <div className="bg-emerald-500 p-2 rounded-lg shadow-lg shadow-emerald-500/20"><BarChart3 className="w-5 h-5" /></div>
              <span className="font-bold text-lg tracking-tight">DataVibe Analytics</span>
            </div>

            <label className="block text-[10px] font-bold text-slate-500 uppercase mb-2 tracking-widest">Jornada</label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <select 
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="w-full bg-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm appearance-none cursor-pointer outline-none focus:ring-2 focus:ring-emerald-500/50"
              >
                {[...new Set(rawData.map(r => r.Fecha))].sort().reverse().map(d => <option key={d} value={d} className="bg-slate-900">{d}</option>)}
              </select>
            </div>
          </div>
          
          <div className="flex-1 p-6 space-y-6">
             <section className="space-y-4">
                <div className="bg-slate-900/60 p-4 rounded-2xl border border-slate-800">
                  <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mb-1">Tonelaje Real</p>
                  <p className="text-xl font-black text-emerald-400">{stats.totalReal.toLocaleString()} T</p>
                </div>
                <div className="bg-slate-900/60 p-4 rounded-2xl border border-slate-800">
                  <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mb-1">Cumplimiento</p>
                  <p className="text-xl font-black text-white">{stats.compliance.toFixed(1)}%</p>
                </div>
             </section>

             <section className="pt-4 border-t border-slate-800">
                <div className="flex items-center gap-2 mb-4">
                  <Settings2 className="w-4 h-4 text-emerald-500" />
                  <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Configuración de Gráficos</h3>
                </div>
                
                <div className="space-y-3">
                  {userCharts.map((chart, idx) => (
                    <div key={idx} className={`rounded-xl border transition-all ${expandedChartConfig === idx ? 'bg-slate-900 border-slate-700 p-4' : 'bg-slate-900/40 border-slate-800 p-3 cursor-pointer hover:border-slate-700'}`} onClick={() => expandedChartConfig !== idx && setExpandedChartConfig(idx)}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[11px] font-bold text-slate-300 truncate pr-2">{idx + 1}. {chart.title}</span>
                        {expandedChartConfig === idx ? (
                          <ChevronUp className="w-4 h-4 text-slate-500 cursor-pointer" onClick={(e) => {e.stopPropagation(); setExpandedChartConfig(null)}} />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-slate-500" />
                        )}
                      </div>
                      
                      {expandedChartConfig === idx && (
                        <div className="space-y-4 mt-4 pt-4 border-t border-slate-800 animate-in fade-in duration-300">
                          <div>
                            <label className="block text-[9px] font-bold text-slate-500 uppercase mb-1">Título</label>
                            <input type="text" value={chart.title} onChange={(e) => updateChartConfig(idx, 'title', e.target.value)} className="w-full bg-slate-800 rounded-lg px-3 py-1.5 text-xs text-white outline-none focus:ring-1 focus:ring-emerald-500" />
                          </div>
                          <div>
                            <label className="block text-[9px] font-bold text-slate-500 uppercase mb-1">Tipo de Gráfico</label>
                            <select value={chart.type} onChange={(e) => updateChartConfig(idx, 'type', e.target.value as any)} className="w-full bg-slate-800 rounded-lg px-2 py-1.5 text-xs text-white outline-none cursor-pointer focus:ring-1 focus:ring-emerald-500">
                              <option value="bar">Barra</option>
                              <option value="line">Línea</option>
                              <option value="pie">Circular</option>
                              <option value="area">Área</option>
                            </select>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
             </section>
          </div>
          
          <div className="p-6 border-t border-slate-800 bg-slate-950/80 backdrop-blur-md sticky bottom-0 space-y-3">
            <button disabled={!config || exportingImage || exportingPDF} onClick={exportSummaryImage} className="w-full flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-emerald-400 py-3 rounded-xl font-black text-[11px] tracking-widest transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed border border-emerald-500/20">
              {exportingImage ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />} DESCARGAR RESUMEN (JPG)
            </button>
            <button disabled={rawData.length === 0 || exportingPDF} onClick={() => setShowExportModal(true)} className="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white py-3 rounded-xl font-bold transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed">
              <FileText className="w-4 h-4" /> EXPORTAR REPORTE PDF
            </button>
          </div>
        </aside>
      )}

      <main className={`flex-1 flex flex-col relative overflow-hidden bg-slate-50 ${exportingPDF ? 'overflow-visible bg-white' : ''}`}>
        {rawData.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center p-12 bg-white">
            <div className="w-20 h-20 bg-emerald-100 text-emerald-600 rounded-3xl flex items-center justify-center mb-8 animate-bounce"><FileUp className="w-8 h-8" /></div>
            <h1 className="text-3xl font-black text-slate-900 mb-2">Cargar Archivo de Despachos</h1>
            <label className="mt-8 cursor-pointer bg-slate-900 text-white px-8 py-4 rounded-2xl font-black hover:bg-slate-800 transition-all shadow-xl flex items-center gap-3">
              <input type="file" className="hidden" accept=".xlsm,.xlsx" onChange={e => e.target.files?.[0] && processFile(e.target.files[0])} />
              <FileUp className="w-5 h-5" /> SUBIR EXCEL (.XLSM)
            </label>
          </div>
        ) : (
          <div className={`flex-1 flex flex-col ${exportingPDF ? 'overflow-visible' : 'overflow-y-auto'}`}>
            {!exportingPDF && (
              <header className="sticky top-0 bg-white/95 backdrop-blur-md border-b border-slate-200 px-10 py-5 flex justify-between items-center z-20 no-print shadow-sm">
                <div className="flex flex-col">
                  <h2 className="text-xl font-black text-slate-900 uppercase tracking-tighter">Jornada: {selectedDate}</h2>
                  {analyzing && <span className="text-[10px] font-bold text-emerald-600 animate-pulse uppercase tracking-widest mt-1">Sincronizando análisis IA...</span>}
                </div>
              </header>
            )}

            <div id="dashboard-report" className={`${exportingPDF ? 'w-[1056px] min-w-[1056px] overflow-visible bg-white' : 'max-w-7xl mx-auto w-full'}`}>
              <div id="teaser-capture-zone" className="bg-white">
                {(!exportingPDF || pdfOptions.summary) && renderSummaryPage()}
                {(!exportingPDF || pdfOptions.charts) && chartChunks.length > 0 && renderChartsPage(chartChunks[0], 0, chartChunks.length)}
              </div>
              {(!exportingPDF || pdfOptions.charts) && chartChunks.slice(1).map((chunk, chunkIdx) => renderChartsPage(chunk, chunkIdx + 1, chartChunks.length))}
              {(!exportingPDF || pdfOptions.products) && productList.map((prod, index) => (
                <div key={prod} className={pdfPageClass} style={{ pageBreakAfter: 'always' }}>
                   <div className="flex justify-between items-center mb-10 border-b border-slate-100 pb-6">
                      <div>
                        <span className="text-[10px] font-black text-slate-400 uppercase tracking-[0.5em] block mb-2">Desglose Técnico</span>
                        <h2 className="text-4xl font-black text-slate-900 uppercase tracking-tighter">{prod}</h2>
                      </div>
                      <div className="text-right">
                        <span className="px-6 py-2 bg-slate-900 text-white text-[10px] font-black uppercase rounded-full">Producto {index + 1} de {productList.length}</span>
                      </div>
                   </div>
                   <div className="flex-1 overflow-visible">
                      <ProductDetailSection product={prod} data={filteredData.filter(d => d.Producto === prod)} compactMode={exportingPDF} />
                   </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {showExportModal && (
          <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-[60] flex items-center justify-center p-4">
             <div className="bg-white rounded-[3rem] shadow-2xl p-12 max-w-md w-full border border-slate-200 animate-in zoom-in duration-300">
                <div className="w-20 h-20 bg-emerald-50 text-emerald-600 rounded-3xl flex items-center justify-center mb-8"><FileText className="w-10 h-10" /></div>
                <h3 className="text-3xl font-black text-slate-900 uppercase tracking-tight mb-3">Preparar Reporte</h3>
                <div className="space-y-4 mb-12">
                   <div onClick={() => setPdfOptions(prev => ({...prev, summary: !prev.summary}))} className="flex items-center p-5 bg-slate-50 rounded-2xl cursor-pointer border border-slate-200 hover:border-emerald-500 transition-all">
                      {pdfOptions.summary ? <CheckSquare className="w-6 h-6 text-emerald-600 mr-4" /> : <Square className="w-6 h-6 text-slate-300 mr-4" />}
                      <span className="font-bold text-slate-800 text-sm uppercase tracking-widest">Resumen Ejecutivo</span>
                   </div>
                   <div onClick={() => setPdfOptions(prev => ({...prev, charts: !prev.charts}))} className="flex items-center p-5 bg-slate-50 rounded-2xl cursor-pointer border border-slate-200 hover:border-emerald-500 transition-all">
                      {pdfOptions.charts ? <CheckSquare className="w-6 h-6 text-emerald-600 mr-4" /> : <Square className="w-6 h-6 text-slate-300 mr-4" />}
                      <span className="font-bold text-slate-800 text-sm uppercase tracking-widest">Gráficos de Gestión</span>
                   </div>
                   <div onClick={() => setPdfOptions(prev => ({...prev, products: !prev.products}))} className="flex items-center p-5 bg-slate-50 rounded-2xl cursor-pointer border border-slate-200 hover:border-emerald-500 transition-all">
                      {pdfOptions.products ? <CheckSquare className="w-6 h-6 text-emerald-600 mr-4" /> : <Square className="w-6 h-6 text-slate-300 mr-4" />}
                      <span className="font-bold text-slate-800 text-sm uppercase tracking-widest">Detalle de Productos</span>
                   </div>
                </div>
                <div className="flex gap-4">
                   <button onClick={() => setShowExportModal(false)} className="flex-1 py-5 bg-slate-100 text-slate-500 rounded-2xl font-black uppercase text-xs tracking-widest hover:bg-slate-200 transition-all">Cancelar</button>
                   <button onClick={confirmExportPDF} className="flex-1 py-5 bg-emerald-600 text-white rounded-2xl font-black uppercase text-xs tracking-widest hover:bg-emerald-700 shadow-xl transition-all">Generar PDF</button>
                </div>
             </div>
          </div>
        )}
      </main>

      {(loading || exportingPDF || exportingImage) && (
        <div className="fixed inset-0 bg-slate-950/90 backdrop-blur-xl z-[100] flex items-center justify-center">
          <div className="bg-white p-16 rounded-[4rem] shadow-2xl flex flex-col items-center max-w-sm text-center">
            <div className="relative mb-10">
               <div className="w-28 h-28 border-[8px] border-emerald-50 border-t-emerald-600 rounded-full animate-spin" />
               <Loader2 className="w-12 h-12 text-emerald-600 absolute inset-0 m-auto animate-pulse" />
            </div>
            <h3 className="font-black text-3xl text-slate-900 mb-4">{exportingPDF ? "Exportando Reporte" : exportingImage ? "Generando Teaser" : "Procesando Datos"}</h3>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;
