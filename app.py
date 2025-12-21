import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import re

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard SQM", layout="wide")

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')

# --- 2. FUNCIÓN DE LIMPIEZA PROFUNDA ---
def normalizar_nombre(texto):
    if pd.isna(texto):
        return "SIN NOMBRE"
    # Convertir a mayúsculas
    texto = str(texto).upper()
    # Eliminar puntos, comas y símbolos raros (como el punto de S.A.)
    texto = re.sub(r'[.,]', '', texto)
    # Reemplazar "M & Q" o "M AND Q" por algo uniforme "M&Q" antes de quitar espacios
    texto = texto.replace(" AND ", "&").replace(" & ", "&")
    # Eliminar todos los espacios extras
    texto = " ".join(texto.split())
    return texto

# --- 3. DICCIONARIO DE MAPEO ACTUALIZADO ---
MAPE_EMPRESAS = {
    # M&Q
    "M&Q SPA": "M&Q SPA", "MQ SPA": "M&Q SPA", "M&Q": "M&Q SPA", "M & Q SPA": "M&Q SPA",
    "MINING AND QUARRYING SPA": "M&Q SPA", "MINING AND QUARRYNG SPA": "M&Q SPA",
    
    # M S & D
    "MS&D SPA": "M S & D SPA", "M S & D SPA": "M S & D SPA", "MSD SPA": "M S & D SPA",
    "MINING SERVICES AND DERIVATES SPA": "M S & D SPA", "M S AND D SPA": "M S & D SPA",
    
    # JORQUERA
    "JORQUERA TRANSPORTE S A": "JORQUERA TRANSPORTE S. A.",
    
    # AG SERVICES
    "AG SERVICE SPA": "AG SERVICES SPA", "AG SERVICES SPA": "AG SERVICES SPA"
}

st.title("📊 Control de Gestión: Histórico de Romanas")

uploaded_file = st.file_uploader("Subir archivo Excel", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()
        
        # Limpieza de fechas y números
        df['FECHA'] = pd.to_datetime(df['FECHA'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['FECHA'])
        df['TONELAJE'] = pd.to_numeric(df['TONELAJE'], errors='coerce').fillna(0)

        # --- APLICAR LIMPIEZA AGRESIVA ---
        # Primero normalizamos el texto (quitamos puntos y estandarizamos ampersands)
        df['EMPRESA DE TRANSPORTE'] = df['EMPRESA DE TRANSPORTE'].apply(normalizar_nombre)
        
        # Luego aplicamos el mapeo para agrupar
        df['EMPRESA DE TRANSPORTE'] = df['EMPRESA DE TRANSPORTE'].replace(MAPE_EMPRESAS)

        # --- FILTROS Y GRÁFICOS ---
        fecha_sel = st.sidebar.date_input("Fecha", df['FECHA'].max().date())
        df_view = df[df['FECHA'].dt.date == fecha_sel]

        if not df_view.empty:
            st.subheader("🚛 Desempeño por Empresa (Agrupamiento Total)")
            
            # AGRUPACIÓN MATEMÁTICA: Aquí es donde se suman las barras
            df_grouped = df_view.groupby('EMPRESA DE TRANSPORTE', as_index=False)['TONELAJE'].sum()
            df_grouped = df_grouped.sort_values(by='TONELAJE', ascending=False)

            fig = px.bar(
                df_grouped, x='EMPRESA DE TRANSPORTE', y='TONELAJE',
                color='TONELAJE', text_auto='.2s',
                color_continuous_scale='Greens'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("Verificar Agrupación"):
                st.write("Nombres únicos detectados hoy:", df_grouped['EMPRESA DE TRANSPORTE'].tolist())
        else:
            st.warning("No hay datos para esta fecha.")
            
    except Exception as e:
        st.error(f"Error: {e}")
