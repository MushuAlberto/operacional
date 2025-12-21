import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Dashboard Ejecutivo SQM",
    page_icon="📊",
    layout="wide"
)

# --- 2. CONFIGURACIÓN DE IA (SECRETS) ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
else:
    st.warning("⚠️ IA Desactivada: Configura GEMINI_API_KEY en los Secrets.")

# --- 3. DICCIONARIO DE ESTANDARIZACIÓN ACTUALIZADO ---
# Se han aplicado exactamente las reglas de nombre solicitadas
MAPE_EMPRESAS = {
    # Grupo M&Q SPA
    "M AND Q SPA": "M&Q SPA",
    "M AND Q": "M&Q SPA",
    "M Q SPA": "M&Q SPA",
    "MQ SPA": "M&Q SPA",
    "M&Q SPA": "M&Q SPA",
    "MANDQ SPA": "M&Q SPA",
    "MINING AND QUARRYING SPA": "M&Q SPA",
    "MINING AND QUARRYNG SPA": "M&Q SPA",
    
    # Grupo M S & D SPA
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
    
    # Otros
    "JORQUERA TRANSPORTE S A": "JORQUERA TRANSPORTE S. A.",
    "AG SERVICE SPA": "AG SERVICES SPA",
    "AG SERVICES SPA": "AG SERVICES SPA",
    "COSEDUCAM S A": "COSEDUCAM S A"
}

# --- 4. ENCABEZADO ---
st.title("📊 Control de Gestión: Histórico de Romanas")
st.markdown("### Reporte Operacional de Despacho")
st.divider()

# --- 5. CARGA Y LIMPIEZA DE DATOS ---
uploaded_file = st.file_uploader("Subir archivo: 02.- Histórico Romanas", type=["xlsx", "csv"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        
        # Limpieza de columnas y formatos
        df.columns = df.columns.str.strip()
        df['FECHA'] = pd.to_datetime(df['FECHA'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['FECHA'])
        df['TONELAJE'] = pd.to_numeric(df['TONELAJE'], errors='coerce').fillna(0)

        # --- PROCESO DE LIMPIEZA DE EMPRESAS ---
        # Convertimos a mayúsculas y quitamos espacios para asegurar el match con el diccionario
        df['EMPRESA DE TRANSPORTE'] = df['EMPRESA DE TRANSPORTE'].astype(str).str.strip().str.upper()
        df['EMPRESA DE TRANSPORTE'] = df['EMPRESA DE TRANSPORTE'].replace(MAPE_EMPRESAS)

        # --- 6. FILTROS ---
        st.sidebar.header("⚙️ Filtros")
        max_date = df['FECHA'].max().date()
        fecha_sel = st.sidebar.date_input("Fecha", max_date)
        
        lista_prod = sorted(df['PRODUCTO'].unique())
        prod_sel = st.sidebar.multiselect("Productos", lista_prod, default=lista_prod)

        mask = (df['FECHA'].dt.date == fecha_sel) & (df['PRODUCTO'].isin(prod_sel))
        df_view = df.loc[mask]

        if not df_view.empty:
            # --- 7. KPIs ---
            c1, c2, c3 = st.columns(3)
            c1.metric("Tonelaje Total", f"{df_view['TONELAJE'].sum():,.2f} Ton")
            c2.metric("Total Viajes", f"{len(df_view)}")
            c3.metric("Promedio Carga", f"{df_view['TONELAJE'].mean():,.2f} Ton/v")

            st.markdown("---")

            # --- 8. GRÁFICO DE EMPRESAS ---
            st.subheader("🚛 Desempeño por Empresa (Nombres Estandarizados)")
            
            df_grouped = df_view.groupby('EMPRESA DE TRANSPORTE')['TONELAJE'].sum().reset_index()
            df_grouped = df_grouped.sort_values(by='TONELAJE', ascending=False)

            fig_emp = px.bar(
                df_grouped,
                x='EMPRESA DE TRANSPORTE', 
                y='TONELAJE',
                text_auto='.2s',
                color='TONELAJE',
                color_continuous_scale='Greens',
                labels={'TONELAJE': 'Tonelaje Total', 'EMPRESA DE TRANSPORTE': 'Empresa'}
            )
            
            fig_emp.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_emp, use_container_width=True)

            # --- 9. IA ---
            if st.button("🤖 Generar Resumen Analítico"):
                with st.spinner("Analizando..."):
                    resumen = df_grouped.to_string(index=False)
                    prompt = f"Analiza estos datos de transporte: {resumen}. Resume el desempeño de las empresas hoy."
                    response = model.generate_content(prompt)
                    st.info(response.text)

            with st.expander("🔍 Ver registros detallados"):
                st.dataframe(df_view)
        else:
            st.warning("No hay datos para esta selección.")
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("👋 Sube el archivo para comenzar.")
