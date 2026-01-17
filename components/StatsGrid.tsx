
import React from 'react';
import { DataRow } from '../types';

interface StatsGridProps {
  data: DataRow[];
}

const StatsGrid: React.FC<StatsGridProps> = ({ data }) => {
  if (data.length === 0) return null;

  const numericCols = Object.keys(data[0]).filter(key => 
    typeof data[0][key] === 'number' || (!isNaN(Number(data[0][key])) && data[0][key] !== '')
  );

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
      {numericCols.slice(0, 6).map(col => {
        const values = data.map(d => Number(d[col])).filter(v => !isNaN(v));
        const avg = values.reduce((a, b) => a + b, 0) / values.length;
        const max = Math.max(...values);
        const min = Math.min(...values);

        return (
          <div key={col} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <h4 className="text-xs font-bold text-slate-400 uppercase mb-3 truncate" title={col}>{col}</h4>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <p className="text-[10px] text-slate-500 uppercase">Promedio</p>
                <p className="font-bold text-slate-800">{avg.toLocaleString(undefined, {maximumFractionDigits: 1})}</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-500 uppercase">Máx</p>
                <p className="font-bold text-blue-600">{max.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-500 uppercase">Mín</p>
                <p className="font-bold text-indigo-600">{min.toLocaleString()}</p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default StatsGrid;
