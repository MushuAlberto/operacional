import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard Operacional SQM", layout="wide", page_icon="📈")

def call_gemini_api(prompt, api_key, model="gemini-1.5-flash"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.2}}
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        return response.json()['candidates'][0]['content']['parts'][0]['text'], None
    except:
        return "Error al conectar con la IA", "Error"

# --- 2. CARGA DE ARCHIVOS ---
st.title("📊 Control de Despachos y Cumplimiento")
col_up1, col_up2 = st.columns(2)

with col_up1:
    file_romanas = st.file_uploader("📁 02.- Histórico Romanas", type=["xlsx"])
with col_up2:
    file_tablero = st.file_uploader("📁 03.- Tablero Despachos (XLSM)", type=["xlsm"])

if file_tablero and file_romanas:
    try:
        # --- PROCESAMIENTO TABLERO (03) ---
        # Definimos las columnas por posición (B=1, AF=31, AG=32, AH=33, AI=34, AJ=35, AK=36, AL=37)
        cols_tablero = [1, 31, 32, 33, 34, 35, 36, 37] 
        df_tab = pd.read_excel(file_tablero, sheet_name="Base de Datos", usecols=cols_tablero, engine='openpyxl')
        
        # Renombramos para facilitar el uso
        df_tab.columns = ['Fecha', 'Producto', 'Destino', 'Ton_Prog', 'Ton_Real', 'Equipos_Prog', 'Equipos_Real', 'Cumplimiento']
        df_tab['Fecha'] = pd.to_datetime(df_tab['Fecha'], errors='coerce')
        df_tab = df_tab.dropna(subset=['Producto'])

        # --- PROCESAMIENTO ROMANAS (02) ---
        # Columnas W, X, Y son 22, 23, 24 (index 0)
        df_rom = pd.read_excel(file_romanas, usecols=[0, 22, 23, 24], engine='openpyxl') 
        df_rom.columns = ['Fecha_R', 'Regulacion_1', 'Regulacion_2', 'Regulacion_3']

        # --- 3. FILTROS LATERALES ---
        st.sidebar.header("🎯 Filtros de Dashboard")
        lista_productos = sorted(df_tab['Producto'].unique())
        prod_sel = st.sidebar.selectbox("Seleccionar Producto", lista_productos)
        
        # Filtrar datos por producto seleccionado
        df_p = df_tab[df_tab['Producto'] == prod_sel]

        # --- 4. VISUALIZACIÓN DE KPIs ---
        st.header(f"Dashboard: {prod_sel}")
        
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        t_prog = df_p['Ton_Prog'].sum()
        t_real = df_p['Ton_Real'].sum()
        cumpl_avg = (t_real / t_prog * 100) if t_prog > 0 else 0
        
        kpi1.metric("Ton. Programadas", f"{t_prog:,.1f}")
        kpi2.metric("Ton. Reales", f"{t_real:,.1f}")
        kpi3.metric("% Cumplimiento Total", f"{cumpl_avg:.1f}%")
        kpi4.metric("Equipos Reales", f"{df_p['Equipos_Real'].sum():.0f}")

        # --- 5. GRÁFICOS ---
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            # Gráfico de Barras: Prog vs Real por Destino
            df_dest = df_p.groupby('Destino')[['Ton_Prog', 'Ton_Real']].sum().reset_index()
            fig_dest = go.Figure(data=[
                go.Bar(name='Programado', x=df_dest['Destino'], y=df_dest['Ton_Prog'], marker_color='#A8D5BA'),
                go.Bar(name='Real', x=df_dest['Destino'], y=df_dest['Ton_Real'], marker_color='#2E7D32')
            ])
            fig_dest.update_layout(title="Cumplimiento por Destino (Toneladas)", barmode='group')
            st.plotly_chart(fig_dest, use_container_width=True)

        with col_g2:
            # Evolución del Cumplimiento
            fig_line = px.line(df_p, x='Fecha', y='Cumplimiento', title="Evolución % Cumplimiento Diario", markers=True)
            fig_line.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Meta 100%")
            st.plotly_chart(fig_line, use_container_width=True)

        # --- 6. REGULACIONES (Archivo Romanas) ---
        st.subheader("📋 Estado de Regulaciones (Histórico Romanas)")
        st.dataframe(df_rom.head(10), use_container_width=True)

        # --- 7. IA ANALYST ---
        st.divider()
        if st.button("🚀 Generar Análisis de Cumplimiento con IA"):
            api_k = st.secrets.get("GEMINI_API_KEY")
            if api_k:
                with st.spinner("Analizando brechas..."):
                    prompt = f"""
                    Analiza el producto {prod_sel}. 
                    Programado: {t_prog} Ton, Real: {t_real} Ton. 
                    Cumplimiento: {cumpl_avg:.1f}%.
                    Destinos afectados: {df_dest['Destino'].tolist()}.
                    Tarea: Indica si el cumplimiento es aceptable y qué factor podría estar fallando según la brecha de equipos.
                    """
                    res, err = call_gemini_api(prompt, api_k)
                    st.info(res)
            else:
                st.warning("Falta API Key.")

    except Exception as e:
        st.error(f"Error al leer los archivos: {e}. Asegúrate que las pestañas y columnas coincidan.")
else:
    st.info("Sube ambos archivos para generar el dashboard por producto.")
