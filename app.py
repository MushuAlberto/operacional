import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard Operacional - Productos", layout="wide")

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')

st.title("📊 Control de Gestión: Análisis por Producto")
st.markdown("### Resumen de Tonelaje Despachado")
st.divider()

# --- 2. CARGA DE DATOS ---
uploaded_file = st.file_uploader("Subir archivo Excel (02.- Histórico Romanas)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip() # Limpiar espacios en nombres de columnas
        
        # Convertir Fecha y Tonelaje
        df['FECHA'] = pd.to_datetime(df['FECHA'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['FECHA'])
        df['TONELAJE'] = pd.to_numeric(df['TONELAJE'], errors='coerce').fillna(0)
        
        # Limpieza simple de la columna Producto
        df['PRODUCTO'] = df['PRODUCTO'].astype(str).str.strip().str.upper()

        # --- 3. FILTROS ---
        st.sidebar.header("⚙️ Filtros")
        fecha_sel = st.sidebar.date_input("Seleccionar Fecha", df['FECHA'].max().date())
        
        # Filtro de Producto para el usuario
        lista_productos = sorted(df['PRODUCTO'].unique())
        productos_sel = st.sidebar.multiselect("Filtrar Productos", lista_productos, default=lista_productos)

        # Aplicar filtros al DataFrame
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
            
            # Agrupar datos por Producto
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

            # --- 6. ANÁLISIS DE IA ---
            if st.button("🤖 Analizar Tendencia de Productos"):
                with st.spinner("La IA está analizando los volúmenes..."):
                    resumen_ia = df_prod.to_string(index=False)
                    prompt = f"Analiza estos datos de despacho por producto: {resumen_ia}. ¿Cuál es el producto dominante y qué sugiere esto para la operación del día {fecha_sel}?"
                    response = model.generate_content(prompt)
                    st.info(response.text)

            # --- 7. TABLA DE DETALLES ---
            with st.expander("🔍 Ver registros detallados"):
                st.dataframe(df_view[['FECHA', 'PRODUCTO', 'DESTINO', 'TONELAJE', 'EMPRESA DE TRANSPORTE']])

        else:
            st.warning(f"No se encontraron registros para el día {fecha_sel}.")
            
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("👋 Por favor, sube el archivo '02.- Histórico Romanas' para generar el gráfico por producto.")
