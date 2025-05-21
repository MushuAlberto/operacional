import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Dashboard Excel", layout="wide")
st.title("📊 App de Análisis desde Excel (.xlsm)")
st.sidebar.header("Opciones")

# Cargar archivo
archivo = st.sidebar.file_uploader("Sube tu archivo .xlsm", type=["xlsm"])

if archivo is not None:
    try:
        # Leer todas las hojas
        xls = pd.ExcelFile(archivo, engine='openpyxl')
        hojas = xls.sheet_names
        hoja_seleccionada = st.sidebar.selectbox("Selecciona una hoja", hojas)

        df = pd.read_excel(xls, sheet_name=hoja_seleccionada)

        st.subheader(f"Datos de la hoja: {hoja_seleccionada}")
        st.dataframe(df.head())

        # Informe básico
        if st.checkbox("Mostrar resumen estadístico"):
            st.subheader("📊 Resumen estadístico")
            st.write(df.describe(include='all'))

        # Dashboard
        st.subheader("📈 Visualización de Datos")

        columnas_numericas = df.select_dtypes(include=['number']).columns.tolist()
        columnas_categoricas = df.select_dtypes(include=['object']).columns.tolist()

        if len(columnas_numericas) >= 1:
            col_x = st.selectbox("Selecciona columna numérica para histograma", columnas_numericas)
            fig, ax = plt.subplots()
            sns.histplot(df[col_x].dropna(), kde=True, ax=ax)
            st.pyplot(fig)

        if len(columnas_numericas) >= 2:
            col_y = st.selectbox("Selecciona segunda columna numérica para gráfico de dispersión", columnas_numericas)
            fig, ax = plt.subplots()
            sns.scatterplot(data=df, x=col_x, y=col_y, ax=ax)
            st.pyplot(fig)

        if len(columnas_categoricas) >= 1:
            col_cat = st.selectbox("Selecciona columna categórica para conteo", columnas_categoricas)
            conteo = df[col_cat].value_counts()
            st.bar_chart(conteo)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")

else:
    st.info("Por favor, carga un archivo .xlsm para comenzar.")