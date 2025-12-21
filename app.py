import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard Operacional SQM", layout="wide", page_icon="📈")

def call_gemini_api(prompt, api_key, model="gemini-1.5-flash"):
    # Se usa v1beta para evitar errores 404 con modelos nuevos
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.2}}
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text'], None
        return f"Error API: {response.status_code}", "Error"
    except Exception as e:
        return f"Error de conexión: {str(e)}", "Error"

# --- 2. CARGA DE ARCHIVOS ---
st.title("📊 Control de Despachos y Cumplimiento Diario")
st.markdown("---")

col_up1, col_up2 = st.columns(2)
with col_up1:
    file_romanas = st.file_uploader("📁 02.- Histórico Romanas", type=["xlsx"])
with col_up2:
    file_tablero = st.file_uploader("📁 03.- Tablero Despachos (XLSM)", type=["xlsm"])

if file_tablero and file_romanas:
    try:
        # --- PROCESAMIENTO TABLERO (03) ---
        cols_tab = [1, 31, 32, 33, 34, 35, 36, 37] 
        df_tab = pd.read_excel(file_tablero, sheet_name="Base de Datos", usecols=cols_tab, engine='openpyxl')
        df_tab.columns = ['Fecha', 'Producto', 'Destino', 'Ton_Prog', 'Ton_Real', 'Eq_Prog', 'Eq_Real', 'Cumplimiento']
        
        # CORRECCIÓN DE FECHA: Se usa dayfirst=True y format='mixed' para evitar el error de la captura
        df_tab['Fecha'] = pd.to_datetime(df_tab['Fecha'], dayfirst=True, errors='coerce').dt.date
        df_tab = df_tab.dropna(subset=['Fecha', 'Producto'])
        df_tab['Producto'] = df_tab['Producto'].astype(str).str.strip().str.upper()

        # --- PROCESAMIENTO ROMANAS (02) ---
        df_rom = pd.read_excel(file_romanas, engine='openpyxl')
        df_rom.columns = df_rom.columns.str.strip().str.upper()
        if 'FECHA' in df_rom.columns:
            df_rom['FECHA'] = pd.to_datetime(df_rom['FECHA'], dayfirst=True, errors='coerce').dt.date

        # --- 3. FILTROS LATERALES ---
        st.sidebar.header("🎯 Parámetros")
        fechas_disp = sorted(df_tab['Fecha'].unique(), reverse=True)
        fecha_sel = st.sidebar.selectbox("Seleccione la Fecha", fechas_disp)
        
        df_fecha = df_tab[df_tab['Fecha'] == fecha_sel]
        productos_disp = sorted(df_fecha['Producto'].unique())
        prod_sel = st.sidebar.selectbox("Seleccione el Producto", productos_disp)
        
        df_p = df_fecha[df_fecha['Producto'] == prod_sel]

        # --- 4. LÓGICA DE REGULACIONES (Archivo 02) ---
        reg1, reg2, reg3 = 0, 0, 0
        if 'PRODUCTO' in df_rom.columns and 'FECHA' in df_rom.columns:
            mask_reg = (df_rom['PRODUCTO'].astype(str).str.upper() == prod_sel) & (df_rom['FECHA'] == fecha_sel)
            df_reg_sel = df_rom[mask_reg]
            reg1 = df_reg_sel['REGULACION 1'].sum() if 'REGULACION 1' in df_reg_sel.columns else 0
            reg2 = df_reg_sel['REGULACION 2'].sum() if 'REGULACION 2' in df_reg_sel.columns else 0
            reg3 = df_reg_sel['REGULACION 3'].sum() if 'REGULACION 3' in df_reg_sel.columns else 0

        # --- 5. DASHBOARD VISUAL ---
        st.header(f"Reporte: {prod_sel}")
        st.info(f"📅 Fecha analizada: {fecha_sel}")

        t_prog, t_real = df_p['Ton_Prog'].sum(), df_p['Ton_Real'].sum()
        cump_dia = (t_real / t_prog * 100) if t_prog > 0 else 0
        eq_prog, eq_real = df_p['Eq_Prog'].sum(), df_p['Eq_Real'].sum()
        total_reg = reg1 + reg2 + reg3

        # Tarjetas
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Cumplimiento Día", f"{cump_dia:.1f}%")
        m2.metric("Equipos Programados", f"{eq_prog:.0f}")
        m3.metric("Equipos Reales", f"{eq_real:.0f}")
        m4.metric("Regulaciones (Equipos)", f"{total_reg:.0f}", delta_color="inverse")

        # Gráficos
        g1, g2 = st.columns(2)
        with g1:
            fig_ton = go.Figure(data=[
                go.Bar(name='Programado', x=['Tonelaje'], y=[t_prog], marker_color='#A8D5BA', text=[f"{t_prog:,.0f}"], textposition='auto'),
                go.Bar(name='Real', x=['Tonelaje'], y=[t_real], marker_color='#2E7D32', text=[f"{t_real:,.0f}"], textposition='auto')
            ])
            fig_ton.update_layout(title="Comparativa Tonelaje", barmode='group')
            st.plotly_chart(fig_ton, use_container_width=True)

        with g2:
            fig_eq = go.Figure(data=[
                go.Bar(name='Programado', x=['Equipos'], y=[eq_prog], marker_color='#BDD7EE', text=[f"{eq_prog:.0f}"], textposition='auto'),
                go.Bar(name='Real', x=['Equipos'], y=[eq_real], marker_color='#2F5597', text=[f"{eq_real:.0f}"], textposition='auto')
            ])
            fig_eq.update_layout(title="Comparativa Equipos", barmode='group')
            st.plotly_chart(fig_eq, use_container_width=True)

        # Seccion Regulaciones
        if total_reg > 0:
            st.warning(f"🚨 Regulaciones detectadas")
            r1, r2, r3 = st.columns(3)
            r1.metric("Regulación 1", f"{reg1:.0f}")
            r2.metric("Regulación 2", f"{reg2:.0f}")
            r3.metric("Regulación 3", f"{reg3:.0f}")

        # IA Analyst
        st.divider()
        if st.button("🚀 Generar Informe con IA"):
            api_k = st.secrets.get("GEMINI_API_KEY")
            if api_k:
                with st.spinner("Analizando..."):
                    prompt = f"Producto: {prod_sel}, Fecha: {fecha_sel}. Cumplimiento: {cump_dia:.1f}%. Regulaciones: {total_reg}. Analiza brevemente el desempeño."
                    res, _ = call_gemini_api(prompt, api_k)
                    st.write(res)
            else:
                st.warning("API Key no encontrada.")

    except Exception as e:
        st.error(f"Error de procesamiento: {str(e)}")
else:
    st.info("👋 Cargue los archivos para iniciar.")
