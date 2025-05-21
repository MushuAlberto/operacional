import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Tablero Despachos", layout="wide")
st.title("🚚 Tablero de Despachos - Informe Operacional 2025")

# Rutas
ARCHIVO = "data/08.- Tablero Despachos - Informe Operacional 2025.xlsm"
HOJA = "Base de Datos"

# Verificar si el archivo existe
if not os.path.exists(ARCHIVO):
    st.error(f"""
    ⚠️ No se encontró el archivo:
    
    `{ARCHIVO}`
    
    Asegúrate de colocarlo dentro de la carpeta `data/`.
    """)
else:
    try:
        # Cargar datos desde la hoja especificada sin encabezado
        df = pd.read_excel(ARCHIVO, sheet_name=HOJA, engine='openpyxl', header=None)

        # Renombrar columnas por posición (Columna B = índice 1, E = índice 4, F = índice 5)
        df.columns = [f'Col_{i}' for i in range(df.shape[1])]
        df.rename(columns={
            1: 'Fecha',
            4: 'Tiempo_Faena_SdA',
            5: 'Tiempo_Puerto_Angamos'
        }, inplace=True)

        # Convertir columna Fecha a tipo datetime y filtrar fechas válidas desde 2025
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df = df[df['Fecha'] >= '2025-01-01']

        # Mostrar título del filtro
        st.markdown("## 📅 Selecciona una fecha para ver los datos del día")

        # Obtener lista de fechas disponibles
        fechas_disponibles = sorted(df['Fecha'].dt.date.unique())

        if len(fechas_disponibles) == 0:
            st.warning("No hay datos disponibles con fechas desde el 01/01/2025.")
        else:
            # Selector de fecha con date_input
            fecha_seleccionada = st.date_input(
                "Elige una fecha:",
                min_value=min(fechas_disponibles),
                max_value=max(fechas_disponibles),
                value=min(fechas_disponibles)
            )

            # Formatear fecha para mostrarla amigablemente
            fecha_formateada = fecha_seleccionada.strftime("%A, %d de %B de %Y").capitalize()
            st.markdown(f"### 🗓️ Fecha seleccionada: **{fecha_formateada}**")

            # Filtrar los datos por la fecha seleccionada
            df_filtrado = df[df['Fecha'].dt.date == fecha_seleccionada]

            if df_filtrado.empty:
                st.info(f"No hay registros disponibles para la fecha: {fecha_seleccionada}.")
            else:
                # Calcular totales del día
                tiempo_faena_sda = df_filtrado['Tiempo_Faena_SdA'].sum()
                tiempo_puerto_angamos = df_filtrado['Tiempo_Puerto_Angamos'].sum()

                # Mostrar resultados en celdas destacadas
                st.markdown("### ⏰ Resultados del día")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"""
                    <div style="
                        background-color:#e6f7ff;
                        padding:20px;
                        border-radius:10px;
                        text-align:center;
                        font-size:1.2em;
                        box-shadow: 2px 2px 6px rgba(0,0,0,0.1);">
                        <strong>Tiempo (Faena General SdA)</strong><br>
                        {tiempo_faena_sda:.2f} horas
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <div style="
                        background-color:#fff3e0;
                        padding:20px;
                        border-radius:10px;
                        text-align:center;
                        font-size:1.2em;
                        box-shadow: 2px 2px 6px rgba(0,0,0,0.1);">
                        <strong>Tiempo (Puerto Angamos)</strong><br>
                        {tiempo_puerto_angamos:.2f} horas
                    </div>
                    """, unsafe_allow_html=True)

                # Mostrar tabla de datos filtrados
                st.markdown("### 📋 Detalles del día")
                st.dataframe(df_filtrado[['Fecha', 'Tiempo_Faena_SdA', 'Tiempo_Puerto_Angamos']], use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ Error al procesar el archivo: {e}")