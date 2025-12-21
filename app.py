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
st.title("📊 Control de Despachos: Análisis por Día Seleccionado")
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
        
        # Limpieza de datos
        df_tab['Producto'] = df_tab['Producto'].astype(str).str.strip().str.upper()
        df_tab['Fecha'] = pd.to_datetime(df_tab['Fecha']).dt.date # Solo fecha sin hora

        # --- PROCESAMIENTO ROMANAS (02) ---
        df_rom = pd.read_excel(file_romanas, engine='openpyxl')
        df_rom.columns = df_rom.columns.str.strip().str.upper()
        if 'FECHA' in df_rom.columns:
            df_rom['FECHA'] = pd.to_datetime(df_rom['FECHA']).dt.date

        # --- 3. FILTROS EN BARRA LATERAL ---
        st.sidebar.header("🎯 Parámetros de Consulta")
        
        # Filtro de Fecha
        fechas_disponibles = sorted(df_tab['Fecha'].unique(), reverse=True)
        fecha_sel = st.sidebar.selectbox("Seleccione la Fecha", fechas_disponibles)
        
        # Filtro de Producto (solo productos que existan en esa fecha)
        df_fecha = df_tab[df_tab['Fecha'] == fecha_sel]
        productos_fecha = sorted(df_fecha['Producto'].unique())
        prod_sel = st.sidebar.selectbox("Seleccione el Producto", productos_fecha)
        
        # Filtrado final de datos para los gráficos
        df_p = df_fecha[df_fecha['Producto'] == prod_sel]

        # --- 4. LÓGICA DE REGULACIONES (Archivo 02) ---
        reg1, reg2, reg3 = 0, 0, 0
        if 'PRODUCTO' in df_rom.columns and 'FECHA' in df_rom.columns:
            mask_reg = (df_rom['PRODUCTO'].astype(str).str.upper() == prod_sel) & (df_rom['FECHA'] == fecha_sel)
            df_reg_sel = df_rom[mask_reg]
            reg1 = df_reg_sel['REGULACION 1'].sum() if 'REGULACION 1' in df_reg_sel.columns else 0
            reg2 = df_reg_sel['REGULACION 2'].sum() if 'REGULACION 2' in df_reg_sel.columns else 0
            reg3 = df_reg_sel['REGULACION 3'].sum() if 'REGULACION 3' in df_reg_sel.columns else 0

        # --- 5. CABECERA Y MÉTRICAS DEL DÍA ---
        st.header(f"Reporte: {prod_sel}")
        st.subheader(f"📅 Día seleccionado: {fecha_sel.strftime('%d/%m/%Y')}")

        t_prog, t_real = df_p['Ton_Prog'].sum(), df_p['Ton_Real'].sum()
        cump_dia = (t_real / t_prog * 100) if t_prog > 0 else 0
        eq_prog, eq_real = df_p['Eq_Prog'].sum(), df_p['Eq_Real'].sum()
        total_reg = reg1 + reg2 + reg3

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Cumplimiento Día", f"{cump_dia:.1f}%")
        m2.metric("Equipos Programados", f"{eq_prog:.0f}")
        m3.metric("Equipos Reales", f"{eq_real:.0f}")
        m4.metric("Regulaciones (Equipos)", f"{total_reg:.0f}", delta="En espera", delta_color="inverse")

        # --- 6. GRÁFICOS COMPARATIVOS ---
        g1, g2 = st.columns(2)

        with g1:
            fig_ton = go.Figure(data=[
                go.Bar(name='Programado', x=['Tonelaje'], y=[t_prog], marker_color='#A8D5BA', text=[f"{t_prog:,.0f}"], textposition='auto'),
                go.Bar(name='Real', x=['Tonelaje'], y=[t_real], marker_color='#2E7D32', text=[f"{t_real:,.0f}"], textposition='auto')
            ])
            fig_ton.update_layout(title=f"Comparativa Tonelaje - {fecha_sel}", barmode='group', height=400)
            st.plotly_chart(fig_ton, use_container_width=True)

        with g2:
            fig_eq = go.Figure(data=[
                go.Bar(name='Programado', x=['Equipos'], y=[eq_prog], marker_color='#BDD7EE', text=[f"{eq_prog:.0f}"], textposition='auto'),
                go.Bar(name='Real', x=['Equipos'], y=[eq_real], marker_color='#2F5597', text=[f"{eq_real:.0f}"], textposition='auto')
            ])
            fig_eq.update_layout(title=f"Comparativa Equipos - {fecha_sel}", barmode='group', height=400)
            st.plotly_chart(fig_eq, use_container_width=True)

        # --- 7. DETALLE DE REGULACIONES POR PRODUCTO/DÍA ---
        if total_reg > 0:
            st.warning(f"⚠️ Regulaciones detectadas para el día {fecha_sel}")
            r1, r2, r3 = st.columns(3)
            r1.info(f"**Regulación 1**\n\n {reg1:.0f} Equipos")
            r2.info(f"**Regulación 2**\n\n {reg2:.0f} Equipos")
            r3.info(f"**Regulación 3**\n\n {reg3:.0f} Equipos")
        else:
            st.success("✅ No se registraron equipos en regulación para este producto en la fecha seleccionada.")

        # --- 8. IA ANALYST ---
        st.divider()
        if st.button("🚀 Analizar desempeño del día con IA"):
            api_k = st.secrets.get("GEMINI_API_KEY")
            if api_k:
                with st.spinner("Analizando datos del día..."):
                    prompt = f"""
                    Analiza el desempeño de {prod_sel} para el día {fecha_sel}.
                    - Cumplimiento: {cump_dia:.1f}%.
                    - Brecha Equipos: {eq_prog - eq_real} camiones de diferencia.
                    - Regulaciones: {total_reg} equipos esperando.
                    Tarea: Proporciona un breve comentario sobre la eficiencia de este día y si las regulaciones fueron el factor crítico.
                    """
                    res, err = call_gemini_api(prompt, api_k)
                    st.markdown(f"### Análisis de la IA:\n{res}")
            else:
                st.warning("API Key no configurada.")

    except Exception as e:
        st.error(f"Error de procesamiento: {e}")
else:
    st.info("👋 Sube los archivos para comenzar el análisis por fecha.")
