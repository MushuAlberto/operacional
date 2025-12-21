import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import openai
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Reporte Operacional SQM", layout="wide", page_icon="📊")

# Inicialización segura de la IA
def init_openai():
    """Inicializa y valida la conexión con OpenAI"""
    if "OPENAI_API_KEY" in st.secrets:
        try:
            openai.api_key = st.secrets["OPENAI_API_KEY"]
            return True, None
        except Exception as e:
            return False, f"Error de configuración de IA: {str(e)}"
    else:
        return False, "⚠️ Falta la API Key en los Secrets de Streamlit."

api_configured, error_msg = init_openai()
if error_msg:
    st.sidebar.warning(error_msg)

# Título principal
st.title("📊 Análisis de Despacho por Producto - SQM")
st.markdown("**Sistema de análisis operacional con IA integrada (ChatGPT)**")
st.divider()

# --- 2. CARGA DE DATOS ---
uploaded_file = st.file_uploader(
    "📁 Subir archivo Excel (02.- Histórico Romanas)", 
    type=["xlsx"],
    help="Sube el archivo con los datos de despachos"
)

if uploaded_file:
    try:
        # Carga y limpieza de datos
        with st.spinner("Cargando datos..."):
            df = pd.read_excel(uploaded_file)
            df.columns = df.columns.str.strip()
            
            # Limpieza de Fechas y Tonelaje
            df['FECHA'] = pd.to_datetime(df['FECHA'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['FECHA'])
            df['TONELAJE'] = pd.to_numeric(df['TONELAJE'], errors='coerce').fillna(0)
            df['PRODUCTO'] = df['PRODUCTO'].astype(str).str.strip().str.upper()
            
            # Nuevas columnas calculadas
            df['AÑO'] = df['FECHA'].dt.year
            df['MES'] = df['FECHA'].dt.month
            df['NOMBRE_MES'] = df['FECHA'].dt.strftime('%B')
            df['DIA_SEMANA'] = df['FECHA'].dt.day_name()
        
        st.success(f"✅ Datos cargados: {len(df)} registros desde {df['FECHA'].min().date()} hasta {df['FECHA'].max().date()}")
        
        # --- 3. FILTROS MEJORADOS ---
        st.sidebar.header("⚙️ Filtros de Análisis")
        
        # Selector de rango de fechas
        col_f1, col_f2 = st.sidebar.columns(2)
        min_fecha = df['FECHA'].min().date()
        max_fecha = df['FECHA'].max().date()
        
        fecha_inicio = col_f1.date_input("Desde", max_fecha, min_value=min_fecha, max_value=max_fecha)
        fecha_fin = col_f2.date_input("Hasta", max_fecha, min_value=min_fecha, max_value=max_fecha)
        
        # Filtros adicionales
        lista_productos = sorted(df['PRODUCTO'].unique())
        productos_sel = st.sidebar.multiselect(
            "Productos", 
            lista_productos, 
            default=lista_productos,
            help="Selecciona uno o más productos para filtrar"
        )
        
        if 'EMPRESA DE TRANSPORTE' in df.columns:
            empresas = sorted(df['EMPRESA DE TRANSPORTE'].dropna().unique())
            empresas_sel = st.sidebar.multiselect("Empresas de Transporte", empresas, default=empresas)
        else:
            empresas_sel = []
        
        # Aplicar filtros
        mask = (
            (df['FECHA'].dt.date >= fecha_inicio) & 
            (df['FECHA'].dt.date <= fecha_fin) & 
            (df['PRODUCTO'].isin(productos_sel))
        )
        if empresas_sel and 'EMPRESA DE TRANSPORTE' in df.columns:
            mask = mask & (df['EMPRESA DE TRANSPORTE'].isin(empresas_sel))
        
        df_view = df.loc[mask].copy()
        
        if not df_view.empty:
            # --- 4. KPIs MEJORADOS ---
            st.subheader("📈 Indicadores Clave")
            c1, c2, c3, c4 = st.columns(4)
            
            total_ton = df_view['TONELAJE'].sum()
            num_viajes = len(df_view)
            num_productos = df_view['PRODUCTO'].nunique()
            promedio_ton = df_view['TONELAJE'].mean()
            
            c1.metric("Tonelaje Total", f"{total_ton:,.0f} Ton")
            c2.metric("N° de Viajes", f"{num_viajes:,}")
            c3.metric("Productos Diferentes", num_productos)
            c4.metric("Promedio por Viaje", f"{promedio_ton:.1f} Ton")
            
            st.divider()
            
            # --- 5. VISUALIZACIONES ---
            tab1, tab2, tab3 = st.tabs(["📊 Por Producto", "📅 Tendencia Temporal", "🏢 Por Empresa"])
            
            with tab1:
                st.subheader(f"Distribución de Tonelaje por Producto")
                df_prod = df_view.groupby('PRODUCTO').agg({
                    'TONELAJE': 'sum',
                    'FECHA': 'count'
                }).rename(columns={'FECHA': 'VIAJES'}).reset_index()
                df_prod = df_prod.sort_values('TONELAJE', ascending=False)
                
                col_g1, col_g2 = st.columns([2, 1])
                
                with col_g1:
                    fig_bar = px.bar(
                        df_prod, 
                        x='PRODUCTO', 
                        y='TONELAJE',
                        color='TONELAJE',
                        text='TONELAJE',
                        color_continuous_scale='Greens',
                        labels={'TONELAJE': 'Tonelaje (Ton)'}
                    )
                    fig_bar.update_traces(texttemplate='%{text:.2s}', textposition='outside')
                    fig_bar.update_layout(height=400)
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                with col_g2:
                    fig_pie = px.pie(
                        df_prod, 
                        values='TONELAJE', 
                        names='PRODUCTO',
                        hole=0.4,
                        color_discrete_sequence=px.colors.sequential.Greens
                    )
                    fig_pie.update_layout(height=400)
                    st.plotly_chart(fig_pie, use_container_width=True)
            
            with tab2:
                st.subheader("Tendencia de Despachos en el Tiempo")
                df_tiempo = df_view.groupby(df_view['FECHA'].dt.date)['TONELAJE'].sum().reset_index()
                df_tiempo.columns = ['FECHA', 'TONELAJE']
                
                fig_line = px.line(
                    df_tiempo, 
                    x='FECHA', 
                    y='TONELAJE',
                    markers=True,
                    labels={'TONELAJE': 'Tonelaje (Ton)', 'FECHA': 'Fecha'}
                )
                fig_line.update_traces(line_color='#2E7D32')
                st.plotly_chart(fig_line, use_container_width=True)
                
                # Análisis por día de la semana
                st.subheader("Distribución por Día de la Semana")
                df_dow = df_view.groupby('DIA_SEMANA')['TONELAJE'].sum().reset_index()
                dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                df_dow['DIA_SEMANA'] = pd.Categorical(df_dow['DIA_SEMANA'], categories=dias_orden, ordered=True)
                df_dow = df_dow.sort_values('DIA_SEMANA')
                
                fig_dow = px.bar(df_dow, x='DIA_SEMANA', y='TONELAJE', color='TONELAJE',
                                color_continuous_scale='Greens')
                st.plotly_chart(fig_dow, use_container_width=True)
            
            with tab3:
                if 'EMPRESA DE TRANSPORTE' in df_view.columns:
                    st.subheader("Análisis por Empresa de Transporte")
                    df_emp = df_view.groupby('EMPRESA DE TRANSPORTE').agg({
                        'TONELAJE': 'sum',
                        'FECHA': 'count'
                    }).rename(columns={'FECHA': 'VIAJES'}).reset_index()
                    df_emp = df_emp.sort_values('TONELAJE', ascending=False)
                    
                    fig_emp = px.bar(
                        df_emp, 
                        x='EMPRESA DE TRANSPORTE', 
                        y='TONELAJE',
                        color='VIAJES',
                        text='TONELAJE',
                        color_continuous_scale='Blues'
                    )
                    fig_emp.update_traces(texttemplate='%{text:.2s}', textposition='outside')
                    st.plotly_chart(fig_emp, use_container_width=True)
                    
                    st.dataframe(df_emp, use_container_width=True)
                else:
                    st.info("No hay información de empresas de transporte en el dataset")
            
            st.divider()
            
            # --- 6. ANÁLISIS CON IA (OPENAI/CHATGPT) ---
            st.subheader("🤖 Análisis Inteligente con ChatGPT")
            
            col_ai1, col_ai2, col_ai3 = st.columns([2, 1, 1])
            
            with col_ai2:
                tipo_analisis = st.selectbox(
                    "Tipo de análisis",
                    ["Resumen General", "Análisis Detallado", "Recomendaciones", "Comparativa"]
                )
            
            with col_ai3:
                modelo = st.selectbox(
                    "Modelo",
                    ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
                    help="GPT-4o es más preciso, GPT-3.5-turbo es más rápido y económico"
                )
            
            with col_ai1:
                if st.button("🚀 Generar Análisis con IA", type="primary", use_container_width=True):
                    if not api_configured:
                        st.error("❌ La IA no está configurada correctamente. Verifica la API Key de OpenAI.")
                    else:
                        try:
                            with st.spinner(f"🔍 Analizando datos con {modelo}..."):
                                # Preparar contexto más rico
                                estadisticas = {
                                    'total_tonelaje': float(total_ton),
                                    'num_viajes': int(num_viajes),
                                    'num_productos': int(num_productos),
                                    'promedio_viaje': float(promedio_ton),
                                    'fecha_inicio': str(fecha_inicio),
                                    'fecha_fin': str(fecha_fin),
                                    'dias_analisis': (fecha_fin - fecha_inicio).days + 1
                                }
                                
                                # Construir prompt según tipo de análisis
                                if tipo_analisis == "Resumen General":
                                    prompt = f"""Eres un analista de operaciones logísticas de SQM. Analiza estos datos de despacho:

Estadísticas del período ({estadisticas['fecha_inicio']} a {estadisticas['fecha_fin']}):
- Tonelaje total: {estadisticas['total_tonelaje']:,.0f} toneladas
- Número de viajes: {estadisticas['num_viajes']}
- Productos diferentes: {estadisticas['num_productos']}
- Promedio por viaje: {estadisticas['promedio_viaje']:.1f} toneladas

Top 5 productos por tonelaje:
{df_prod.head().to_string(index=False)}

Proporciona un resumen ejecutivo conciso (máximo 150 palabras) sobre el desempeño operacional."""

                                elif tipo_analisis == "Análisis Detallado":
                                    prompt = f"""Como experto en logística, analiza en detalle estos datos de despacho de SQM:

Período: {estadisticas['dias_analisis']} días
Datos: {estadisticas['total_tonelaje']:,.0f} toneladas en {estadisticas['num_viajes']} viajes

Distribución por producto:
{df_prod.to_string(index=False)}

Proporciona:
1. Análisis de eficiencia operativa
2. Identificación de patrones
3. Productos críticos
4. Observaciones sobre la distribución de carga"""

                                elif tipo_analisis == "Recomendaciones":
                                    prompt = f"""Eres un consultor de optimización logística. Basándote en estos datos de SQM:

Métricas clave:
- {estadisticas['num_viajes']} viajes realizados
- {estadisticas['total_tonelaje']:,.0f} toneladas despachadas
- Promedio: {estadisticas['promedio_viaje']:.1f} ton/viaje

Productos principales:
{df_prod.head(5).to_string(index=False)}

Proporciona 3-4 recomendaciones específicas y accionables para optimizar las operaciones."""

                                else:  # Comparativa
                                    prompt = f"""Analiza comparativamente el desempeño de estos productos de SQM:

{df_prod.to_string(index=False)}

Identifica:
1. Productos de mayor/menor volumen
2. Posibles desequilibrios operacionales
3. Oportunidades de consolidación
4. Productos que requieren atención especial"""
                                
                                # Generar respuesta con OpenAI
                                response = openai.ChatCompletion.create(
                                    model=modelo,
                                    messages=[
                                        {
                                            "role": "system", 
                                            "content": "Eres un analista experto en operaciones logísticas y minería. Proporciona análisis claros, concisos y accionables en español."
                                        },
                                        {
                                            "role": "user", 
                                            "content": prompt
                                        }
                                    ],
                                    temperature=0.7,
                                    max_tokens=1000
                                )
                                
                                # Mostrar resultado
                                st.markdown("### 📋 Resultado del Análisis")
                                st.markdown(response.choices[0].message.content)
                                
                                # Información adicional
                                col_info1, col_info2, col_info3 = st.columns(3)
                                with col_info1:
                                    st.caption(f"🤖 Modelo: {modelo}")
                                with col_info2:
                                    st.caption(f"📝 Tokens usados: {response.usage.total_tokens}")
                                with col_info3:
                                    st.caption(f"⚡ Tipo: {tipo_analisis}")
                                
                                # Métricas adicionales en expander
                                with st.expander("📊 Ver datos utilizados en el análisis"):
                                    st.json(estadisticas)
                                    st.dataframe(df_prod)
                                
                        except Exception as ia_err:
                            st.error("❌ Error al generar análisis con IA")
                            with st.expander("🔍 Ver detalles del error"):
                                st.code(str(ia_err))
                                st.info("""
**Posibles causas:**
- API Key inválida o expirada
- Límite de cuota excedido (verifica tu saldo en OpenAI)
- Problema de conectividad
- Modelo no disponible en tu cuenta

**Solución:** 
1. Verifica tu API Key en los Secrets de Streamlit
2. Revisa tu saldo en platform.openai.com/usage
3. Intenta con gpt-3.5-turbo si tienes problemas con GPT-4
                                """)
            
            st.divider()
            
            # --- 7. TABLA DETALLADA ---
            st.subheader("📋 Registros Detallados")
            
            # Opciones de visualización
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1:
                num_registros = st.selectbox("Registros a mostrar", [10, 25, 50, 100, "Todos"])
            with col_t2:
                ordenar_por = st.selectbox("Ordenar por", ['FECHA', 'TONELAJE', 'PRODUCTO'])
            with col_t3:
                orden_desc = st.checkbox("Descendente", value=True)
            
            df_tabla = df_view.sort_values(ordenar_por, ascending=not orden_desc)
            
            if num_registros != "Todos":
                df_tabla = df_tabla.head(num_registros)
            
            # Mostrar tabla con formato
            columnas_mostrar = ['FECHA', 'PRODUCTO', 'DESTINO', 'TONELAJE']
            if 'EMPRESA DE TRANSPORTE' in df_tabla.columns:
                columnas_mostrar.append('EMPRESA DE TRANSPORTE')
            
            st.dataframe(
                df_tabla[columnas_mostrar].style.format({'TONELAJE': '{:.2f}'}),
                use_container_width=True,
                height=400
            )
            
            # Botón de descarga
            csv = df_tabla.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Descargar datos filtrados (CSV)",
                data=csv,
                file_name=f"despachos_sqm_{fecha_inicio}_{fecha_fin}.csv",
                mime="text/csv"
            )
            
        else:
            st.warning("⚠️ No hay datos para los filtros seleccionados. Intenta ampliar el rango de fechas o cambiar los filtros.")
            
    except Exception as e:
        st.error(f"❌ Error al procesar el archivo Excel")
        with st.expander("🔍 Ver detalles del error"):
            st.code(str(e))
            st.info("Verifica que el archivo tenga las columnas: FECHA, PRODUCTO, DESTINO, TONELAJE")
else:
    # Pantalla de bienvenida
    st.info("👋 **Bienvenido al Sistema de Análisis Operacional SQM**")
    st.markdown("""
    ### 📝 Instrucciones:
    1. Sube el archivo Excel con los datos de despachos
    2. Usa los filtros en la barra lateral para ajustar el análisis
    3. Explora las diferentes visualizaciones en las pestañas
    4. Genera análisis inteligentes con ChatGPT para obtener insights
    
    ### 📊 Características:
    - ✅ Análisis de KPIs operacionales
    - ✅ Visualizaciones interactivas
    - ✅ Análisis con IA (ChatGPT GPT-4/GPT-3.5)
    - ✅ Exportación de datos
    - ✅ Filtros avanzados
    - ✅ Selección de modelos de IA
    """)
    
    # Mostrar estado de la API
    with st.expander("🔧 Estado de configuración"):
        if api_configured:
            st.success("✅ API de OpenAI configurada correctamente")
        else:
            st.error("❌ API de OpenAI no configurada")
            st.markdown("""
### Para configurar la API de OpenAI:

1. Obtén tu API Key en: https://platform.openai.com/api-keys
2. En Streamlit Cloud, ve a **Settings > Secrets**
3. Agrega el siguiente código:

```toml
OPENAI_API_KEY = "sk-tu-api-key-aqui"
```

4. Guarda y reinicia la app

**Nota:** Asegúrate de tener saldo disponible en tu cuenta de OpenAI.
            """)
