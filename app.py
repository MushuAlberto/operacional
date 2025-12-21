import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard SQM", layout="wide")

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')

# --- 2. DICCIONARIO MAESTRO DE LIMPIEZA ---
MAPE_EMPRESAS = {
    # M&Q SPA
    "M AND Q SPA": "M&Q SPA", "M AND Q": "M&Q SPA", "M Q SPA": "M&Q SPA", 
    "MQ SPA": "M&Q SPA", "MANDQ SPA": "M&Q SPA", "MINING AND QUARRYING SPA": "M&Q SPA",
    "MINING AND QUARRYNG SPA": "M&Q SPA", "M & Q": "M&Q SPA",
    
    # M S & D SPA
    "MINING SERVICES AND DERIVATES": "M S & D SPA",
    "MINING SERVICES AND DERIVATES SPA": "M S & D SPA",
    "M S AND D": "M S & D SPA", "M S AND D SPA": "M S & D SPA",
    "MSANDD SPA": "M S & D SPA", "M S D": "M S & D SPA",
    "M S D SPA": "M S & D SPA", "M S & D": "M S & D SPA",
    "MS&D SPA": "M S & D SPA", "M S & D SPA": "M S & D SPA",
    
    # JORQUERA
    "JORQUERA TRANSPORTE S A": "JORQUERA TRANSPORTE S. A.",
    "JORQUERA TRANSPORTE SA": "JORQUERA TRANSPORTE S. A.",
    "JORQUERA TRANSPORTE": "JORQUERA TRANSPORTE S. A.",

    # AG SERVICES
    "AG SERVICE SPA": "AG SERVICES SPA", "AG SERVICES": "AG SERVICES SPA",
    
    # COSEDUCAM
    "COSEDUCAM S A": "COSEDUCAM S A", "COSEDUCAM": "COSEDUCAM S A"
}

st.title("📊 Control de Gestión: Histórico de Romanas")

uploaded_file = st.file_uploader("Subir archivo", type=["xlsx", "csv"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        
        # --- LIMPIEZA INICIAL ---
        df.columns = df.columns.str.strip()
        df['FECHA'] = pd.to_datetime(df['FECHA'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['FECHA'])
        df['TONELAJE'] = pd.to_numeric(df['TONELAJE'], errors='coerce').fillna(0)

        # --- LIMPIEZA DE EMPRESAS (EL CORAZÓN DEL PROBLEMA) ---
        # 1. Convertir a string, quitar espacios extremos y pasar a MAYÚSCULAS
        df['EMPRESA DE TRANSPORTE'] = df['EMPRESA DE TRANSPORTE'].astype(str).str.strip().str.upper()
        
        # 2. Reemplazar múltiples espacios por uno solo (ej: "M   Q" -> "M Q")
        df['EMPRESA DE TRANSPORTE'] = df['EMPRESA DE TRANSPORTE'].str.replace(r'\s+', ' ', regex=True)
        
        # 3. Aplicar el diccionario de mapeo
        df['EMPRESA DE TRANSPORTE'] = df['EMPRESA DE TRANSPORTE'].replace(MAPE_EMPRESAS)

        # --- FILTROS ---
        st.sidebar.header("Filtros")
        fecha_sel = st.sidebar.date_input("Fecha", df['FECHA'].max().date())
        df_view = df[df['FECHA'].dt.date == fecha_sel]

        if not df_view.empty:
            # --- KPIs ---
            c1, c2 = st.columns(2)
            c1.metric("Tonelaje Total", f"{df_view['TONELAJE'].sum():,.2f}")
            c2.metric("Viajes", len(df_view))

            # --- GRÁFICO ---
            st.subheader("🚛 Desempeño por Empresa (Estandarizado)")
            
            # Agrupamos explícitamente para asegurar que se sumen
            df_grouped = df_view.groupby('EMPRESA DE TRANSPORTE')['TONELAJE'].sum().reset_index()
            df_grouped = df_grouped.sort_values(by='TONELAJE', ascending=False)

            fig = px.bar(
                df_grouped, x='EMPRESA DE TRANSPORTE', y='TONELAJE',
                color='TONELAJE', text_auto='.2s',
                color_continuous_scale='Greens'
            )
            st.plotly_chart(fig, use_container_width=True)

            with st.expander("Ver tabla de datos limpia"):
                st.write(df_grouped)
        else:
            st.warning("No hay datos para esta fecha.")
            
    except Exception as e:
        st.error(f"Error: {e}")
