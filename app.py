import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from datetime import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Reporte Operacional SQM", layout="wide", page_icon="📊")

def init_gemini():
    """Valida la existencia de la API Key en los secretos de Streamlit"""
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"], None
    else:
        return None, "⚠️ Configura la GEMINI_API_KEY en los Secrets de Streamlit."

def call_gemini_api(prompt, api_key, model="gemini-1.5-flash"):
    """Llama a la API de Gemini usando v1beta para solucionar el Error 404"""
    model_name = model.replace("models/", "")
    # URL v1beta: Necesaria para modelos 1.5 en ciertas regiones y evitar el 404
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2, 
            "maxOutputTokens": 1000,
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code != 200:
            return None, f"Error {response.status_code}: {response.text}"
            
        result = response.json()
        if 'candidates' in result and len(result['candidates']) > 0:
            return result['candidates'][0]['content']['parts'][0]['text'], None
        return None, "Sin respuesta del modelo."
    except Exception as e:
        return None, f"Fallo de conexión: {str(e)}"

# --- 2. DICCIONARIO DE ESTANDARIZACIÓN DE EMPRESAS ---
MAPE_EMPRESAS = {
    "M AND Q SPA": "M&Q SPA", "M AND Q": "M&Q SPA", "M Q SPA": "M&Q SPA",
    "MQ SPA": "M&Q SPA", "MANDQ SPA": "M&Q SPA", "MINING AND QUARRYING SPA": "M&Q SPA",
    "M & Q SPA": "M&Q SPA", "M&Q": "M&Q SPA",
    "MINING SERVICES AND DERIVATES": "M S & D SPA",
    "M S AND D": "M S & D SPA", "M S D SPA": "M S & D SPA",
    "MS&D SPA": "M S & D SPA", "M S & D": "M S & D SPA",
    "JORQUERA TRANSPORTE S A": "JORQUERA TRANSPORTE S. A.",
    "AG SERVICE SPA": "AG SERVICES SPA"
}

api_key, error_msg = init_gemini()

# Interfaz Principal
st.title("📊 Dashboard de Control Operacional - SQM")
st.markdown("### Gestión de Despachos e Inteligencia Logística")
st.divider()

# --- 3. CARGA Y PROCESAMIENTO ---
uploaded_file = st.file_uploader("📁 Subir archivo Excel (02.- Histórico Romanas)", type=["xlsx"])

if uploaded_file:
    try:
        with st.spinner("Procesando datos operativos..."):
            df = pd.read_excel(uploaded_file)
            df.columns = df.columns.str.strip()
            
            # Limpieza básica
            df['FECHA'] = pd.to_datetime(df['FECHA'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['FECHA'])
            df['TONELAJE'] = pd.to_numeric(df['TONELAJE'], errors='coerce').fillna(0)
            
            # Estandarización de nombres
            df['PRODUCTO'] = df['PRODUCTO'].astype(str).str.strip().str.upper()
            if 'EMPRESA DE TRANSPORTE' in df.columns:
                df['EMPRESA DE TRANSPORTE'] = df['EMPRESA DE TRANSPORTE'].astype(str).str.strip().str.upper()
                df['EMPRESA DE TRANSPORTE'] = df['EMPRESA DE TRANSPORTE'].replace(MAPE_EMPRESAS)

        # --- 4. FILTROS Y BENCHMARK ---
        st.sidebar.header("⚙️ Filtros de Análisis")
        f_max = df['FECHA'].max().date()
        f_inicio = st.sidebar.date_input("Fecha Inicio", f_max)
        f_fin = st.sidebar.date_input("Fecha Fin", f_max)
        
        # Máscara de datos seleccionados
        mask = (df['FECHA'].dt.date >= f_inicio) & (df['FECHA'].dt.date <= f_fin)
        df_view = df.loc[mask].copy()

        if not df_view.empty:
            # Lógica de Benchmark Mensual
            mes_ref, año_ref = f_inicio.month, f_inicio.year
            df_mes = df[(df['FECHA'].dt.month == mes_ref) & (df['FECHA'].dt.year == año_ref)]
            prom_diario_mes = df_mes.groupby(df_mes['FECHA'].dt.date)['TONELAJE'].sum().mean()
            
            total_ton = df_view['TONELAJE'].sum()
            dias_sel = (f_fin - f_inicio).days + 1
            rendimiento_actual = total_ton / dias_sel
            desviacion = ((rendimiento_actual - prom_diario_mes) / prom_diario_mes) * 100

            # --- 5. KPIs VISUALES ---
            st.subheader(f"📈 Desempeño vs Promedio de {df['FECHA'].dt.strftime('%B').iloc[0]}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tonelaje Total", f"{total_ton:,.0f} T")
            c2.metric("Promedio Actual", f"{rendimiento_actual:,.1f} T/día")
            c3.metric("Promedio Mensual", f"{prom_diario_mes:,.1f} T/día")
            c4.metric("Desviación %", f"{desviacion:.1f}%", delta=f"{desviacion:.1f}%")

            # --- 6. ALERTAS TEMPRANAS ---
            if desviacion < -15:
                st.error(f"⚠️ **ALERTA DE CAÍDA:** El rendimiento actual está un {abs(desviacion):.1f}% por debajo del promedio mensual.")
            elif desviacion > 15:
                st.success(f"🚀 **SOBRE-RENDIMIENTO:** Operación un {desviacion:.1f}% sobre la media mensual.")

            # --- 7. GRÁFICOS INTERACTIVOS ---
            st.divider()
            t1, t2 = st.tabs(["📦 Análisis por Producto", "🚛 Análisis por Empresa"])
            
            with t1:
                df_prod = df_view.groupby('PRODUCTO')['TONELAJE'].sum().reset_index().sort_values('TONELAJE', ascending=False)
                fig_p = px.bar(df_prod, x='PRODUCTO', y='TONELAJE', color='TONELAJE', text_auto='.2s',
                               color_continuous_scale='Greens', title="Volumen de Despacho por Producto")
                st.plotly_chart(fig_p, use_container_width=True)
            
            with t2:
                df_emp = df_view.groupby('EMPRESA DE TRANSPORTE')['TONELAJE'].sum().reset_index().sort_values('TONELAJE', ascending=False)
                fig_e = px.bar(df_emp, x='EMPRESA DE TRANSPORTE', y='TONELAJE', color='TONELAJE', text_auto='.2s',
                               color_continuous_scale='Blues', title="Ranking de Empresas (Nombres Unificados)")
                st.plotly_chart(fig_e, use_container_width=True)

            # --- 8. IA INTEGRADA ---
            st.divider()
            st.subheader("🤖 Consultoría Logística (IA)")
            col_btn, col_txt = st.columns([1, 2])
            
            with col_btn:
                if st.button("🚀 Generar Informe de Gestión", type="primary", use_container_width=True):
                    if api_key:
                        with st.spinner("Gemini analizando variaciones..."):
                            ctx = f"""
                            Eres Jefe de Logística en SQM. Analiza:
                            - Rendimiento: {rendimiento_actual:.1f} T/día vs {prom_diario_mes:.1f} T/día (Mes).
                            - Desviación: {desviacion:.1f}%.
                            - Mix de Productos: {df_prod.head(5).to_dict(orient='records')}
                            
                            Tarea: Explica la causa probable de la desviación y da 2 acciones de mejora.
                            """
                            res, err = call_gemini_api(ctx, api_key)
                            if err: st.error(err)
                            else: st.markdown(f"**Análisis del Experto:**\n\n{res}")
                    else: st.warning("API Key no configurada.")

            # --- 9. TABLA DE DATOS ---
            with st.expander("🔍 Explorar Registros Detallados"):
                st.dataframe(df_view[['FECHA', 'PRODUCTO', 'EMPRESA DE TRANSPORTE', 'DESTINO', 'TONELAJE']], use_container_width=True)

        else:
            st.warning("No se encontraron datos para el rango de fechas seleccionado.")
            
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("👋 Bienvenido. Por favor sube el archivo Excel 'Histórico Romanas' para iniciar el análisis.")
