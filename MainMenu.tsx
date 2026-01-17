import React from 'react';
import logo from './logo-sqm.png';

const MainMenu: React.FC = () => {
    return (
        <div className="bg-gray-100 min-h-screen p-4">
            <header className="flex items-center justify-center py-4">
                <img src={logo} alt="Logo" className="h-16" />
            </header>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="bg-white shadow-md rounded-lg p-4">
                    <h2 className="text-xl font-semibold">Llegada de Equipos</h2>
                    <p className="text-gray-600">Detalles sobre la llegada de los equipos.</p>
                </div>
                <div className="bg-white shadow-md rounded-lg p-4">
                    <h2 className="text-xl font-semibold">Informe Operativo</h2>
                    <p className="text-gray-600">Información sobre el informe operativo.</p>
                </div>
            </div>
        </div>
    );
};

export default MainMenu;