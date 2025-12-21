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
    st.warning("⚠️ IA Desactivada: Configura GEMINI_API_KEY en los Secrets de Streamlit.")

# --- 3. DICCIONARIO DE ESTANDARIZACIÓN DE EMPRESAS ---
MAPE_EMPRESAS = {
    "JORQUERA TRANSPORTE S A": "JORQUERA TRANSPORTE S. A.",
    "MINING SERVICES AND DERIVATES": "M S & D SPA",
    "MINING SERVICES AND DERIVATES SPA": "M S & D SPA",
    "M S AND D": "M S & D SPA",
    "M S AND D SPA": "M S & D SPA",
    "MSANDD SPA": "M S & D SPA",
    "M S D": "M S & D SPA",
    "M S D SPA": "M S & D SPA",
    "M S & D": "M S & D SPA",
    "M S & D SPA": "M S & D SPA",
    "MS&D SPA": "M S & D SPA",
    "M AND Q SPA": "M&Q SPA",
    "M AND Q": "M&Q SPA",
    "M Q SPA": "M&Q SPA",
    "MQ SPA": "M&Q SPA",
    "M&Q SPA": "M&Q SPA",
    "MANDQ SPA": "M&Q SPA",
    "MINING AND QUARRYING SPA": "M&Q SPA",
    "MINING AND QUARRYNG SPA": "M&Q SPA",
    "AG SERVICE SPA": "AG SERVICES SPA",
    "AG SERVICES SPA": "AG SERVICES SPA",
    "COSEDUCAM S A": "COSEDUCAM S A"
}

# --- 4. ENCABEZADO ---
st.title("📊 Control de Gestión: Histórico de Romanas")
st.markdown("### Reporte Operacional de Despacho de Litio")
st.divider()

# --- 5. CARGA Y LIMPIEZA DE DATOS ---
uploaded_file = st.file_uploader("Subir archivo: 02.- Histórico Romanas", type=["xlsx", "csv"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)

        # Limpieza de nombres de columnas
        df.columns = df.columns.str.strip()

        # Conversión de Fechas
        df['FECHA'] = pd.to_datetime(df['FECHA'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['FECHA'])
        
        # Conversión de Tonelaje
        df['TONELAJE'] = pd.to_numeric(df['TONELAJE'], errors='coerce').fillna(0)

        # --- ESTANDARIZACIÓN DE EMPRESAS ---
        # Pasamos a mayúsculas y quitamos espacios extra para asegurar el cruce
        df['EMPRESA DE TRANSPORTE'] = df['EMPRESA DE TRANSPORTE'].astype(str).str.strip().str.upper()
        # Aplicamos el mapeo. Si el nombre no está en el diccionario, se queda como está.
        df['EMPRESA DE TRANSPORTE'] = df['EMPRESA DE TRANSPORTE'].replace(MAPE_EMPRESAS)

        # --- 6. FILTROS LATERALES ---
        st.sidebar.header("⚙️ Panel de Filtros")
        max_date = df['FECHA'].max().date()
        fecha_sel = st.sidebar.date_input("Seleccionar Fecha", max_date)
        
        lista_productos = sorted(df['PRODUCTO'].unique())
        productos_sel = st.sidebar.multiselect("Filtrar Productos", lista_productos, default=lista_productos)

        mask = (df['FECHA'].dt.date == fecha_sel) & (df['PRODUCTO'].isin(productos_sel))
        df_view = df.loc[mask]

        if not df_view.empty:
            # --- 7. DASHBOARD EJECUTIVO ---
            ton_total = df_view['TONELAJE'].sum()
            total_viajes = len(df_view)
            prom_ton = df_view['TONELAJE'].mean()

            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("Tonelaje Total", f"{ton_total:,.2f} Ton")
            kpi2.metric("Total de Viajes", f"{total_viajes}")
            kpi3.metric("Promedio Carga", f"{prom_ton:,.2f} Ton/v")

            st.markdown("---")

            # --- 8. VISUALIZACIONES ---
            col_a, col_b = st.columns(2)

            with col_a:
                st.subheader("🚛 Tonelaje por Empresa (Estandarizado)")
                # Agrupamos por los nombres ya limpios
                resumen_empresa = df_view.groupby('EMPRESA DE TRANSPORTE')['TONELAJE'].sum().reset_index()
                resumen_empresa = resumen_empresa.sort_values(by='TONELAJE', ascending=False)
                
                fig_emp = px.bar(
                    resumen_empresa,
                    x='EMPRESA DE TRANSPORTE', y='TONELAJE',
                    color='TONELAJE',
                    color_continuous_scale='Greens',
                    labels={'TONELAJE': 'Ton Totales'}
                )
                st.plotly_chart(fig_emp, use_container_width=True)

            with col_b:
                st.subheader("📍 Destinos")
                fig_dest = px.pie(df_view, values='TONELAJE', names='DESTINO', hole=0.4)
                st.plotly_chart(fig_dest, use_container_width=True)

            # --- 9. ANÁLISIS ESTRATÉGICO CON IA ---
            st.markdown("---")
            if st.button("Generar Informe Ejecutivo con IA"):
                with st.spinner("Analizando datos..."):
                    # Enviamos datos ya agrupados para que la IA sea más precisa
                    resumen_ia = resumen_empresa.to_string()
                    prompt = f"Analiza estos datos de transporte: {resumen_ia}. Resume el desempeño de las empresas y detecta la principal transportista hoy."
                    response = model.generate_content(prompt)
                    st.info(response.text)

            # --- 10. DETALLE ---
            with st.expander("🔍 Ver registros detallados"):
                st.dataframe(df_view[['FECHA', 'PRODUCTO', 'DESTINO', 'TONELAJE', 'EMPRESA DE TRANSPORTE']], use_container_width=True)
        
        else:
            st.warning("No hay datos para esta selección.")

    except Exception as e:
        st.error(f"Error: {e}")

else:
    st.info("👋 Sube el archivo '02.- Histórico Romanas' para comenzar.")
