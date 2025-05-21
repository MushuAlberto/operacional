import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración inicial
st.set_page_config(page_title="Cargar y Analizar Excel", layout="wide")
st.title("📥 Carga y Análisis de Archivo Excel (.xlsm)")

st.markdown("""
### Instrucciones:
1. Usa el panel lateral para cargar tu archivo `.xlsm`.
2. Selecciona una hoja de cálculo.
3. Explora los datos y realiza análisis básico.
""")

# Sidebar para carga de archivo
st.sidebar.header("📂 Cargar Archivo Excel")
archivo = st.sidebar.file_uploader("Sube tu archivo .xlsm", type=["xlsm"])

if archivo is not None:
    try:
        # Leer todas las hojas del archivo
        xls = pd.ExcelFile(archivo, engine='openpyxl')
        hojas = xls.sheet_names
        st.sidebar.success("Archivo cargado correctamente.")

        # Selección de hoja
        hoja_seleccionada = st.sidebar.selectbox("Selecciona una hoja", hojas)

        # Leer datos de la hoja seleccionada
        df = pd.read_excel(xls, sheet_name=hoja_seleccionada)

        # Mostrar datos
        st.subheader(f"📄 Vista previa de la hoja: {hoja_seleccionada}")
        st.dataframe(df.head())

        # Opción de mostrar todo el DataFrame
        if st.checkbox("Mostrar todos los datos"):
            st.dataframe(df)

        # Informe estadístico
        if st.checkbox("📊 Mostrar resumen estadístico"):
            st.subheader("📈 Resumen estadístico")
            st.write(df.describe(include='all'))

        # Análisis visual
        st.subheader("📈 Análisis Visual")

        columnas_numericas = df.select_dtypes(include=['number']).columns.tolist()
        columnas_categoricas = df.select_dtypes(include=['object']).columns.tolist()

        if len(columnas_numericas) >= 1:
            col_x = st.selectbox("Selecciona columna numérica para histograma", columnas_numericas, key="hist")
            fig, ax = plt.subplots()
            sns.histplot(df[col_x].dropna(), kde=True, ax=ax)
            st.pyplot(fig)

        if len(columnas_numericas) >= 2:
            col_y = st.selectbox("Selecciona segunda columna numérica para gráfico de dispersión", columnas_numericas, key="scatter")
            fig, ax = plt.subplots()
            sns.scatterplot(data=df, x=col_x, y=col_y, ax=ax)
            st.pyplot(fig)

        if len(columnas_categoricas) >= 1:
            col_cat = st.selectbox("Selecciona columna categórica para conteo", columnas_categoricas, key="bar")
            conteo = df[col_cat].value_counts()
            st.bar_chart(conteo)

    except Exception as e:
        st.error(f"⚠️ Error al procesar el archivo: {e}")

else:
    st.info("📌 Por favor, carga un archivo .xlsm usando el panel lateral.")