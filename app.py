import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime, date

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
        # Cargar datos desde la hoja especificada
        df = pd.read_excel(ARCHIVO, sheet_name=HOJA, engine='openpyxl', header=None)  # Sin encabezado

        # Renombrar columnas manualmente según posición (B: índice 1, E: índice 4, F: índice 5)
        df.columns = [f'Col_{i}' for i in range(df.shape[1])]
        df.rename(columns={
            1: 'Fecha',
            4: 'Tiempo_Faena_SdA',
            5: 'Tiempo_Puerto_Angamos'
        }, inplace=True)

        # Convertir columna de fechas (Columna B) a tipo datetime y filtrar solo fechas válidas
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df = df[df['Fecha'] >= pd.Timestamp('2025-01-01')]

        st.success("✅ Archivo cargado correctamente desde la hoja: `Base de Datos`")

        # Mostrar encabezado de datos
        st.subheader("📄 Vista previa de los datos")
        st.dataframe(df[['Fecha', 'Tiempo_Faena_SdA', 'Tiempo_Puerto_Angamos']].head())

        # Filtro por fecha usando un calendario
        st.markdown("### 📅 Selecciona una fecha:")
        fechas_disponibles = sorted(df['Fecha'].dt.date.unique())
        fecha_seleccionada = st.select_slider(
            "",
            options=fechas_disponibles,
            value=min(fechas_disponibles) if len(fechas_disponibles) > 0 else date.today()
        )

        # Formatear la fecha seleccionada para mostrarla de manera amigable
        fecha_formateada = fecha_seleccionada.strftime("%A, %d de %B de %Y").capitalize()
        st.markdown(f"#### 🗓️ Fecha seleccionada: **{fecha_formateada}**")

        # Filtrar datos según la fecha seleccionada
        df_filtrado = df[df['Fecha'].dt.date == fecha_seleccionada]

        # Calcular valores para Tiempo (Faena General SdA) y Puerto Angamos
        tiempo_faena_sda = df_filtrado['Tiempo_Faena_SdA'].sum() if not df_filtrado.empty else 0
        tiempo_puerto_angamos = df_filtrado['Tiempo_Puerto_Angamos'].sum() if not df_filtrado.empty else 0

        # Mostrar resultados en celdas destacadas
        st.markdown("### ⏰ Resultados por Fecha")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"""
            <div style="
                background-color:#f0f8ff;
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
                background-color:#fffaf0;
                padding:20px;
                border-radius:10px;
                text-align:center;
                font-size:1.2em;
                box-shadow: 2px 2px 6px rgba(0,0,0,0.1);">
                <strong>Tiempo (Puerto Angamos)</strong><br>
                {tiempo_puerto_angamos:.2f} horas
            </div>
            """, unsafe_allow_html=True)

        # Mostrar datos filtrados
        st.markdown("### 📋 Datos filtrados por fecha")
        st.dataframe(df_filtrado[['Fecha', 'Tiempo_Faena_SdA', 'Tiempo_Puerto_Angamos']], use_container_width=True)

        # Opcional: Análisis visual
        st.markdown("### 📊 Análisis Visual")

        columnas_numericas = ['Tiempo_Faena_SdA', 'Tiempo_Puerto_Angamos']
        col1, col2 = st.columns(2)

        if len(columnas_numericas) >= 1:
            with col1:
                fig, ax = plt.subplots()
                sns.histplot(df['Tiempo_Faena_SdA'].dropna(), kde=True, ax=ax, color="skyblue")
                ax.set_title("Distribución Tiempo Faena General SdA")
                st.pyplot(fig)

        if len(columnas_numericas) >= 2:
            with col2:
                fig, ax = plt.subplots()
                sns.scatterplot(data=df, x='Tiempo_Faena_SdA', y='Tiempo_Puerto_Angamos', ax=ax, color="coral")
                ax.set_title("Relación entre tiempos")
                st.pyplot(fig)

    except Exception as e:
        st.error(f"⚠️ Error al procesar el archivo: {e}")