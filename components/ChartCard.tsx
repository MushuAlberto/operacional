
import React, { useMemo } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  LineChart, Line, AreaChart, Area, PieChart, Pie, Cell, Legend, LabelList
} from 'recharts';

interface ChartCardProps {
  type: 'bar' | 'line' | 'pie' | 'area';
  data: any[];
  xAxis: string;
  yAxis: string | string[]; // Soporte para múltiples ejes
  title: string;
  isPrinting?: boolean;
}

const COLORS = [
  '#cbd5e1', '#1e293b', '#0068c9', '#83c9ff', '#ff2b2b', '#ffabab', '#29b09d', '#7defd1'
]; // Paleta ajustada para comparativas (Gris claro vs Azul oscuro/Negro)

const ChartCard: React.FC<ChartCardProps> = ({ type, data, xAxis, yAxis, title, isPrinting = false }) => {
  const yAxes = Array.isArray(yAxis) ? yAxis : [yAxis];

  // Added explicit return type any[] to ensure aggregatedData is not inferred as unknown[]
  const aggregatedData = useMemo((): any[] => {
    if (!data || data.length === 0) return [];
    
    const groups = data.reduce((acc: any, item: any) => {
      const key = String(item[xAxis] || 'S/D').trim();
      if (!key || key === 'undefined' || key === 'null') return acc;
      
      if (!acc[key]) {
        acc[key] = { name: key };
        yAxes.forEach(y => acc[key][y] = 0);
      }
      
      yAxes.forEach(y => {
        acc[key][y] += (Number(item[y]) || 0);
      });
      
      return acc;
    }, {});
    
    // Ordenar por el primer eje Y por defecto
    return Object.values(groups)
      .sort((a: any, b: any) => b[yAxes[0]] - a[yAxes[0]])
      .slice(0, 10);
  }, [data, xAxis, yAxis]);

  const renderChartContent = () => {
    const chartType = type?.toLowerCase();
    
    const commonProps = {
      data: aggregatedData,
      margin: { top: 30, right: 30, left: 0, bottom: 20 }
    };

    switch (chartType) {
      case 'bar':
        return (
          <BarChart {...commonProps} barGap={8}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f2f6" />
            <XAxis 
              dataKey="name" 
              axisLine={false} 
              tickLine={false} 
              tick={{fontSize: 10, fontWeight: 700, fill: '#64748b'}} 
              height={50} 
              interval={0} 
              angle={-45} 
              textAnchor="end" 
            />
            <YAxis hide />
            <Tooltip 
              cursor={{fill: '#f8fafc'}} 
              contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
            />
            {yAxes.length > 1 && <Legend verticalAlign="top" align="right" wrapperStyle={{paddingBottom: '20px', fontSize: '13px', fontWeight: '900'}} iconType="square" />}
            {yAxes.map((y, idx) => (
              <Bar key={y} isAnimationActive={false} dataKey={y} fill={COLORS[idx % COLORS.length]} radius={[4, 4, 0, 0]} barSize={yAxes.length > 1 ? 20 : 35} name={y.replace('_', ' ')}>
                <LabelList 
                  dataKey={y} 
                  position="top" 
                  offset={10} 
                  style={{ fill: COLORS[idx % COLORS.length] === '#cbd5e1' ? '#94a3b8' : '#1e293b', fontSize: '9px', fontWeight: '900' }} 
                  formatter={(v: any) => Math.round(Number(v)).toLocaleString()}
                />
              </Bar>
            ))}
          </BarChart>
        );
      case 'line':
        return (
          <LineChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f2f6" />
            <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fontSize: 10, fill: '#555'}} height={50} interval={0} angle={-45} textAnchor="end" />
            <YAxis hide />
            <Tooltip />
            {yAxes.map((y, idx) => (
              <Line key={y} isAnimationActive={false} type="monotone" dataKey={y} stroke={COLORS[idx % COLORS.length]} strokeWidth={3} dot={{ r: 4, fill: COLORS[idx % COLORS.length] }} name={y.replace('_', ' ')} />
            ))}
          </LineChart>
        );
      case 'pie':
        // Fix: Explicitly cast 'd' to any to prevent "Property 'name' does not exist on type 'unknown'"
        const pieData = aggregatedData.map((d: any) => ({ name: d.name, value: d[yAxes[0]] }));
        return (
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="40%"
              innerRadius={55}
              outerRadius={75}
              paddingAngle={5}
              dataKey="value"
              // Fix: Added explicit typing for label props
              label={({ value }: any) => `${Math.round(Number(value)).toLocaleString()}`}
              labelLine={{ stroke: '#cbd5e1', strokeWidth: 1 }}
              isAnimationActive={false}
            >
              {pieData.map((_, index) => <Cell key={`cell-${index}`} fill={COLORS[(index + 2) % COLORS.length]} />)}
            </Pie>
            <Tooltip />
            <Legend 
              verticalAlign="bottom" 
              height={80} 
              wrapperStyle={{ fontSize: '13px', fontWeight: '900', paddingTop: '10px' }} 
            />
          </PieChart>
        );
      default:
        return <div className="p-4 text-slate-400">Tipo no soportado</div>;
    }
  };

  return (
    <div className="bg-white p-6 rounded-[1.5rem] border border-slate-100 shadow-sm flex flex-col h-[420px]">
      <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-2">{title}</h3>
      <div className="flex-1 w-full">
        <ResponsiveContainer width="100%" height="100%">
          {renderChartContent()}
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ChartCard;
