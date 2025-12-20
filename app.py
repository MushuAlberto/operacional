import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# --- CONFIGURACIÓN DE LA APP ---
st.set_page_config(page_title="Dashboard Operativo SQM", layout="wide")

# Configuración de la IA (Gemini)
# Reemplaza 'TU_API_KEY' con tu clave real de Google AI Studio
# Configuración segura usando los Secrets de Streamlit
import streamlit as st

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Falta la configuración de la API Key en los Secrets de Streamlit.")
model = genai.GenerativeModel('gemini-pro')

# Estilo CSS para mejorar la estética
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    div.stButton > button { background-color: #558b2f; color: white; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- ENCABEZADO ---
st.title("📊 Control de Gestión: Transporte de Litio")
st.markdown("---")

uploaded_file = st.file_uploader("Sube el archivo de operaciones diario", type=["xlsx", "csv"])

if uploaded_file:
    # Carga de datos
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    
    # 1. KPIs MAESTROS (Lo que el gerente ve al abrir)
    cumplimiento_global = (df['Desp_Ton'].sum() / df['Prog_Ton'].sum()) * 100
    ton_totales = df['Desp_Ton'].sum()
    eficiencia_promedio = df['Promedio'].mean()

    c1, c2, c3 = st.columns(3)
    c1.metric("Cumplimiento Global", f"{cumplimiento_global:.1f}%", f"{cumplimiento_global-100:.1f}%")
    c2.metric("Total Despachado", f"{ton_totales:,.0f} Ton")
    c3.metric("Promedio Tonelaje/Viaje", f"{eficiencia_promedio:.2f} T")

    # 2. SECCIÓN VISUAL (Gráficos Interactivos)
    st.markdown("### 📈 Análisis de Cumplimiento por Área")
    col_chart, col_data = st.columns([2, 1])

    with col_chart:
        # Gráfico de barras comparativo
        fig = px.bar(df, x='Area', y=['Prog_Ton', 'Desp_Ton'], 
                     barmode='group', 
                     title="Programado vs. Despachado",
                     color_discrete_sequence=['#A5D6A7', '#2E7D32']) # Tonos de verde SQM
        st.plotly_chart(fig, use_container_width=True)

    with col_data:
        # Tabla resumen rápida
        st.write("**Alertas de Desviación:**")
        desviaciones = df[df['Cumplimiento'] < 90][['Area', 'Cumplimiento']]
        if not desviaciones.empty:
            st.warning(f"Hay {len(desviaciones)} áreas por debajo del 90% de cumplimiento.")
            st.table(desviaciones)
        else:
            st.success("Todas las áreas cumplen con el 90%+")

    # 3. ANÁLISIS ESTRATÉGICO CON IA
    st.markdown("---")
    st.subheader("🤖 Resumen Ejecutivo Inteligente")
    
    if st.button("Generar Informe con IA"):
        with st.spinner("Analizando datos operativos con Gemini..."):
            # Preparamos los datos para la IA
            data_summary = df[['Area', 'Producto', 'Cumplimiento', 'Tiempo_Int', 'Observaciones']].to_string()
            prompt = f"""
            Actúa como un Gerente de Operaciones Logísticas. 
            Analiza los siguientes datos de despacho de litio y redacta un resumen ejecutivo de 3 puntos:
            1. Cuál fue el desempeño general.
            2. Identifica el cuello de botella principal basado en los tiempos y observaciones.
            3. Da una recomendación estratégica para el turno de mañana.
            
            Datos: {data_summary}
            """
            
            response = model.generate_content(prompt)
            st.info(response.text)

    # 4. DETALLE OPERATIVO (Expandible para no saturar)
    with st.expander("🔍 Ver detalle operativo (Formato Tabla Original)"):
        st.dataframe(df.style.highlight_max(axis=0, subset=['Tiempo_Int'], color='#ffcdd2'))

else:
    st.info("👋 Bienvenido. Por favor sube el archivo de datos para comenzar el análisis.")