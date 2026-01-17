import React from 'react';
import './MainMenu.css';

const MainMenu = () => {
    return (
        <div className="main-menu">
            <img src="https://www.example.com/sqm-logo.png" alt="SQM Logo" /> {/* Replace with the actual SQM logo URL */}
            <button className="button">Llegada de Equipos</button>
            <button className="button">Informe Operativo</button>
        </div>
    );
};

export default MainMenu;