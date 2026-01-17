
import React, { useState, useMemo, useCallback, useRef } from 'react';
import * as XLSX from 'xlsx';
import { 
  Upload, FileText, Download, Calendar, Filter, 
  MapPin, Building2, Clock, ArrowLeft, Loader2, ChevronRight, Truck
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, 
  Legend, ResponsiveContainer 
} from 'recharts';

interface ArrivalData {
  fecha: string;
  destino: string;
  empresa: string;
  hora: number;
}

interface LlegadaEquiposProps {
  onBack: () => void;
}

const LOGO_SQM = "https://www.sqm.com/wp-content/uploads/2021/03/logo-sqm-header.svg";

const COMPANY_LOGOS: Record<string, string> = {
  "COSEDUCAM S A": "CD",
  "M&Q SPA": "MQ",
  "M S & D SPA": "MSD",
  "AGRETOC": "AT",
  "JORQUERA TRANSPORTE S. A.": "JQ",
  "AG SERVICES SPA": "AGS"
};

const parseExcelDate = (val: any): string => {
  if (val instanceof Date) return val.toISOString().split('T')[0];
  if (typeof val === 'number') {
    const d = new Date((val - 25569) * 86400 * 1000);
    return !isNaN(d.getTime()) ? d.toISOString().split('T')[0] : '';
  }
  if (typeof val === 'string' && val.trim() !== '') {
    const clean = val.trim();
    if (/^\d{4}-\d{2}-\d{2}/.test(clean)) return clean.split(' ')[0];
    const parts = clean.split(/[-/]/);
    if (parts.length === 3) {
      if (parts[0].length === 2) return `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
    }
  }
  return '';
};

const normalizarNombreEmpresa = (nombre: any): string => {
  let n = String(nombre || '').trim().toUpperCase();
  if (!n) return 'SIN EMPRESA';
  n = n.replace(/\./g, '').replace(/&/g, 'AND');
  n = n.split(/\s+/).join(' ');
  const equivalencias: Record<string, string> = {
    "JORQUERA TRANSPORTE S A": "JORQUERA TRANSPORTE S. A.",
    "JORQUERA TRANSPORTE SA": "JORQUERA TRANSPORTE S. A.",
    "MINING SERVICES AND DERIVATES": "M S & D SPA",
    "MINING SERVICES AND DERIVATES SPA": "M S & D SPA",
    "M S AND D": "M S & D SPA",
    "M S AND D SPA": "M S & D SPA",
    "MSANDD SPA": "M S & D SPA",
    "M S D": "M S & D SPA",
    "M S D SPA": "M S & D SPA",
    "M S & D": "M S & D SPA",
    "M S & D SPA": "M S & D SPA",
    "MS&D SPA": "M S & D SPA",
    "M AND Q SPA": "M&Q SPA",
    "M AND Q": "M&Q SPA",
    "M Q SPA": "M&Q SPA",
    "M & Q": "M&Q SPA",
    "MQ SPA": "M&Q SPA",
    "M&Q SPA": "M&Q SPA",
    "MANDQ SPA": "M&Q SPA",
    "MINING AND QUARRYING SPA": "M&Q SPA",
    "MINING AND QUARRYNG SPA": "M&Q SPA",
    "AG SERVICE SPA": "AG SERVICES SPA",
    "AG SERVICES SPA": "AG SERVICES SPA",
    "AG SERVICES": "AG SERVICES SPA",
    "COSEDUCAM": "COSEDUCAM S A",
    "AGRETOC": "AGRETOC"
  };
  return equivalencias[n] || n;
};

const normalizarDestino = (destino: any): string => {
  const d = String(destino || '').trim().toUpperCase();
  if (!d) return 'S/D';
  if (["BAQUEDANO/CLB", "BAQUEDANO CLB", "BAQ"].includes(d)) return "BAQUEDANO";
  return d;
};

const LlegadaEquipos: React.FC<LlegadaEquiposProps> = ({ onBack }) => {
  const [rawData, setRawData] = useState<ArrivalData[]>([]);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [selectedDestinos, setSelectedDestinos, ] = useState<string[]>([]);
  const [selectedEmpresas, setSelectedEmpresas] = useState<string[]>([]);
  const [hourRange, setHourRange] = useState<[number, number]>([0, 23]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const bstr = evt.target?.result;
        const wb = XLSX.read(bstr, { type: 'binary', cellDates: true });
        const ws = wb.Sheets[wb.SheetNames[0]];
        const data = XLSX.utils.sheet_to_json(ws, { header: 1 }) as any[][];
        if (data.length < 2) throw new Error("Archivo insuficiente.");
        const processed: ArrivalData[] = data.slice(1).map((row) => {
          const fechaStr = parseExcelDate(row[0]);
          if (!fechaStr) return null;
          const empresaRaw = row[11];
          if (empresaRaw === undefined || empresaRaw === null) return null;
          let hora = 0;
          const rawHora = row[14]; 
          if (typeof rawHora === 'string') {
            const parts = rawHora.split(':');
            hora = parts.length > 0 ? parseInt(parts[0]) : 0;
          } else if (rawHora instanceof Date) {
            hora = rawHora.getHours();
          } else if (typeof rawHora === 'number') {
            hora = Math.floor(rawHora * 24);
          }
          return {
            fecha: fechaStr,
            destino: normalizarDestino(row[3]),
            empresa: normalizarNombreEmpresa(row[11]),
            // Fixed typo: 'h' was not defined, should be 'hora'
            hora: isNaN(hora) ? 0 : hora
          };
        }).filter((r): r is ArrivalData => r !== null);
        setRawData(processed);
        const dates = [...new Set(processed.map(r => r.fecha))].sort();
        if (dates.length > 0) setSelectedDate(dates[dates.length - 1]);
      } catch (err) {
        console.error("Error cargando Excel:", err);
      } finally {
        setLoading(false);
      }
    };
    reader.readAsBinaryString(file);
  };

  const availableDates = useMemo(() => [...new Set(rawData.map(r => r.fecha))].sort(), [rawData]);
  const filteredByDate = useMemo(() => rawData.filter(r => r.fecha === selectedDate), [rawData, selectedDate]);
  const availableDestinos = useMemo(() => [...new Set(filteredByDate.map(r => r.destino))].sort(), [filteredByDate]);
  const availableEmpresas = useMemo(() => [...new Set(filteredByDate.map(r => r.empresa))].sort(), [filteredByDate]);

  React.useEffect(() => {
    if (availableDestinos.length > 0) setSelectedDestinos(availableDestinos);
    if (availableEmpresas.length > 0) setSelectedEmpresas(availableEmpresas);
  }, [availableDestinos, availableEmpresas]);

  const finalData = useMemo(() => {
    return filteredByDate.filter(r => 
      selectedDestinos.includes(r.destino) &&
      selectedEmpresas.includes(r.empresa) &&
      r.hora >= hourRange[0] &&
      r.hora <= hourRange[1]
    );
  }, [filteredByDate, selectedDestinos, selectedEmpresas, hourRange]);

  const exportPDF = async (empresa: string) => {
    const html2canvas = (window as any).html2canvas;
    const jsPDFConstructor = (window as any).jspdf?.jsPDF || (window as any).jsPDF;
    
    if (!html2canvas || !jsPDFConstructor) {
      alert("Error: Librerías de exportación no encontradas.");
      return;
    }

    setExporting(true);
    
    try {
      const p1Element = document.getElementById(`pdf-page1-${empresa}`);
      const p2Element = document.getElementById(`pdf-page2-${empresa}`);

      if (!p1Element || !p2Element) {
        throw new Error("No se encontraron los elementos del reporte.");
      }

      const canvas1 = await html2canvas(p1Element, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#ffffff',
        logging: false
      });

      const canvas2 = await html2canvas(p2Element, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#ffffff',
        logging: false
      });

      const pdf = new jsPDFConstructor('l', 'mm', 'a4');
      const imgData1 = canvas1.toDataURL('image/jpeg', 1.0);
      pdf.addImage(imgData1, 'JPEG', 0, 0, 297, 210);

      pdf.addPage('a4', 'p');
      const imgData2 = canvas2.toDataURL('image/jpeg', 1.0);
      pdf.addImage(imgData2, 'JPEG', 0, 0, 210, 297);

      pdf.save(`Reporte_Equipos_${empresa}_${selectedDate}.pdf`);

    } catch (err) {
      console.error("Error al exportar:", err);
      alert("Error al generar el PDF.");
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#f8fafc] overflow-hidden">
      {/* SIDEBAR */}
      <aside className="w-80 bg-white border-r border-slate-200 overflow-y-auto p-6 flex flex-col gap-8 shrink-0 no-print">
        <button onClick={onBack} className="flex items-center gap-2 text-slate-400 hover:text-slate-600 font-black text-[10px] uppercase tracking-widest transition-colors group">
          <ArrowLeft size={14} className="group-hover:-translate-x-1 transition-transform" /> Volver al Menú
        </button>
        <div className="space-y-4">
          <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100 flex justify-center">
            <img src={LOGO_SQM} alt="SQM" className="h-8 w-auto grayscale opacity-50" />
          </div>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-white shadow-lg">
              <Clock size={20} />
            </div>
            <div>
              <h2 className="text-xl font-black text-slate-800 tracking-tight leading-none">Llegada Equipos</h2>
              <p className="text-[9px] text-slate-400 font-bold uppercase tracking-widest mt-1">Control Horario Digital</p>
            </div>
          </div>
        </div>
        <div className="space-y-6">
          <div className="space-y-2">
            <label className="text-[11px] font-black text-slate-500 uppercase tracking-wider flex items-center gap-2"><Upload size={14} /> Cargar Datos (.xlsx)</label>
            <label className="flex flex-col items-center justify-center w-full h-24 border-2 border-dashed border-slate-200 rounded-2xl cursor-pointer bg-slate-50 hover:bg-white hover:border-blue-300 transition-all group">
              <div className="flex flex-col items-center justify-center py-4 text-center px-2">
                <FileText className="w-6 h-6 text-slate-300 mb-1" />
                <p className="text-[9px] text-slate-400 font-bold uppercase">Seleccionar archivo</p>
              </div>
              <input type="file" className="hidden" accept=".xlsx" onChange={handleFileUpload} />
            </label>
          </div>
          {rawData.length > 0 && (
            <>
              <div className="space-y-2">
                <label className="text-[11px] font-black text-slate-500 uppercase tracking-wider flex items-center gap-2"><Calendar size={14} /> Fecha</label>
                <select value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} className="w-full bg-slate-50 border border-slate-100 rounded-xl px-4 py-2 text-sm font-bold text-slate-700 outline-none">
                  {availableDates.map(d => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-[11px] font-black text-slate-500 uppercase tracking-wider flex items-center gap-2"><MapPin size={14} /> Destinos</label>
                <div className="max-h-32 overflow-y-auto bg-slate-50 rounded-xl border border-slate-100 p-3 space-y-1">
                  {availableDestinos.map(dest => (
                    <label key={dest} className="flex items-center gap-2 text-[10px] font-bold text-slate-600 cursor-pointer hover:bg-white p-1 rounded transition-colors">
                      <input type="checkbox" checked={selectedDestinos.includes(dest)} onChange={(e) => {
                        if (e.target.checked) setSelectedDestinos(prev => [...prev, dest]);
                        else setSelectedDestinos(prev => prev.filter(x => x !== dest));
                      }} /> {dest}
                    </label>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto p-10 space-y-16">
        {loading ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-400 space-y-4">
            <Loader2 className="w-12 h-12 animate-spin text-blue-500" />
            <p className="text-sm font-black uppercase tracking-widest">Analizando logística...</p>
          </div>
        ) : rawData.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-300 space-y-6">
            <div className="w-24 h-24 bg-white rounded-3xl flex items-center justify-center shadow-sm border border-slate-100"><Upload size={48} className="text-slate-100" /></div>
            <div className="text-center space-y-2">
              <h3 className="text-2xl font-black text-slate-400 tracking-tight">Cargue un archivo para comenzar</h3>
            </div>
          </div>
        ) : (
          <div className="space-y-24 max-w-7xl mx-auto pb-20">
            {selectedEmpresas.map(empresa => {
              const dataEmpresa = finalData.filter(d => d.empresa === empresa);
              const chartData = Array.from({ length: 24 }, (_, h) => {
                const point: any = { name: h };
                selectedDestinos.forEach(dest => {
                  point[dest] = dataEmpresa.filter(d => d.hora === h && d.destino === dest).length;
                });
                return point;
              });

              return (
                <div key={empresa} className="space-y-4">
                  {/* Vista Dashboard (UI) */}
                  <div className="bg-white rounded-[3rem] border border-slate-100 shadow-xl overflow-hidden p-12 space-y-10">
                    <div className="flex justify-between items-center border-b border-slate-100 pb-8">
                      <div className="flex gap-6 items-center">
                        <div className="w-16 h-16 bg-slate-900 rounded-2xl flex items-center justify-center text-white font-black text-xl shadow-lg overflow-hidden">
                           <img src={`https://placehold.co/100x100/1e293b/white?text=${COMPANY_LOGOS[empresa] || 'AGS'}`} alt="Empresa" />
                        </div>
                        <div>
                          <p className="text-[10px] font-black text-blue-600 uppercase tracking-widest">Operaciones Litio</p>
                          <h2 className="text-4xl font-black text-slate-800 tracking-tighter uppercase">{empresa}</h2>
                        </div>
                      </div>
                      <button 
                        onClick={() => exportPDF(empresa)}
                        disabled={exporting}
                        className="bg-slate-900 text-white px-8 py-3 rounded-2xl text-[11px] font-black tracking-widest uppercase hover:bg-slate-800 transition-all flex items-center gap-3 no-print disabled:opacity-50"
                      >
                        {exporting ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />} 
                        Exportar PDF
                      </button>
                    </div>
                    
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
                        <div className="h-80 w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={chartData}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                    <XAxis dataKey="name" tick={{fontSize: 10, fontWeight: 800}} />
                                    <YAxis tick={{fontSize: 10, fontWeight: 800}} />
                                    <Tooltip />
                                    <Legend />
                                    {selectedDestinos.map((dest, idx) => (
                                        <Line key={dest} type="monotone" dataKey={dest} stroke={['#2563eb', '#dc2626', '#10b981', '#f59e0b', '#000000'][idx % 5]} strokeWidth={3} dot={{r: 4}} name={dest} />
                                    ))}
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="bg-slate-50 p-6 rounded-3xl">
                            <h4 className="text-xs font-black text-slate-400 uppercase mb-4">Resumen de Equipos</h4>
                            <div className="space-y-4">
                                {selectedDestinos.map(dest => {
                                    const count = dataEmpresa.filter(d => d.destino === dest).length;
                                    return (
                                        <div key={dest} className="flex justify-between items-center border-b border-slate-200 pb-2">
                                            <span className="text-xs font-bold text-slate-600">{dest}</span>
                                            <span className="text-lg font-black text-slate-800">{count}</span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                  </div>

                  {/* --- PLANTILLAS PDF (OCULTAS) --- */}
                  <div style={{ position: 'absolute', left: '-10000px', top: '-10000px' }}>
                    <div id={`pdf-page1-${empresa}`} style={{ width: '297mm', height: '210mm', backgroundColor: 'white', padding: '15mm', boxSizing: 'border-box' }}>
                      <div className="flex justify-between items-center mb-10">
                        <img src={LOGO_SQM} alt="SQM" className="h-10 w-auto" />
                        <div className="text-right">
                          <h1 className="text-xl font-black text-slate-800 uppercase tracking-tighter">Reporte de Equipos</h1>
                          <p className="text-sm font-bold text-slate-500 uppercase tracking-widest">{selectedDate}</p>
                        </div>
                      </div>

                      <div className="relative h-1 mb-10 bg-[#89B821] rounded-full" />

                      <div className="flex items-center gap-8 mb-12 px-6">
                          <div className="w-24 h-24 bg-slate-900 rounded-2xl flex items-center justify-center text-white font-black text-3xl uppercase overflow-hidden">
                              <img src={`https://placehold.co/150x150/1e293b/white?text=${COMPANY_LOGOS[empresa] || 'AGS'}`} alt="Empresa" crossOrigin="anonymous" />
                          </div>
                          <div>
                              <h3 className="text-3xl font-black uppercase text-slate-800 tracking-tighter">{empresa}</h3>
                              <p className="text-xs text-slate-400 font-bold uppercase tracking-[0.3em] mt-1">Socio Logístico Estratégico SQM</p>
                          </div>
                      </div>

                      <div className="px-6">
                          <h4 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-6">Gráfico de Frecuencia Horaria</h4>
                          <div style={{ width: '250mm', height: '80mm' }}>
                              <ResponsiveContainer width="100%" height="100%">
                                  <LineChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
                                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                                      <XAxis dataKey="name" tick={{fontSize: 11, fontWeight: 'bold'}} label={{ value: 'HR ENTRADA', position: 'insideBottom', offset: -10, fontSize: 12, fontWeight: 'bold' }} />
                                      <YAxis tick={{fontSize: 11, fontWeight: 'bold'}} label={{ value: 'Cantidad', angle: -90, position: 'insideLeft', fontSize: 12, fontWeight: 'bold' }} />
                                      <Legend verticalAlign="top" align="right" wrapperStyle={{ paddingBottom: '20px', fontSize: '12px', fontWeight: 'bold' }} />
                                      {selectedDestinos.map((dest, idx) => (
                                          <Line 
                                            key={dest} 
                                            type="monotone" 
                                            dataKey={dest} 
                                            stroke={['#2563eb', '#dc2626', '#10b981', '#f59e0b', '#000000'][idx % 5]} 
                                            strokeWidth={3} 
                                            dot={{r: 5}} 
                                            name={dest} 
                                            isAnimationActive={false} 
                                          />
                                      ))}
                                  </LineChart>
                              </ResponsiveContainer>
                          </div>
                      </div>
                    </div>

                    <div id={`pdf-page2-${empresa}`} style={{ width: '210mm', minHeight: '297mm', backgroundColor: 'white', padding: '20mm', boxSizing: 'border-box' }}>
                       <div className="flex justify-between items-center mb-12 border-b-2 border-slate-100 pb-6">
                         <img src={LOGO_SQM} alt="SQM" className="h-8 w-auto grayscale" />
                         <span className="text-[10px] font-black uppercase tracking-widest text-slate-300">Detalle Operativo &bull; Pág 2</span>
                       </div>
                       
                       <h2 className="text-2xl font-black text-slate-800 text-center mb-12 uppercase tracking-tighter">Detalle por Destino y Horario</h2>
                       
                       <table className="w-full border-collapse" style={{ border: '2.5px solid #000' }}>
                          <thead>
                              <tr style={{ backgroundColor: '#f8fafc' }}>
                                  <th className="p-3 text-[11px] font-black text-center border-2 border-black uppercase" style={{ width: '25%' }}>Rango Horario</th>
                                  {selectedDestinos.map(dest => (
                                      <th key={dest} className="p-3 text-[10px] font-black text-center border-2 border-black uppercase leading-tight">
                                        {dest}
                                      </th>
                                  ))}
                              </tr>
                          </thead>
                          <tbody>
                              {Array.from({ length: 24 }, (_, h) => {
                                  return (
                                      <tr key={h}>
                                          <td className="p-2 text-[10px] font-bold text-center border-2 border-black">
                                              {h.toString().padStart(2, '0')}:00 - {h.toString().padStart(2, '0')}:59
                                          </td>
                                          {selectedDestinos.map(dest => {
                                              const count = dataEmpresa.filter(d => d.hora === h && d.destino === dest).length;
                                              return (
                                                  <td key={dest} className={`p-2 text-[11px] font-bold text-center border-2 border-black ${count > 0 ? 'bg-blue-50/30' : ''}`}>
                                                      {count}
                                                  </td>
                                              );
                                          })}
                                      </tr>
                                  );
                              })}
                              <tr style={{ backgroundColor: '#f1f5f9' }}>
                                  <td className="p-4 text-[12px] font-black uppercase tracking-widest text-left border-2 border-black">TOTAL JORNADA</td>
                                  {selectedDestinos.map(dest => {
                                      const totalDest = dataEmpresa.filter(d => d.destino === dest).length;
                                      return (
                                          <td key={dest} className="p-4 text-[14px] font-black text-center border-2 border-black">
                                              {totalDest}
                                          </td>
                                      );
                                  })}
                              </tr>
                          </tbody>
                       </table>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
};

export default LlegadaEquipos;
