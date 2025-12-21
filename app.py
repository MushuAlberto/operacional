import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard Operacional SQM", layout="wide", page_icon="📊")

def call_gemini_api(prompt, api_key, model="gemini-1.5-flash"):
    # Uso de v1beta para resolver el error 404 de modelos 1.5
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

# --- 2. CARGA DE ARCHIVO ---
st.title("🚀 Panel de Control SQM - Cumplimiento y Regulaciones")
st.markdown("---")

file_tablero = st.file_uploader("📁 Cargar 03.- Tablero Despachos (XLSM)", type=["xlsm"])

if file_tablero:
    try:
        # --- PROCESAMIENTO COLUMNAS ESPECÍFICAS ---
        # B=1 (Fecha), AF=31 (Prod), AH=33 (Ton Prog), AI=34 (Ton Real), 
        # AJ=35 (Eq Prog), AK=36 (Eq Real), AL=37 (% Cump), AU=46 (% Reg Real)
        cols_idx = [1, 31, 33, 34, 35, 36, 37, 46]
        df = pd.read_excel(file_tablero, sheet_name="Base de Datos", usecols=cols_idx, engine='openpyxl')
        
        # Renombrar para claridad
        df.columns = ['Fecha', 'Producto', 'Ton_Prog', 'Ton_Real', 'Eq_Prog', 'Eq_Real', 'Cumplimiento', 'Regulacion_Real']
        
        # Limpieza de Fechas (Solución al error "time data doesn't match format")
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce').dt.date
        df = df.dropna(subset=['Fecha', 'Producto'])
        df['Producto'] = df['Producto'].astype(str).str.strip().str.upper()

        # --- 3. FILTROS ---
        st.sidebar.header("🔍 Filtros de Consulta")
        fechas_disp = sorted(df['Fecha'].unique(), reverse=True)
        fecha_sel = st.sidebar.selectbox("Seleccione la Fecha", fechas_disp)
        
        df_fecha = df[df['Fecha'] == fecha_sel]
        productos_disp = sorted(df_fecha['Producto'].unique())
        prod_sel = st.sidebar.selectbox("Seleccione el Producto", productos_disp)
        
        # Datos finales filtrados
        df_p = df_fecha[df_fecha['Producto'] == prod_sel]

        # --- 4. KPIs Y TARJETAS ---
        t_prog, t_real = df_p['Ton_Prog'].sum(), df_p['Ton_Real'].sum()
        cump_dia = (t_real / t_prog * 100) if t_prog > 0 else 0
        eq_prog, eq_real = df_p['Eq_Prog'].sum(), df_p['Eq_Real'].sum()
        # Promedio de regulación del producto en el día
        reg_promedio = df_p['Regulacion_Real'].mean() * 100 

        st.header(f"Producto: {prod_sel}")
        st.info(f"📅 Reporte del día {fecha_sel}")

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Cumplimiento Diario", f"{cump_dia:.1f}%", delta=f"{cump_dia-100:.1f}%")
        with m2:
            st.metric("Equipos (Real vs Prog)", f"{eq_real:.0f} / {eq_prog:.0f}")
        with m3:
            # Tarjeta de Regulación solicitada (Columna AU)
            st.metric("% Regulación Real", f"{reg_promedio:.1f}%", delta_color="inverse")

        # --- 5. GRÁFICOS ---
        g1, g2 = st.columns(2)
        with g1:
            fig_ton = go.Figure(data=[
                go.Bar(name='Prog', x=['Tonelaje'], y=[t_prog], marker_color='#A8D5BA', text=[f"{t_prog:,.0f}"]),
                go.Bar(name='Real', x=['Tonelaje'], y=[t_real], marker_color='#2E7D32', text=[f"{t_real:,.0f}"])
            ])
            fig_ton.update_layout(title="Comparativa Toneladas", barmode='group')
            st.plotly_chart(fig_ton, use_container_width=True)

        with g2:
            fig_eq = go.Figure(data=[
                go.Bar(name='Prog', x=['Equipos'], y=[eq_prog], marker_color='#BDD7EE', text=[f"{eq_prog:.0f}"]),
                go.Bar(name='Real', x=['Equipos'], y=[eq_real], marker_color='#2F5597', text=[f"{eq_real:.0f}"])
            ])
            fig_eq.update_layout(title="Comparativa Equipos", barmode='group')
            st.plotly_chart(fig_eq, use_container_width=True)

        # --- 6. ANÁLISIS IA ---
        st.divider()
        if st.button("🚀 Analizar con IA"):
            api_k = st.secrets.get("GEMINI_API_KEY")
            if api_k:
                with st.spinner("Generando diagnóstico..."):
                    prompt = f"Análisis SQM: {prod_sel} el {fecha_sel}. Cumplimiento {cump_dia:.1f}%, Regulación {reg_promedio:.1f}%. Diagnostica la operación."
                    res, _ = call_gemini_api(prompt, api_k)
                    st.markdown(f"**Análisis:** {res}")
            else:
                st.warning("Verifica la API Key en los Secrets.")

    except Exception as e:
        st.error(f"Error de procesamiento: {str(e)}")
else:
    st.info("👋 Por favor, carga el archivo '03.- Tablero Despachos' para visualizar los datos.")
