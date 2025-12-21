import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Dashboard Ejecutivo - Transporte de Litio",
    page_icon="📊",
    layout="wide"
)

# --- 2. CONFIGURACIÓN DE IA (SECRETS) ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
else:
    st.warning("⚠️ IA Desactivada: Configura GEMINI_API_KEY en los Secrets de Streamlit para habilitar el resumen analítico.")

# --- 3. ESTILOS VISUALES (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    div[data-testid="stExpander"] { background-color: #ffffff; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. ENCABEZADO ---
st.title("📊 Control de Gestión: Histórico de Romanas")
st.markdown("### Reporte Operacional de Despacho de Litio")
st.divider()

# --- 5. CARGA Y LIMPIEZA DE DATOS ---
uploaded_file = st.file_uploader("Subir archivo: 02.- Histórico Romanas (Excel o CSV)", type=["xlsx", "csv"])

if uploaded_file:
    try:
        # Carga según extensión
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)

        # Limpieza de nombres de columnas
        df.columns = df.columns.str.strip()

        # CONVERSIÓN DE DATOS (Solución al error anterior)
        # Forzamos formato día/mes/año y gestionamos errores con 'coerce'
        df['FECHA'] = pd.to_datetime(df['FECHA'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['FECHA']) # Eliminamos filas sin fecha válida
        
        # Aseguramos que Tonelaje sea número
        df['TONELAJE'] = pd.to_numeric(df['TONELAJE'], errors='coerce').fillna(0)

        # --- 6. FILTROS LATERALES ---
        st.sidebar.header("⚙️ Panel de Filtros")
        
        # Filtro de fecha
        min_date = df['FECHA'].min().date()
        max_date = df['FECHA'].max().date()
        fecha_sel = st.sidebar.date_input("Seleccionar Fecha", max_date, min_value=min_date, max_value=max_date)
        
        # Filtro de Producto
        lista_productos = sorted(df['PRODUCTO'].unique())
        productos_sel = st.sidebar.multiselect("Filtrar Productos", lista_productos, default=lista_productos)

        # Aplicación de filtros
        mask = (df['FECHA'].dt.date == fecha_sel) & (df['PRODUCTO'].isin(productos_sel))
        df_view = df.loc[mask]

        if not df_view.empty:
            # --- 7. DASHBOARD EJECUTIVO (KPIs) ---
            ton_total = df_view['TONELAJE'].sum()
            total_viajes = len(df_view)
            prom_ton = df_view['TONELAJE'].mean()

            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("Tonelaje Total", f"{ton_total:,.2f} Ton")
            kpi2.metric("Total de Viajes", f"{total_viajes} viajes")
            kpi3.metric("Promedio Carga", f"{prom_ton:,.2f} Ton/viaje")

            st.markdown("---")

            # --- 8. VISUALIZACIONES ---
            col_a, col_b = st.columns(2)

            with col_a:
                st.subheader("🚛 Desempeño por Empresa")
                fig_emp = px.bar(
                    df_view.groupby('EMPRESA DE TRANSPORTE')['TONELAJE'].sum().reset_index(),
                    x='EMPRESA DE TRANSPORTE', y='TONELAJE',
                    labels={'TONELAJE': 'Tonelaje Total', 'EMPRESA DE TRANSPORTE': 'Empresa'},
                    color_discrete_sequence=['#2E7D32']
                )
                st.plotly_chart(fig_emp, use_container_width=True)

            with col_b:
                st.subheader("📍 Destinos de Carga")
                fig_dest = px.pie(
                    df_view, values='TONELAJE', names='DESTINO',
                    hole=0.4,
                    color_discrete_sequence=px.colors.sequential.Greens_r
                )
                st.plotly_chart(fig_dest, use_container_width=True)

            # --- 9. ANÁLISIS ESTRATÉGICO CON IA ---
            st.markdown("---")
            st.subheader("🤖 Resumen Analítico (IA)")
            if st.button("Generar Informe Ejecutivo con IA"):
                if "GEMINI_API_KEY" in st.secrets:
                    with st.spinner("Analizando tendencias operativas..."):
                        # Resumen compacto para la IA
                        resumen_texto = df_view[['PRODUCTO', 'DESTINO', 'TONELAJE', 'EMPRESA DE TRANSPORTE']].to_string()
                        prompt = f"""
                        Actúa como un experto en logística minera. Analiza los siguientes datos de hoy:
                        {resumen_texto}
                        
                        Proporciona:
                        1. Una breve conclusión sobre la productividad.
                        2. Identifica si alguna empresa de transporte concentró la mayoría de la carga.
                        3. Una recomendación rápida para mejorar el flujo de despacho.
                        """
                        response = model.generate_content(prompt)
                        st.info(response.text)
                else:
                    st.error("No se encontró la clave de API en los Secrets.")

            # --- 10. DETALLE DE DATOS ---
            with st.expander("🔍 Ver registros detallados del día"):
                st.dataframe(df_view[['FECHA', 'PRODUCTO', 'DESTINO', 'TONELAJE', 'EMPRESA DE TRANSPORTE']], use_container_width=True)
        
        else:
            st.warning("No se encontraron datos para los filtros seleccionados.")

    except Exception as e:
        st.error(f"Error crítico al procesar el archivo: {e}")
        st.info("Asegúrate de que el archivo tenga las columnas: FECHA, PRODUCTO, DESTINO, TONELAJE y EMPRESA DE TRANSPORTE.")

else:
    st.info("👋 Por favor, sube el archivo '02.- Histórico Romanas' para visualizar el análisis.")
