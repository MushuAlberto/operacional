import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
from datetime import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Logística SQM 2025", layout="wide", page_icon="🚛")

def init_gemini():
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"], None
    return None, "⚠️ Configura GEMINI_API_KEY en los Secrets."

def call_gemini_api(prompt, api_key, model="gemini-1.5-flash"):
    model_name = model.replace("models/", "")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1200}
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code != 200:
            return None, f"Error {response.status_code}: {response.text}"
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text'], None
    except Exception as e:
        return None, str(e)

# --- 2. DICCIONARIO DE LIMPIEZA ---
MAPE_EMPRESAS = {
    "M AND Q SPA": "M&Q SPA", "M AND Q": "M&Q SPA", "M Q SPA": "M&Q SPA",
    "MQ SPA": "M&Q SPA", "MANDQ SPA": "M&Q SPA", "MINING AND QUARRYING SPA": "M&Q SPA",
    "M & Q SPA": "M&Q SPA", "M&Q": "M&Q SPA",
    "MINING SERVICES AND DERIVATES": "M S & D SPA",
    "M S AND D": "M S & D SPA", "M S D SPA": "M S & D SPA",
    "MS&D SPA": "M S & D SPA", "M S & D": "M S & D SPA"
}

api_key, error_msg = init_gemini()

st.title("📊 Control de Gestión Logística 2025 - SQM")
st.markdown("---")

# --- 3. CARGA DE ARCHIVOS DUAL ---
col_up1, col_up2 = st.columns(2)

with col_up1:
    file_romanas = st.file_uploader("📁 02.- Histórico Romanas (.xlsx)", type=["xlsx"])

with col_up2:
    file_tablero = st.file_uploader("📁 03.- Tablero Despachos - Informe Operacional (.xlsm)", type=["xlsm"])

# --- 4. PROCESAMIENTO DE DATOS ---
df_romanas = None
df_tablero = None

if file_romanas:
    try:
        df_romanas = pd.read_excel(file_romanas, engine='openpyxl')
        df_romanas.columns = df_romanas.columns.str.strip()
        df_romanas['FECHA'] = pd.to_datetime(df_romanas['FECHA'], dayfirst=True, errors='coerce')
        df_romanas = df_romanas.dropna(subset=['FECHA'])
        df_romanas['TONELAJE'] = pd.to_numeric(df_romanas['TONELAJE'], errors='coerce').fillna(0)
        df_romanas['PRODUCTO'] = df_romanas['PRODUCTO'].astype(str).str.strip().str.upper()
        if 'EMPRESA DE TRANSPORTE' in df_romanas.columns:
            df_romanas['EMPRESA DE TRANSPORTE'] = df_romanas['EMPRESA DE TRANSPORTE'].astype(str).str.strip().str.upper().replace(MAPE_EMPRESAS)
        st.sidebar.success("✅ Romanas cargado")
    except Exception as e:
        st.error(f"Error en Romanas: {e}")

if file_tablero:
    try:
        # Cargamos .xlsm especificando motor openpyxl
        df_tablero = pd.read_excel(file_tablero, engine='openpyxl')
        df_tablero.columns = df_tablero.columns.str.strip()
        st.sidebar.success("✅ Tablero Operacional cargado")
    except Exception as e:
        st.error(f"Error en Tablero: {e}")

# --- 5. LÓGICA DE ANÁLISIS ---
if df_romanas is not None:
    # Filtros Temporales
    f_max = df_romanas['FECHA'].max().date()
    f_inicio = st.sidebar.date_input("Inicio Periodo", f_max)
    f_fin = st.sidebar.date_input("Fin Periodo", f_max)
    
    mask = (df_romanas['FECHA'].dt.date >= f_inicio) & (df_romanas['FECHA'].dt.date <= f_fin)
    df_view = df_romanas.loc[mask].copy()

    if not df_view.empty:
        # Benchmark Mensual
        df_mes = df_romanas[(df_romanas['FECHA'].dt.month == f_inicio.month) & (df_romanas['FECHA'].dt.year == f_inicio.year)]
        prom_diario_mes = df_mes.groupby(df_mes['FECHA'].dt.date)['TONELAJE'].sum().mean()
        total_ton = df_view['TONELAJE'].sum()
        rendimiento_actual = total_ton / ((f_fin - f_inicio).days + 1)
        desviacion = ((rendimiento_actual - prom_diario_mes) / prom_diario_mes) * 100

        # KPIs Principales
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Tonelaje", f"{total_ton:,.0f} T")
        c2.metric("Promedio Diario", f"{rendimiento_actual:,.1f} T", f"{desviacion:.1f}% vs Mes")
        c3.metric("N° Viajes Romanas", len(df_view))

        # Visualización Dual
        tab1, tab2, tab3 = st.tabs(["📊 Romanas", "📋 Tablero Operacional", "🤖 IA & Reportes"])

        with tab1:
            col_a, col_b = st.columns(2)
            df_prod = df_view.groupby('PRODUCTO')['TONELAJE'].sum().reset_index().sort_values('TONELAJE', ascending=False)
            col_a.plotly_chart(px.bar(df_prod, x='PRODUCTO', y='TONELAJE', title="Carga por Producto", color_continuous_scale='Greens'), use_container_width=True)
            df_emp = df_view.groupby('EMPRESA DE TRANSPORTE')['TONELAJE'].sum().reset_index().sort_values('TONELAJE', ascending=False)
            col_b.plotly_chart(px.bar(df_emp, x='EMPRESA DE TRANSPORTE', y='TONELAJE', title="Ranking Empresas", color_continuous_scale='Blues'), use_container_width=True)

        with tab2:
            if df_tablero is not None:
                st.subheader("Información del Tablero Operacional 2025")
                st.dataframe(df_tablero, use_container_width=True)
            else:
                st.info("Sube el archivo .xlsm para visualizar el tablero operacional.")

        with tab3:
            st.subheader("Generación de Informes Ejecutivos")
            col_b1, col_b2 = st.columns(2)
            
            if col_b1.button("🔍 Diagnóstico Técnico", use_container_width=True):
                with st.spinner("Analizando..."):
                    ctx = f"Analiza: Desviación de {desviacion:.1f}% vs promedio mensual. Producto top: {df_prod.iloc[0]['PRODUCTO']}. Genera un análisis profesional para SQM."
                    res, err = call_gemini_api(ctx, api_key)
                    st.markdown(res if not err else err)

            if col_b2.button("📧 Preparar Correo Gerencia", type="primary", use_container_width=True):
                with st.spinner("Redactando..."):
                    ctx_mail = f"Redacta un correo para Gerencia de SQM. Datos: {total_ton}T totales, {len(df_view)} viajes, periodo {f_inicio} al {f_fin}. Menciona la desviación del {desviacion:.1f}% vs promedio mensual."
                    res, err = call_gemini_api(ctx_mail, api_key)
                    st.text_area("Copia el correo desde aquí:", res, height=350)
    else:
        st.warning("No hay datos para las fechas seleccionadas.")
else:
    st.info("👋 Por favor, carga los archivos Excel para comenzar el análisis.")
