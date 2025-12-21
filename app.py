import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard Operacional SQM", layout="wide", page_icon="📊")

def call_gemini_api(prompt, api_key, model="gemini-1.5-flash"):
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

# --- 2. CARGA DE ARCHIVO ÚNICO ---
st.title("🚀 Panel de Control SQM - Gestión por Destino")
st.markdown("---")

file_tablero = st.file_uploader("📁 Cargar archivo: 03.- Tablero Despachos (.xlsm)", type=["xlsm"])

if file_tablero:
    try:
        with st.spinner("Procesando Base de Datos..."):
            # Mapeo de columnas:
            # B=1 (Fecha), AF=31 (Prod), AG=32 (Destino), AH=33 (Ton Prog), 
            # AI=34 (Ton Real), AJ=35 (Eq Prog), AK=36 (Eq Real), AU=46 (% Reg Real)
            cols_idx = [1, 31, 32, 33, 34, 35, 36, 46]
            df = pd.read_excel(file_tablero, sheet_name="Base de Datos", usecols=cols_idx, engine='openpyxl')
            
            df.columns = ['Fecha', 'Producto', 'Destino', 'Ton_Prog', 'Ton_Real', 'Eq_Prog', 'Eq_Real', 'Regulacion_Real']
            
            # Corrección de Fechas (Solución al error "time data doesn't match format")
            df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce').dt.date
            df = df.dropna(subset=['Fecha', 'Producto'])
            df['Producto'] = df['Producto'].astype(str).str.strip().str.upper()
            df['Destino'] = df['Destino'].astype(str).str.strip()

        # --- 3. FILTROS ---
        fechas_disp = sorted(df['Fecha'].unique(), reverse=True)
        fecha_sel = st.sidebar.selectbox("📅 Seleccione la Fecha", fechas_disp)
        
        df_fecha = df[df['Fecha'] == fecha_sel]
        productos_disp = sorted(df_fecha['Producto'].unique())
        prod_sel = st.sidebar.selectbox("📦 Seleccione el Producto", productos_disp)
        
        df_p = df_fecha[df_fecha['Producto'] == prod_sel]

        # --- 4. KPIs Y TARJETAS (Cambio solicitado a Destino) ---
        t_prog, t_real = df_p['Ton_Prog'].sum(), df_p['Ton_Real'].sum()
        cump_dia = (t_real / t_prog * 100) if t_prog > 0 else 0
        reg_promedio = df_p['Regulacion_Real'].mean() * 100 
        
        # Obtener el destino (o destinos)
        destinos_lista = df_p['Destino'].unique()
        destino_display = destinos_lista[0] if len(destinos_lista) == 1 else "Múltiples"

        st.header(f"Producto: {prod_sel}")
        
        m1, m2, m3 = st.columns(3)
        with m1:
            # Nueva tarjeta de Destino solicitada (Columna AG)
            st.metric("📍 Destino Principal", destino_display)
        with m2:
            st.metric("Cumplimiento Día", f"{cump_dia:.1f}%")
        with m3:
            st.metric("% Regulación Real", f"{reg_promedio:.1f}%")

        # --- 5. GRÁFICOS ---
        col1, col2 = st.columns(2)
        with col1:
            fig_ton = go.Figure(data=[
                go.Bar(name='Prog', x=['Tonelaje'], y=[t_prog], marker_color='#A8D5BA', text=[f"{t_prog:,.0f}"]),
                go.Bar(name='Real', x=['Tonelaje'], y=[t_real], marker_color='#2E7D32', text=[f"{t_real:,.0f}"])
            ])
            fig_ton.update_layout(title="Comparativa Toneladas", barmode='group')
            st.plotly_chart(fig_ton, use_container_width=True)

        with col2:
            # Gráfico de equipos Real vs Prog
            eq_prog, eq_real = df_p['Eq_Prog'].sum(), df_p['Eq_Real'].sum()
            fig_eq = go.Figure(data=[
                go.Bar(name='Prog', x=['Equipos'], y=[eq_prog], marker_color='#BDD7EE', text=[f"{eq_prog:.0f}"]),
                go.Bar(name='Real', x=['Equipos'], y=[eq_real], marker_color='#2F5597', text=[f"{eq_real:.0f}"])
            ])
            fig_eq.update_layout(title="Comparativa Equipos", barmode='group')
            st.plotly_chart(fig_eq, use_container_width=True)

        # --- 6. DETALLE POR DESTINO ---
        if len(destinos_lista) > 1:
            with st.expander("🔍 Ver desglose por todos los destinos"):
                st.table(df_p[['Destino', 'Ton_Prog', 'Ton_Real', 'Eq_Real']])

        # --- 7. ANÁLISIS IA ---
        st.divider()
        if st.button("🚀 Generar Diagnóstico con IA"):
            api_k = st.secrets.get("GEMINI_API_KEY")
            if api_k:
                with st.spinner("Analizando..."):
                    prompt = f"Analiza {prod_sel} hacia {destinos_lista} el {fecha_sel}. Cumplimiento {cump_dia:.1f}%, Regulación {reg_promedio:.1f}%."
                    res, _ = call_gemini_api(prompt, api_k)
                    st.markdown(f"**Análisis:** {res}")
            else:
                st.warning("Configura la API Key en los Secrets.")

    except Exception as e:
        st.error(f"Error: {str(e)}")
else:
    st.info("👋 Cargue el archivo 03 para ver el reporte por Destino.")
