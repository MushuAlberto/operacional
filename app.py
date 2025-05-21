import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
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
        # Cargar datos desde la hoja especificada
        df = pd.read_excel(ARCHIVO, sheet_name=HOJA, engine='openpyxl')

        # Convertir columna de fechas a tipo datetime (si no está ya en ese formato)
        if 'Fecha' in df.columns:
            df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')

        st.success("✅ Archivo cargado correctamente desde la hoja: `Base de Datos`")

        # Mostrar encabezado de datos
        st.subheader("📄 Vista previa de los datos")
        st.dataframe(df.head())

        # Filtro por fecha usando un calendario
        st.subheader("📅 Filtrar por fecha")
        fecha_seleccionada = st.date_input(
            "Selecciona una fecha:",
            value=df['Fecha'].min()  # Valor predeterminado: primera fecha disponible
        )

        # Formatear la fecha seleccionada para mostrarla de manera amigable
        fecha_formateada = fecha_seleccionada.strftime("%A, %d de %B de %Y")
        st.markdown(f"### Fecha: **{fecha_formateada}**")

        # Filtrar datos según la fecha seleccionada
        df_filtrado = df[df['Fecha'] == pd.Timestamp(fecha_seleccionada)]

        # Calcular valores para Tiempo (Faena General SdA) y Tiempo (Puerto Angamos)
        tiempo_faena_sda = df_filtrado['Tiempo (Faena General SdA)'].sum() if 'Tiempo (Faena General SdA)' in df.columns else 0
        tiempo_puerto_angamos = df_filtrado['Tiempo (Puerto Angamos)'].sum() if 'Tiempo (Puerto Angamos)' in df.columns else 0

        # Mostrar resultados en celdas destacadas
        st.subheader("⏰ Resultados por Fecha")
        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                label="Tiempo (Faena General SdA)",
                value=f"{tiempo_faena_sda:.2f} horas",
                delta=None,
                delta_color="normal",
                help="Tiempo acumulado en Faena General SdA"
            )

        with col2:
            st.metric(
                label="Tiempo (Puerto Angamos)",
                value=f"{tiempo_puerto_angamos:.2f} horas",
                delta=None,
                delta_color="normal",
                help="Tiempo acumulado en Puerto Angamos"
            )

        # Mostrar datos filtrados
        st.subheader("Datos filtrados por fecha")
        st.dataframe(df_filtrado)

        # Resumen estadístico
        if st.checkbox("📊 Mostrar resumen estadístico"):
            st.subheader("📈 Resumen estadístico")
            st.write(df.describe(include='all'))

        # Análisis visual
        st.subheader("📈 Análisis Visual")

        columnas_numericas = df.select_dtypes(include=['number']).columns.tolist()
        columnas_categoricas = df.select_dtypes(include=['object']).columns.tolist()

        col1, col2 = st.columns(2)

        if len(columnas_numericas) >= 1:
            with col1:
                col_x = st.selectbox("Selecciona columna numérica para histograma", columnas_numericas, key="histograma")
                fig, ax = plt.subplots()
                sns.histplot(df[col_x].dropna(), kde=True, ax=ax)
                st.pyplot(fig)

        if len(columnas_numericas) >= 2:
            with col2:
                col_y = st.selectbox("Selecciona segunda columna numérica", columnas_numericas, key="dispersion")
                fig, ax = plt.subplots()
                sns.scatterplot(data=df, x=col_x, y=col_y, ax=ax)
                st.pyplot(fig)

        if len(columnas_categoricas) >= 1:
            col_cat = st.selectbox("Selecciona columna categórica para conteo", columnas_categoricas, key="barras")
            conteo = df[col_cat].value_counts()
            st.bar_chart(conteo)

    except Exception as e:
        st.error(f"⚠️ Error al procesar el archivo: {e}")