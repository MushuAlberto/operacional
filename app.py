import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from datetime import datetime

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Reporte Operacional SQM", layout="wide", page_icon="📊")

def init_gemini():
    """Valida la existencia de la API Key en los secretos de Streamlit"""
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"], None
    else:
        return None, "⚠️ Falta la API Key en los Secrets de Streamlit."

def call_gemini_api(prompt, api_key, model="gemini-1.5-flash"):
    """Llama a la API de Gemini usando la estructura REST v1 estable"""
    # Limpieza del nombre del modelo para la URL
    model_clean = model.replace("-latest", "")
    if not model_clean.startswith("models/"):
        model_path = f"models/{model_clean}"
    else:
        model_path = model_clean

    # URL optimizada para la versión estable
    url = f"https://generativelanguage.googleapis.com/v1/{model_path}:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.3, # Baja temperatura para análisis de datos precisos
            "maxOutputTokens": 1500,
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code != 200:
            error_detail = response.json().get('error', {}).get('message', 'Error desconocido')
            return None, f"Error {response.status_code}: {error_detail}"
            
        result = response.json()
        if 'candidates' in result and len(result['candidates']) > 0:
            return result['candidates'][0]['content']['parts'][0]['text'], None
        return None, "La API no devolvió candidatos de respuesta."
    except Exception as e:
        return None, f"Fallo de conexión: {str(e)}"

api_key, error_msg = init_gemini()

# Título e Interfaz
st.title("📊 Análisis de Despacho por Producto - SQM")
st.markdown("**Sistema operacional con IA integrada para optimización de logística**")
st.divider()

# --- 2. CARGA DE DATOS ---
uploaded_file = st.file_uploader("📁 Subir archivo Excel (02.- Histórico Romanas)", type=["xlsx"])

if uploaded_file:
    try:
        with st.spinner("Procesando datos..."):
            df = pd.read_excel(uploaded_file)
            df.columns = df.columns.str.strip()
            
            # Limpieza de Fechas y Números
            df['FECHA'] = pd.to_datetime(df['FECHA'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['FECHA'])
            df['TONELAJE'] = pd.to_numeric(df['TONELAJE'], errors='coerce').fillna(0)
            
            # Normalización de Nombres (Evita duplicados por espacios o puntos)
            df['PRODUCTO'] = df['PRODUCTO'].astype(str).str.strip().str.upper()
            if 'EMPRESA DE TRANSPORTE' in df.columns:
                df['EMPRESA DE TRANSPORTE'] = df['EMPRESA DE TRANSPORTE'].astype(str)\
                    .str.replace(r'\s+', ' ', regex=True)\
                    .str.replace('.', '', regex=False)\
                    .str.strip().str.upper()
            
            # Columnas Temporales
            df['DIA_SEMANA'] = df['FECHA'].dt.day_name()
        
        st.success(f"✅ {len(df)} registros cargados correctamente.")

        # --- 3. FILTROS LATERALES ---
        st.sidebar.header("⚙️ Panel de Control")
        min_f, max_f = df['FECHA'].min().date(), df['FECHA'].max().date()
        
        col_f1, col_f2 = st.sidebar.columns(2)
        f_inicio = col_f1.date_input("Desde", max_f)
        f_fin = col_f2.date_input("Hasta", max_f)
        
        lista_prod = sorted(df['PRODUCTO'].unique())
        prod_sel = st.sidebar.multiselect("Productos", lista_prod, default=lista_prod)
        
        mask = (df['FECHA'].dt.date >= f_inicio) & (df['FECHA'].dt.date <= f_fin) & (df['PRODUCTO'].isin(prod_sel))
        df_view = df.loc[mask].copy()

        if not df_view.empty:
            # --- 4. KPIs ---
            st.subheader("📈 Resumen de Operación")
            c1, c2, c3, c4 = st.columns(4)
            total_ton = df_view['TONELAJE'].sum()
            c1.metric("Tonelaje Total", f"{total_ton:,.1f} T")
            c2.metric("Viajes", f"{len(df_view):,}")
            c3.metric("Productos", df_view['PRODUCTO'].nunique())
            c4.metric("Promedio Viaje", f"{df_view[df_view['TONELAJE']>0]['TONELAJE'].mean():.1f} T")

            # --- 5. VISUALIZACIÓN ---
            tab1, tab2 = st.tabs(["📊 Distribución de Productos", "📅 Análisis Temporal"])
            
            with tab1:
                df_prod = df_view.groupby('PRODUCTO')['TONELAJE'].sum().reset_index().sort_values('TONELAJE', ascending=False)
                fig_bar = px.bar(df_prod, x='PRODUCTO', y='TONELAJE', color='TONELAJE', 
                                 text_auto='.2s', color_continuous_scale='Greens',
                                 title="Tonelaje por Tipo de Producto")
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with tab2:
                df_time = df_view.groupby(df_view['FECHA'].dt.date)['TONELAJE'].sum().reset_index()
                fig_line = px.line(df_time, x='FECHA', y='TONELAJE', markers=True, title="Evolución Diaria de Despachos")
                fig_line.update_traces(line_color='#2E7D32')
                st.plotly_chart(fig_line, use_container_width=True)

            # --- 6. IA INTEGRADA ---
            st.divider()
            st.subheader("🤖 Análisis de Tendencias con IA")
            
            col_ai_1, col_ai_2 = st.columns([2, 1])
            with col_ai_2:
                tipo_an = st.selectbox("Enfoque del análisis", ["Resumen Ejecutivo", "Eficiencia Operativa", "Recomendaciones"])
                mod_sel = st.selectbox("Modelo Gemini", ["gemini-1.5-flash", "gemini-1.5-pro"])
            
            with col_ai_1:
                if st.button("🚀 Generar Informe Inteligente", type="primary", use_container_width=True):
                    if not api_key:
                        st.error("Error: No se encontró la API Key.")
                    else:
                        with st.spinner("Analizando datos..."):
                            contexto = f"""
                            Datos SQM ({f_inicio} a {f_fin}):
                            - Total Tonelaje: {total_ton:,.0f}
                            - Total Viajes: {len(df_view)}
                            - Detalle por producto: {df_prod.to_dict(orient='records')}
                            
                            Tarea: Proporciona un {tipo_an} sobre estos datos destacando el producto con mayor movimiento y una sugerencia de optimización.
                            """
                            respuesta, err = call_gemini_api(contexto, api_key, mod_sel)
                            if err:
                                st.error(f"Error de IA: {err}")
                            else:
                                st.info(respuesta)

            # --- 7. DETALLE ---
            with st.expander("🔍 Ver Tabla de Datos"):
                st.dataframe(df_view[['FECHA', 'PRODUCTO', 'DESTINO', 'TONELAJE']], use_container_width=True)
        else:
            st.warning("No hay datos para los filtros seleccionados.")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
else:
    st.info("👋 Por favor, sube el archivo Excel de Romanas para comenzar el análisis.")
