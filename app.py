import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard SQM", layout="wide", page_icon="📊")

def call_gemini_api(prompt, api_key, model="gemini-1.5-flash"):
    # Uso de v1beta para evitar el error 404
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
st.title("📊 Panel de Control Operacional SQM")
st.markdown("---")

# Ahora solo pedimos un archivo
file_tablero = st.file_uploader("📁 Cargar archivo: 03.- Tablero Despachos - Informe Operacional 2025 (.xlsm)", type=["xlsm"])

if file_tablero:
    try:
        with st.spinner("Procesando Base de Datos..."):
            # Mapeo de columnas solicitado:
            # B=1 (Fecha), AF=31 (Prod), AH=33 (Ton Prog), AI=34 (Ton Real), 
            # AJ=35 (Eq Prog), AK=36 (Eq Real), AL=37 (% Cump), AU=46 (% Reg Real)
            cols_idx = [1, 31, 33, 34, 35, 36, 37, 46]
            df = pd.read_excel(file_tablero, sheet_name="Base de Datos", usecols=cols_idx, engine='openpyxl')
            
            # Renombrar columnas para el Dashboard
            df.columns = ['Fecha', 'Producto', 'Ton_Prog', 'Ton_Real', 'Eq_Prog', 'Eq_Real', 'Cumplimiento', 'Regulacion_Real']
            
            # Limpieza y corrección de fechas (dayfirst=True evita el error de formato)
            df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce').dt.date
            df = df.dropna(subset=['Fecha', 'Producto'])
            df['Producto'] = df['Producto'].astype(str).str.strip().str.upper()

        # --- 3. FILTROS LATERALES ---
        st.sidebar.header("🔍 Configuración del Reporte")
        
        # Selector de Fecha
        fechas_disp = sorted(df['Fecha'].unique(), reverse=True)
        fecha_sel = st.sidebar.selectbox("Seleccione la Fecha del Reporte", fechas_disp)
        
        # Selector de Producto (filtrado por la fecha elegida)
        df_fecha = df[df['Fecha'] == fecha_sel]
        productos_disp = sorted(df_fecha['Producto'].unique())
        prod_sel = st.sidebar.selectbox("Seleccione el Producto", productos_disp)
        
        # Datos finales del día y producto
        df_p = df_fecha[df_fecha['Producto'] == prod_sel]

        # --- 4. KPIs Y TARJETAS PRINCIPALES ---
        t_prog, t_real = df_p['Ton_Prog'].sum(), df_p['Ton_Real'].sum()
        cump_dia = (t_real / t_prog * 100) if t_prog > 0 else 0
        eq_prog, eq_real = df_p['Eq_Prog'].sum(), df_p['Eq_Real'].sum()
        # Dato de regulación de la columna AU
        reg_promedio = df_p['Regulacion_Real'].mean() * 100 

        st.header(f"Producto: {prod_sel}")
        st.subheader(f"📅 Informe del día: {fecha_sel.strftime('%d-%m-%Y')}")

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Cumplimiento Día", f"{cump_dia:.1f}%", delta=f"{cump_dia-100:.1f}% vs Meta")
        with m2:
            st.metric("Equipos (Real / Prog)", f"{eq_real:.0f} / {eq_prog:.0f}")
        with m3:
            # Tarjeta de Regulación basada en columna AU
            st.metric("% Regulación Real (AU)", f"{reg_promedio:.1f}%", delta_color="inverse")

        # --- 5. GRÁFICOS COMPARATIVOS ---
        col1, col2 = st.columns(2)
        
        with col1:
            fig_ton = go.Figure(data=[
                go.Bar(name='Programado', x=['Tonelaje'], y=[t_prog], marker_color='#A8D5BA', text=[f"{t_prog:,.0f}"]),
                go.Bar(name='Real', x=['Tonelaje'], y=[t_real], marker_color='#2E7D32', text=[f"{t_real:,.0f}"])
            ])
            fig_ton.update_layout(title="Comparativa de Toneladas", barmode='group', height=400)
            st.plotly_chart(fig_ton, use_container_width=True)

        with col2:
            fig_eq = go.Figure(data=[
                go.Bar(name='Programado', x=['Equipos'], y=[eq_prog], marker_color='#BDD7EE', text=[f"{eq_prog:.0f}"]),
                go.Bar(name='Real', x=['Equipos'], y=[eq_real], marker_color='#2F5597', text=[f"{eq_real:.0f}"])
            ])
            fig_eq.update_layout(title="Comparativa de Equipos", barmode='group', height=400)
            st.plotly_chart(fig_eq, use_container_width=True)

        # --- 6. ASISTENTE DE IA ---
        st.divider()
        if st.button("🚀 Generar Análisis Operacional"):
            api_k = st.secrets.get("GEMINI_API_KEY")
            if api_k:
                with st.spinner("Analizando brechas y regulaciones..."):
                    prompt = f"""
                    Analiza el desempeño operacional de {prod_sel} para el {fecha_sel}:
                    - Tonelaje: {t_real:,.0f} de {t_prog:,.0f} programadas ({cump_dia:.1f}% cumplimiento).
                    - Equipos: {eq_real} de {eq_prog} planificados.
                    - Regulación (Columna AU): {reg_promedio:.1f}%.
                    Tarea: Da un diagnóstico rápido sobre la eficiencia del despacho y el impacto de la regulación.
                    """
                    res, _ = call_gemini_api(prompt, api_k)
                    st.markdown(f"### 🤖 Diagnóstico de la IA:\n{res}")
            else:
                st.warning("⚠️ No se encontró la GEMINI_API_KEY en los Secrets.")

    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {str(e)}")
        st.info("Asegúrate de que el archivo tenga la pestaña 'Base de Datos' y las columnas en las posiciones correctas.")
else:
    st.info("👋 Bienvenido. Por favor, carga el archivo Excel (.xlsm) del Tablero de Despachos para comenzar.")
