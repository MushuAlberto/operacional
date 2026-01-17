
import React, { useMemo } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  Legend, LabelList
} from 'recharts';
import { 
  Package, Truck, Target, MapPin, TrendingDown, TrendingUp
} from 'lucide-react';

interface ProductDetailSectionProps {
  product: string;
  data: any[];
  index?: number;
  total?: number;
}

const ProductDetailSection: React.FC<ProductDetailSectionProps> = ({ product, data, index = 1, total = 1 }) => {
  const stats = useMemo(() => {
    if (!data || data.length === 0) return null;
    const tonProg = data.reduce((a, b) => a + (Number(b.Ton_Prog) || 0), 0);
    const tonReal = data.reduce((a, b) => a + (Number(b.Ton_Real) || 0), 0);
    const eqProg = data.reduce((a, b) => a + (Number(b.Eq_Prog) || 0), 0);
    const eqReal = data.reduce((a, b) => a + (Number(b.Eq_Real) || 0), 0);
    const regSum = data.reduce((a, b) => a + (Number(b.Regulacion_Real) || 0), 0);
    const regProm = data.length > 0 ? regSum / data.length : 0;
    
    const destinations: Record<string, number> = {};
    data.forEach(d => { 
      const dest = String(d.Destino || 'S/D');
      destinations[dest] = (destinations[dest] || 0) + 1; 
    });
    const mainDestEntry = Object.entries(destinations).sort((a, b) => b[1] - a[1])[0];

    return {
      tonProg, tonReal, tonDiff: tonReal - tonProg,
      eqProg, eqReal, eqDiff: eqReal - eqProg,
      compliance: tonProg > 0 ? (tonReal / tonProg) * 100 : 0,
      avgReg: regProm,
      avgLoad: eqReal > 0 ? tonReal / eqReal : 0,
      mainDest: mainDestEntry ? mainDestEntry[0] : 'S/D',
      mainDestCount: mainDestEntry ? mainDestEntry[1] : 0
    };
  }, [data]);

  if (!stats) return null;

  const chartData = [
    { name: 'Tonelaje', Programado: stats.tonProg, Real: stats.tonReal },
    { name: 'Equipos', Programado: stats.eqProg, Real: stats.eqReal }
  ];

  const getStatusInfo = (compliance: number) => {
    if (compliance >= 95) return { text: 'CUMPLIMIENTO ÓPTIMO', classes: 'bg-emerald-50 text-emerald-600' };
    if (compliance >= 80) return { text: 'RANGO ACEPTABLE', classes: 'bg-amber-50 text-amber-600' };
    return { text: 'ACCIÓN REQUERIDA', classes: 'bg-rose-50 text-rose-600' };
  };

  const status = getStatusInfo(stats.compliance);

  return (
    <div className="flex flex-col space-y-4 w-full bg-white overflow-hidden">
      {/* Header Superior */}
      <div className="flex justify-between items-end border-b border-slate-100 pb-3">
        <div className="space-y-0.5">
          <p className="text-[8px] font-black text-emerald-500 uppercase tracking-[0.3em]">
            Desglose Operativo por Producto
          </p>
          <h2 className="text-4xl font-[900] text-[#1e293b] tracking-tighter leading-tight">
            {product}
          </h2>
        </div>
        <div className="bg-black text-white px-4 py-1.5 rounded-full text-[9px] font-black tracking-widest uppercase mb-1">
          Ítem {index} de {total}
        </div>
      </div>

      {/* Título de Producto Central */}
      <div className="flex flex-col items-center space-y-2 pt-1">
        <h3 className="text-lg font-black text-[#1e293b] uppercase tracking-tight">
          PRODUCTO: {product}
        </h3>
        <div className={`px-8 py-1.5 rounded-full ${status.classes} text-[9px] font-black tracking-[0.2em] shadow-sm border border-current/10`}>
          {status.text}
        </div>
      </div>

      {/* Grid de Métricas Principales */}
      <div className="grid grid-cols-4 gap-3">
        <MetricCard 
          icon={<Package className="w-4 h-4" />} 
          label="Tonelaje Real" 
          value={`${stats.tonReal.toLocaleString()} Ton`} 
          diff={stats.tonDiff} 
          unit="vs Prog"
        />
        <MetricCard 
          icon={<Truck className="w-4 h-4" />} 
          label="Equipos Reales" 
          value={`${stats.eqReal} EQ`} 
          diff={stats.eqDiff} 
          unit="vs Prog"
        />
        <MetricCard 
          icon={<Target className="w-4 h-4" />} 
          label="Cumplimiento" 
          value={`${stats.compliance.toFixed(1)}%`} 
          diff={stats.compliance - 100} 
          unit=""
          isPerc
        />
        <div className="bg-white p-5 rounded-[1.2rem] border border-slate-100 shadow-sm flex flex-col space-y-3">
          <div className="flex items-center gap-2 text-slate-300">
            <MapPin className="w-4 h-4" />
            <span className="text-[9px] font-black uppercase tracking-wider">Destino Principal</span>
          </div>
          <p className="text-lg font-black text-[#1e293b] leading-tight truncate" title={stats.mainDest}>
            {stats.mainDest}
          </p>
          <div className="bg-emerald-50 text-emerald-600 px-3 py-1 rounded-lg text-[10px] font-bold w-fit">
            ↑ {stats.mainDestCount} viajes
          </div>
        </div>
      </div>

      {/* Sección Inferior: Gráfico e Indicadores */}
      <div className="grid grid-cols-3 gap-6 pt-2">
        {/* Gráfico de Barras */}
        <div className="col-span-2 bg-white p-6 rounded-[1.5rem] border border-slate-100 shadow-sm flex flex-col space-y-4">
          <p className="text-[9px] font-black text-slate-400 uppercase tracking-[0.2em]">
            Comparativa Ejecución vs Programación
          </p>
          <div className="h-[240px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} barGap={15} margin={{ top: 20, right: 30, left: 20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fontSize: 11, fontWeight: 800, fill: '#94a3b8'}} />
                <YAxis hide />
                <Legend verticalAlign="top" align="right" wrapperStyle={{paddingBottom: '10px', fontSize: '13px', fontWeight: '900'}} iconType="square" iconSize={8} />
                <Bar isAnimationActive={false} dataKey="Programado" fill="#cbd5e1" radius={[6, 6, 6, 6]} barSize={40}>
                  <LabelList dataKey="Programado" position="top" formatter={(v: any) => v.toLocaleString()} style={{ fill: '#94a3b8', fontSize: '10px', fontWeight: '900' }} offset={8} />
                </Bar>
                <Bar isAnimationActive={false} dataKey="Real" fill="#1e293b" radius={[6, 6, 6, 6]} barSize={40}>
                  <LabelList dataKey="Real" position="top" formatter={(v: any) => v.toLocaleString()} style={{ fill: '#1e293b', fontSize: '10px', fontWeight: '900' }} offset={8} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Indicadores Adicionales */}
        <div className="bg-white p-6 rounded-[1.5rem] border border-slate-100 shadow-sm flex flex-col">
          <p className="text-[9px] font-black text-slate-400 uppercase tracking-[0.2em] mb-6">
            Indicadores Adicionales
          </p>
          <div className="flex-1 flex flex-col justify-center space-y-6">
            <IndicatorRow label="Regulación Promedio" value={`${stats.avgReg.toFixed(2)}%`} />
            <IndicatorRow label="Promedio de Carga" value={`${stats.avgLoad.toFixed(1)} Ton/EQ`} />
            <IndicatorRow 
              label="Desviación Ton." 
              value={`${(stats.compliance - 100).toFixed(1)}%`} 
              color={stats.compliance >= 100 ? 'text-emerald-600' : 'text-rose-600'} 
            />
          </div>
        </div>
      </div>
    </div>
  );
};

const MetricCard = ({ icon, label, value, diff, unit, isPerc }: any) => {
  const isPos = diff >= 0;
  return (
    <div className="bg-white p-5 rounded-[1.2rem] border border-slate-100 shadow-sm flex flex-col space-y-4">
      <div className="flex items-center gap-2 text-slate-300">
        {icon}
        <span className="text-[9px] font-black uppercase tracking-wider">{label}</span>
      </div>
      <p className="text-2xl font-black text-[#1e293b] tracking-tighter">{value}</p>
      <div className={`flex items-center gap-1.5 text-[10.5px] font-black px-3.5 py-1.5 rounded-lg w-fit ${isPos ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'}`}>
        {isPos ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
        {isPos ? '+' : ''}{isPerc ? diff.toFixed(1) : diff.toLocaleString()} {unit}
      </div>
    </div>
  );
};

const IndicatorRow = ({ label, value, color }: any) => (
  <div className="flex justify-between items-center border-b border-slate-50 pb-3 last:border-0 last:pb-0">
    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{label}</span>
    <span className={`text-xl font-black ${color || 'text-[#1e293b]'} tracking-tighter`}>{value}</span>
  </div>
);

export default ProductDetailSection;
