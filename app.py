import streamlit as st
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Tablero Despachos", layout="wide")
st.title("🚚 Tablero de Despachos - Informe Operacional 2025")

# Instrucciones iniciales
st.markdown("""
### 📥 Carga tu archivo Excel
Por favor, carga el archivo `.xlsm` desde tu computadora.
El archivo debe contener una pestaña llamada **'Base de Datos'**.
""")

# Campo para cargar el archivo
archivo = st.file_uploader("Sube tu archivo .xlsm", type=["xlsm"])

if archivo is not None:
    try:
        # Leer todas las hojas del archivo
        xls = pd.ExcelFile(archivo, engine='openpyxl')

        # Verificar si existe la hoja 'Base de Datos'
        if 'Base de Datos' not in xls.sheet_names:
            st.error("⚠️ No se encontró la hoja 'Base de Datos'.")
        else:
            # Leer la hoja sin asumir encabezado
            df = pd.read_excel(xls, sheet_name='Base de Datos', header=None)

            st.markdown("### 🧾 Vista previa del archivo cargado:")
            st.dataframe(df.head(10))

            st.markdown("### 🔍 Selecciona las columnas que deseas usar:")

            # Seleccionar columna de Fecha
            col_fecha = st.number_input("Número de columna para 'Fecha' (empieza desde 0)", min_value=0, max_value=20, value=1)
            # Seleccionar columna Tiempo Faena General SdA
            col_faena = st.number_input("Número de columna para 'Tiempo (Faena General SdA)'", min_value=0, max_value=20, value=4)
            # Seleccionar columna Puerto Angamos
            col_puerto = st.number_input("Número de columna para 'Tiempo (Puerto Angamos)'", min_value=0, max_value=20, value=5)

            # Renombrar columnas según selección
            df.columns = [f'Col_{i}' for i in range(df.shape[1])]
            df.rename(columns={
                col_fecha: 'Fecha',
                col_faena: 'Tiempo_Faena_SdA',
                col_puerto: 'Tiempo_Puerto_Angamos'
            }, inplace=True)

            # Convertir fecha y filtrar
            df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
            df = df[df['Fecha'] >= '2025-01-01']

            fechas_disponibles = sorted(df['Fecha'].dt.date.unique())

            if len(fechas_disponibles) == 0:
                st.warning("No hay datos disponibles con fechas desde el 01/01/2025.")
            else:
                st.markdown("## 📅 Selecciona una fecha para ver los datos del día")

                fecha_seleccionada = st.date_input(
                    "Elige una fecha:",
                    min_value=min(fechas_disponibles),
                    max_value=max(fechas_disponibles),
                    value=min(fechas_disponibles)
                )

                fecha_formateada = fecha_seleccionada.strftime("%A, %d de %B de %Y").capitalize()
                st.markdown(f"### 🗓️ Fecha seleccionada: **{fecha_formateada}**")

                df_filtrado = df[df['Fecha'].dt.date == fecha_seleccionada]

                if df_filtrado.empty:
                    st.info(f"No hay registros disponibles para la fecha: {fecha_seleccionada}.")
                else:
                    tiempo_faena_sda = df_filtrado['Tiempo_Faena_SdA'].sum()
                    tiempo_puerto_angamos = df_filtrado['Tiempo_Puerto_Angamos'].sum()

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

                    st.markdown("### 📋 Detalles del día")
                    st.dataframe(df_filtrado[['Fecha', 'Tiempo_Faena_SdA', 'Tiempo_Puerto_Angamos']], use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ Error al procesar el archivo: {e}")
else:
    st.info("📌 Por favor, carga un archivo .xlsm para comenzar.")