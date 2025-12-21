import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard SQM - Resumen Diario", layout="wide", page_icon="📊")

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

# --- 2. CARGA DE ARCHIVO ---
st.title("📊 Resumen de Despachos por Día")
st.markdown("---")

file_tablero = st.file_uploader("📁 Cargar archivo: 03.- Tablero Despachos (.xlsm)", type=["xlsm"])

if file_tablero:
    try:
        with st.spinner("Cargando base de datos..."):
            # B=1 (Fecha), AF=31 (Prod), AG=32 (Destino), AH=33 (Ton Prog), 
            # AI=34 (Ton Real), AJ=35 (Eq Prog), AK=36 (Eq Real), AU=46 (% Reg Real)
            cols_idx = [1, 31, 32, 33, 34, 35, 36, 46]
            df = pd.read_excel(file_tablero, sheet_name="Base de Datos", usecols=cols_idx, engine='openpyxl')
            
            df.columns = ['Fecha', 'Producto', 'Destino', 'Ton_Prog', 'Ton_Real', 'Eq_Prog', 'Eq_Real', 'Regulacion_Real']
            
            # Limpieza y corrección de fechas
            df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce').dt.date
            df = df.dropna(subset=['Fecha'])
            df['Producto'] = df['Producto'].astype(str).str.strip().str.upper()

        # --- 3. FILTRO DE FECHA ---
        st.sidebar.header("📅 Selección de Jornada")
        fechas_disp = sorted(df['Fecha'].unique(), reverse=True)
        fecha_sel = st.sidebar.selectbox("Seleccione la Fecha para ver todos los productos", fechas_disp)
        
        # Filtrar datos de toda la fecha seleccionada
        df_dia = df[df['Fecha'] == fecha_sel]

        # --- 4. KPIs GLOBALES DEL DÍA ---
        t_prog_total = df_dia['Ton_Prog'].sum()
        t_real_total = df_dia['Ton_Real'].sum()
        cump_total = (t_real_total / t_prog_total * 100) if t_prog_total > 0 else 0
        reg_total_promedio = df_dia['Regulacion_Real'].mean() * 100

        st.header(f"Resumen de Operaciones: {fecha_sel.strftime('%d-%m-%Y')}")
        
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Total Productos Despachados", len(df_dia['Producto'].unique()))
        with m2:
            st.metric("Cumplimiento Global", f"{cump_total:.1f}%")
        with m3:
            st.metric("Promedio Regulación (AU)", f"{reg_total_promedio:.1f}%")

        # --- 5. GRÁFICOS COMPARATIVOS (TODOS LOS PRODUCTOS) ---
        # Agrupamos por producto para el gráfico
        df_agrupado = df_dia.groupby('Producto').agg({
            'Ton_Prog': 'sum',
            'Ton_Real': 'sum',
            'Eq_Prog': 'sum',
            'Eq_Real': 'sum'
        }).reset_index()

        col1, col2 = st.columns(2)
        
        with col1:
            fig_ton = go.Figure()
            fig_ton.add_trace(go.Bar(x=df_agrupado['Producto'], y=df_agrupado['Ton_Prog'], name='Prog', marker_color='#A8D5BA'))
            fig_ton.add_trace(go.Bar(x=df_agrupado['Producto'], y=df_agrupado['Ton_Real'], name='Real', marker_color='#2E7D32'))
            fig_ton.update_layout(title="Toneladas por Producto", barmode='group', xaxis_tickangle=-45)
            st.plotly_chart(fig_ton, use_container_width=True)

        with col2:
            fig_eq = go.Figure()
            fig_eq.add_trace(go.Bar(x=df_agrupado['Producto'], y=df_agrupado['Eq_Prog'], name='Prog', marker_color='#BDD7EE'))
            fig_eq.add_trace(go.Bar(x=df_agrupado['Producto'], y=df_agrupado['Eq_Real'], name='Real', marker_color='#2F5597'))
            fig_eq.update_layout(title="Equipos por Producto", barmode='group', xaxis_tickangle=-45)
            st.plotly_chart(fig_eq, use_container_width=True)

        # --- 6. TABLA DETALLADA DE PRODUCTOS DEL DÍA ---
        st.subheader("📋 Detalle de Despachos")
        # Mostramos Destino, Toneladas y Equipos en una sola tabla
        st.dataframe(df_dia[['Producto', 'Destino', 'Ton_Prog', 'Ton_Real', 'Eq_Real', 'Regulacion_Real']], use_container_width=True)

        # --- 7. ANÁLISIS IA ---
        st.divider()
        if st.button("🚀 Analizar Desempeño General del Día"):
            api_k = st.secrets.get("GEMINI_API_KEY")
            if api_k:
                with st.spinner("Analizando todos los productos..."):
                    resumen_texto = df_agrupado.to_string()
                    prompt = f"Analiza el desempeño de estos productos del día {fecha_sel}: {resumen_texto}. ¿Hubo algún producto crítico?"
                    res, _ = call_gemini_api(prompt, api_k)
                    st.markdown(f"**Análisis de la Jornada:** {res}")
            else:
                st.warning("Configura la API Key.")

    except Exception as e:
        st.error(f"Error: {str(e)}")
else:
    st.info("👋 Seleccione el archivo 03 para ver el resumen de todos los productos del día.")
