import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard Operacional - Productos", layout="wide")

# CONFIGURACIÓN DE IA ACTUALIZADA
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # Cambiamos 'gemini-pro' por 'gemini-1.5-flash' para evitar el error 404
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.warning("⚠️ IA Desactivada: Configura GEMINI_API_KEY en los Secrets de Streamlit.")

st.title("📊 Control de Gestión: Análisis por Producto")
st.markdown("### Resumen de Tonelaje Despachado")
st.divider()

# --- 2. CARGA DE DATOS ---
uploaded_file = st.file_uploader("Subir archivo Excel (02.- Histórico Romanas)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip() 
        
        # Convertir Fecha y Tonelaje con manejo de errores
        df['FECHA'] = pd.to_datetime(df['FECHA'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['FECHA'])
        df['TONELAJE'] = pd.to_numeric(df['TONELAJE'], errors='coerce').fillna(0)
        
        # Limpieza simple de la columna Producto
        df['PRODUCTO'] = df['PRODUCTO'].astype(str).str.strip().str.upper()

        # --- 3. FILTROS ---
        st.sidebar.header("⚙️ Filtros")
        max_date = df['FECHA'].max().date()
        fecha_sel = st.sidebar.date_input("Seleccionar Fecha", max_date)
        
        lista_productos = sorted(df['PRODUCTO'].unique())
        productos_sel = st.sidebar.multiselect("Filtrar Productos", lista_productos, default=lista_productos)

        mask = (df['FECHA'].dt.date == fecha_sel) & (df['PRODUCTO'].isin(productos_sel))
        df_view = df.loc[mask]

        if not df_view.empty:
            # --- 4. KPIs PRINCIPALES ---
            c1, c2, c3 = st.columns(3)
            c1.metric("Tonelaje Total", f"{df_view['TONELAJE'].sum():,.2f} Ton")
            c2.metric("Total Viajes", len(df_view))
            c3.metric("Productos Distintos", df_view['PRODUCTO'].nunique())

            st.divider()

            # --- 5. GRÁFICO POR PRODUCTO ---
            st.subheader(f"🚛 Distribución de Tonelaje por Producto ({fecha_sel})")
            
            df_prod = df_view.groupby('PRODUCTO')['TONELAJE'].sum().reset_index()
            df_prod = df_prod.sort_values(by='TONELAJE', ascending=False)

            fig = px.bar(
                df_prod, 
                x='PRODUCTO', 
                y='TONELAJE',
                color='TONELAJE',
                text_auto='.2s',
                color_continuous_scale='Greens',
                labels={'TONELAJE': 'Tonelaje Total', 'PRODUCTO': 'Tipo de Producto'}
            )
            
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

            # --- 6. ANÁLISIS DE IA CORREGIDO ---
            if st.button("🤖 Analizar Tendencia de Productos"):
                try:
                    with st.spinner("La IA está analizando los volúmenes con Gemini 1.5 Flash..."):
                        # Convertimos los datos a un formato que la IA entienda bien
                        datos_para_ia = df_prod.to_dict(orient='records')
                        prompt = f"""
                        Como experto en logística, analiza los siguientes datos de despacho de productos para la fecha {fecha_sel}:
                        {datos_para_ia}
                        
                        Por favor indica:
                        1. Cuál es el producto con mayor movimiento.
                        2. Un breve análisis de la distribución del tonelaje.
                        3. Una recomendación operativa basada en estos volúmenes.
                        """
                        response = model.generate_content(prompt)
                        st.info(response.text)
                except Exception as ia_err:
                    st.error(f"Hubo un problema con la IA: {ia_err}")

            # --- 7. TABLA DE DETALLES ---
            with st.expander("🔍 Ver registros detallados"):
                st.dataframe(df_view[['FECHA', 'PRODUCTO', 'DESTINO', 'TONELAJE', 'EMPRESA DE TRANSPORTE']])

        else:
            st.warning(f"No hay datos para el día {fecha_sel}.")
            
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("👋 Sube el archivo Excel para comenzar el análisis por producto.")
