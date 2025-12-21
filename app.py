import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Dashboard Operacional SQM", layout="wide")

# --- 2. CONFIGURACIÓN DE IA (SOLUCIÓN ERROR 404) ---
if "GEMINI_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # Usamos el nombre de modelo estándar más compatible
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
    except Exception as e:
        st.error(f"Error al configurar Gemini: {e}")
else:
    st.warning("⚠️ Falta GEMINI_API_KEY en los Secrets de Streamlit.")

st.title("📊 Control de Gestión: Análisis por Producto")
st.markdown("### Resumen de Tonelaje Despachado")
st.divider()

# --- 3. CARGA DE DATOS ---
uploaded_file = st.file_uploader("Subir archivo Excel (02.- Histórico Romanas)", type=["xlsx"])

if uploaded_file:
    try:
        # Carga del archivo
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip() 
        
        # Procesamiento de Fechas y Tonelaje
        df['FECHA'] = pd.to_datetime(df['FECHA'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['FECHA'])
        df['TONELAJE'] = pd.to_numeric(df['TONELAJE'], errors='coerce').fillna(0)
        
        # Estandarización de Producto (Solo limpieza básica)
        df['PRODUCTO'] = df['PRODUCTO'].astype(str).str.strip().str.upper()

        # --- 4. FILTROS ---
        st.sidebar.header("⚙️ Filtros")
        ultima_fecha = df['FECHA'].max().date()
        fecha_sel = st.sidebar.date_input("Seleccionar Fecha", ultima_fecha)
        
        lista_productos = sorted(df['PRODUCTO'].unique())
        productos_sel = st.sidebar.multiselect("Filtrar Productos", lista_productos, default=lista_productos)

        # Filtrado de datos
        mask = (df['FECHA'].dt.date == fecha_sel) & (df['PRODUCTO'].isin(productos_sel))
        df_view = df.loc[mask]

        if not df_view.empty:
            # --- 5. KPIs ---
            c1, c2, c3 = st.columns(3)
            c1.metric("Tonelaje Total", f"{df_view['TONELAJE'].sum():,.2f} Ton")
            c2.metric("Total Viajes", f"{len(df_view)}")
            c3.metric("Variedad Productos", f"{df_view['PRODUCTO'].nunique()}")

            st.divider()

            # --- 6. GRÁFICO POR PRODUCTO ---
            st.subheader(f"🚛 Distribución por Producto - {fecha_sel}")
            
            df_prod = df_view.groupby('PRODUCTO')['TONELAJE'].sum().reset_index()
            df_prod = df_prod.sort_values(by='TONELAJE', ascending=False)

            fig = px.bar(
                df_prod, 
                x='PRODUCTO', 
                y='TONELAJE',
                color='TONELAJE',
                text_auto='.3s',
                color_continuous_scale='Greens',
                labels={'TONELAJE': 'Tonelaje', 'PRODUCTO': 'Producto'}
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- 7. ANÁLISIS DE IA ---
            if st.button("🤖 Analizar Tendencia de Productos"):
                try:
                    with st.spinner("Analizando volúmenes operativos..."):
                        # Creamos un resumen simple para la IA
                        resumen_texto = "\n".join([f"- {row['PRODUCTO']}: {row['TONELAJE']:.2f} Ton" for _, row in df_prod.iterrows()])
                        
                        prompt = f"""
                        Analiza los siguientes datos de despacho del día {fecha_sel}:
                        {resumen_texto}
                        
                        Dime:
                        1. ¿Cuál es el producto principal?
                        2. ¿Qué porcentaje del total representa aproximadamente?
                        3. Una recomendación logística breve.
                        """
                        
                        response = model.generate_content(prompt)
                        st.info(response.text)
                except Exception as ia_err:
                    st.error("No se pudo conectar con el modelo de IA. Verifica tu API Key o intenta más tarde.")
                    st.debug(f"Detalle técnico: {ia_err}")

            # --- 8. DETALLE ---
            with st.expander("🔍 Ver registros detallados"):
                st.dataframe(df_view[['FECHA', 'PRODUCTO', 'DESTINO', 'TONELAJE', 'EMPRESA DE TRANSPORTE']])

        else:
            st.warning(f"No hay datos registrados para el {fecha_sel}.")
            
    except Exception as e:
        st.error(f"Error al procesar el Excel: {e}")
else:
    st.info("👋 Sube el archivo '02.- Histórico Romanas' para generar el reporte.")
