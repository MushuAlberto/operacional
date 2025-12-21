import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Reporte Operacional SQM", layout="wide")

# Inicialización segura de la IA
if "GEMINI_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # Intentamos con el modelo más estable y universal
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"Error de configuración de IA: {e}")
else:
    st.warning("⚠️ Falta la API Key en los Secrets de Streamlit.")

st.title("📊 Análisis de Despacho por Producto")
st.divider()

# --- 2. CARGA DE DATOS ---
uploaded_file = st.file_uploader("Subir archivo Excel (02.- Histórico Romanas)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip() 
        
        # Limpieza de Fechas y Tonelaje
        df['FECHA'] = pd.to_datetime(df['FECHA'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['FECHA'])
        df['TONELAJE'] = pd.to_numeric(df['TONELAJE'], errors='coerce').fillna(0)
        df['PRODUCTO'] = df['PRODUCTO'].astype(str).str.strip().str.upper()

        # --- 3. FILTROS ---
        st.sidebar.header("⚙️ Filtros")
        ultima_fecha = df['FECHA'].max().date()
        fecha_sel = st.sidebar.date_input("Fecha de consulta", ultima_fecha)
        
        lista_productos = sorted(df['PRODUCTO'].unique())
        productos_sel = st.sidebar.multiselect("Filtrar Productos", lista_productos, default=lista_productos)

        mask = (df['FECHA'].dt.date == fecha_sel) & (df['PRODUCTO'].isin(productos_sel))
        df_view = df.loc[mask]

        if not df_view.empty:
            # --- 4. KPIs ---
            c1, c2, c3 = st.columns(3)
            total_ton = df_view['TONELAJE'].sum()
            c1.metric("Tonelaje Total", f"{total_ton:,.2f} Ton")
            c2.metric("N° de Viajes", f"{len(df_view)}")
            c3.metric("Variedad", f"{df_view['PRODUCTO'].nunique()} Productos")

            # --- 5. GRÁFICO ---
            st.subheader(f"🚛 Distribución por Producto ({fecha_sel})")
            df_prod = df_view.groupby('PRODUCTO')['TONELAJE'].sum().reset_index().sort_values('TONELAJE', ascending=False)

            fig = px.bar(
                df_prod, x='PRODUCTO', y='TONELAJE',
                color='TONELAJE', text_auto='.2s',
                color_continuous_scale='Greens'
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- 6. IA (REPARADA) ---
            if st.button("🤖 Analizar con IA"):
                try:
                    with st.spinner("Procesando análisis..."):
                        resumen = df_prod.to_string(index=False)
                        prompt = f"Analiza estos datos de carga por producto: {resumen}. Resume el impacto operativo brevemente."
                        # Llamada directa para evitar errores de versión
                        response = model.generate_content(prompt)
                        st.info(response.text)
                except Exception as ia_err:
                    st.error("La IA no pudo responder. Esto suele ser por una API Key inválida o restricciones de región.")
                    st.expander("Detalle del error").write(str(ia_err))

            # --- 7. TABLA ---
            with st.expander("🔍 Ver registros del día"):
                st.dataframe(df_view[['FECHA', 'PRODUCTO', 'DESTINO', 'TONELAJE', 'EMPRESA DE TRANSPORTE']])

        else:
            st.warning("No hay datos para la fecha seleccionada.")
            
    except Exception as e:
        st.error(f"Error al procesar el Excel: {e}")
else:
    st.info("👋 Sube el archivo para comenzar.")
