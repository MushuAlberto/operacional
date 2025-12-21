import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Dashboard Operacional - Histórico Romanas", layout="wide")

# Configuración de IA (Gemini) desde Secrets
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
else:
    st.error("⚠️ Configura la GEMINI_API_KEY en los Secrets de Streamlit.")

# --- ESTILOS PERSONALIZADOS ---
st.markdown("""
    <style>
    .metric-container { background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 5px solid #558b2f; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Control de Gestión: Histórico de Romanas")
st.markdown("---")

# --- CARGA DE DATOS ---
uploaded_file = st.file_uploader("Sube el archivo '02.- Histórico Romanas'", type=["xlsx", "csv"])

if uploaded_file:
    # Leer el archivo (usando los nombres de columnas reales)
    if uploaded_file.name.endswith('.xlsx'):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file)

    # Limpieza básica: Asegurar que Fecha sea datetime y Tonelaje numérico
    df['FECHA'] = pd.to_datetime(df['FECHA'])
    df['TONELAJE'] = pd.to_numeric(df['TONELAJE'], errors='coerce')

    # --- FILTROS LATERALES ---
    st.sidebar.header("Filtros del Reporte")
    fecha_sel = st.sidebar.date_input("Selecciona Fecha", df['FECHA'].max())
    productos = st.sidebar.multiselect("Filtrar por Producto", df['PRODUCTO'].unique(), default=df['PRODUCTO'].unique())
    
    # Aplicar filtros
    df_filtrado = df[(df['FECHA'].dt.date == fecha_sel) & (df['PRODUCTO'].isin(productos))]

    if not df_filtrado.empty:
        # --- BLOQUE 1: KPIs MAESTROS ---
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Tonelaje Total Despachado", f"{df_filtrado['TONELAJE'].sum():,.2f} Ton")
        with c2:
            st.metric("Total Viajes (Registros)", len(df_filtrado))
        with c3:
            st.metric("Promedio Ton por Viaje", f"{df_filtrado['TONELAJE'].mean():,.2f} Ton")

        st.markdown("---")

        # --- BLOQUE 2: GRÁFICOS PARA GERENCIA ---
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("🚛 Tonelaje por Empresa de Transporte")
            fig_empresa = px.bar(df_filtrado.groupby('EMPRESA DE TRANSPORTE')['TONELAJE'].sum().reset_index(), 
                                 x='EMPRESA DE TRANSPORTE', y='TONELAJE',
                                 color_discrete_sequence=['#2E7D32'])
            st.plotly_chart(fig_empresa, use_container_width=True)

        with col_right:
            st.subheader("📦 Distribución por Producto")
            fig_prod = px.pie(df_filtrado, values='TONELAJE', names='PRODUCTO', 
                              hole=0.4, color_discrete_sequence=px.colors.sequential.Greens_r)
            st.plotly_chart(fig_prod, use_container_width=True)

        # --- BLOQUE 3: ANÁLISIS DE IA ---
        st.markdown("---")
        st.subheader("🤖 Resumen Analítico de la Jornada")
        if st.button("Generar Informe Ejecutivo"):
            with st.spinner("La IA está analizando los datos..."):
                resumen_datos = df_filtrado[['PRODUCTO', 'DESTINO', 'TONELAJE', 'EMPRESA DE TRANSPORTE']].head(20).to_string()
                prompt = f"""
                Analiza como un experto logístico estos datos de transporte: {resumen_datos}. 
                Indica qué empresa de transporte movió más carga, qué destino es el principal y 
                genera una conclusión sobre la eficiencia del día {fecha_sel}.
                """
                response = model.generate_content(prompt)
                st.info(response.text)

        # --- BLOQUE 4: TABLA DETALLADA ---
        with st.expander("🔍 Ver registros detallados"):
            st.dataframe(df_filtrado[['FECHA', 'PRODUCTO', 'DESTINO', 'TONELAJE', 'EMPRESA DE TRANSPORTE']])

    else:
        st.warning("No hay datos para la fecha y productos seleccionados.")

else:
    st.info("Esperando carga del archivo '02.- Histórico Romanas'...")