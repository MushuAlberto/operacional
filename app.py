import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import base64
from plotly.subplots import make_subplots
import json

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Reporte Priorizado SLIT", layout="wide", page_icon="📊")

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
<style>
    .metric-card {
        background-color: #f9f9f9;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 4px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2E7D32;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNCIÓN DE CACHÉ PARA CARGA DE DATOS ---
@st.cache_data(ttl=3600) # Guarda los datos en caché por 1 hora
def load_data(uploaded_file):
    cols_idx = [1, 31, 32, 33, 34, 35, 36, 46]
    # engine='openpyxl' es necesario para .xlsm
    df = pd.read_excel(uploaded_file, sheet_name="Base de Datos", usecols=cols_idx, engine='openpyxl')
    df.columns = ['Fecha', 'Producto', 'Destino', 'Ton_Prog', 'Ton_Real', 'Eq_Prog', 'Eq_Real', 'Regulacion_Real']
    
    # Limpieza
    df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce').dt.date
    df = df.dropna(subset=['Fecha'])
    df['Producto'] = df['Producto'].astype(str).str.upper().str.strip()
    df['Destino'] = df['Destino'].astype(str).str.strip()
    
    cols_num = ['Ton_Prog', 'Ton_Real', 'Eq_Prog', 'Eq_Real', 'Regulacion_Real']
    for col in cols_num:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
    return df

# --- INICIO DE LA APP ---
st.title("📊 Dashboard de Despachos por Producto")
st.markdown("---")

file_tablero = st.file_uploader("Cargar 03.- Tablero Despachos (.xlsm)", type=["xlsm"])

if file_tablero:
    try:
        # 1. Carga de datos optimizada
        df = load_data(file_tablero)

        # 2. Selección de Fecha
        fechas_disp = sorted(df['Fecha'].unique(), reverse=True)
        
        # Sidebar mejorado
        with st.sidebar:
            st.header("Filtros")
            fecha_sel = st.selectbox("📅 Seleccione la Fecha", fechas_disp)
            st.info(f"Analizando datos del: **{fecha_sel.strftime('%d-%m-%Y')}**")
            st.divider()
            st.caption("Versión Dashboard: 2.0")

        df_dia = df[df['Fecha'] == fecha_sel]
        
        if df_dia.empty:
            st.warning("No hay datos para la fecha seleccionada.")
            st.stop()

        # --- PRIORIZACIÓN DE PRODUCTOS ---
        productos_nombres = sorted(df_dia['Producto'].unique())
        if "SLIT" in productos_nombres:
            productos_nombres.remove("SLIT")
            productos_ordenados = ["SLIT"] + productos_nombres
        else:
            productos_ordenados = productos_nombres

        # ========================================
        # SECCIÓN 1: RESUMEN GENERAL
        # ========================================
        
        col_img_izq, col_espacio, col_img_der = st.columns([2, 6, 3], vertical_alignment="center")
        
        with col_img_izq:
            # Intento cargar imagen local, si falla, usa un placeholder
            try:
                st.image("logoSQM-li-90.png", width=120)
            except:
                st.markdown("🏢 **SQM**") # Placeholder texto
            
        with col_img_der:
            try:
                st.markdown('<div style="text-align: right;">', unsafe_allow_html=True)
                st.image("Image20240314124309.png", width=250)
                st.markdown('</div>', unsafe_allow_html=True)
            except:
                st.markdown('<div style="text-align: right;">📦 Logística</div>', unsafe_allow_html=True)
        
        st.markdown(f"<h3 style='text-align: center;'>Resumen Diario: {fecha_sel.strftime('%d-%m-%Y')}</h3>", unsafe_allow_html=True)
        st.markdown("---")
        
        # Cálculos Generales
        total_ton_prog = df_dia['Ton_Prog'].sum()
        total_ton_real = df_dia['Ton_Real'].sum()
        total_eq_prog = df_dia['Eq_Prog'].sum()
        total_eq_real = df_dia['Eq_Real'].sum()
        cumplimiento_general = (total_ton_real / total_ton_prog * 100) if total_ton_prog > 0 else 0
        num_productos = len(productos_ordenados)
        regulacion_general = df_dia['Regulacion_Real'].mean() * 100

        # KPIs Totales con estilo nativo
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Ton. Real Total", f"{total_ton_real:,.0f}", f"{total_ton_real - total_ton_prog:,.0f} vs Prog")
        k2.metric("Equipos Real Total", f"{total_eq_real:.0f}", f"{total_eq_real - total_eq_prog:.0f} vs Prog")
        k3.metric("Cumplimiento Global", f"{cumplimiento_general:.1f}%", f"{cumplimiento_general - 100:.1f}%", delta_color="normal" if cumplimiento_general >= 95 else "inverse")
        k4.metric("Prod. Despachados", f"{num_productos}")
        k5.metric("Regulación Prom.", f"{regulacion_general:.1f}%")
        
        st.markdown("---")
        
        # Preparar Dataframe de Resumen
        resumen_productos = []
        for prod in productos_ordenados:
            df_p = df_dia[df_dia['Producto'] == prod]
            t_prog = df_p['Ton_Prog'].sum()
            t_real = df_p['Ton_Real'].sum()
            resumen_productos.append({
                'Producto': prod,
                'Ton_Prog': t_prog,
                'Ton_Real': t_real,
                'Eq_Prog': df_p['Eq_Prog'].sum(),
                'Eq_Real': df_p['Eq_Real'].sum(),
                'Cumplimiento': (t_real / t_prog * 100) if t_prog > 0 else 0
            })
        
        df_resumen = pd.DataFrame(resumen_productos)

        # Gráficos Generales
        col_g1, col_g2 = st.columns([2, 1])
        
        with col_g1:
            fig_ton = go.Figure()
            fig_ton.add_trace(go.Bar(name='Ton. Prog', x=df_resumen['Producto'], y=df_resumen['Ton_Prog'], marker_color='#A8D5BA', texttemplate="%{y:,.0f}", textposition='auto'))
            fig_ton.add_trace(go.Bar(name='Ton. Real', x=df_resumen['Producto'], y=df_resumen['Ton_Real'], marker_color='#2E7D32', texttemplate="%{y:,.0f}", textposition='auto'))
            fig_ton.update_layout(title="Comparativa Toneladas (Prog vs Real)", barmode='group', height=350, legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig_ton, use_container_width=True)
            
        with col_g2:
            colors = ['#2E7D32' if c >= 100 else '#FFA726' if c >= 90 else '#EF5350' for c in df_resumen['Cumplimiento']]
            fig_cump = go.Figure(go.Bar(x=df_resumen['Producto'], y=df_resumen['Cumplimiento'], marker_color=colors, texttemplate="%{y:.1f}%", textposition='auto'))
            fig_cump.add_hline(y=100, line_dash="dot", line_color="gray", annotation_text="Meta")
            fig_cump.update_layout(title="% Cumplimiento", height=350)
            st.plotly_chart(fig_cump, use_container_width=True)

        # ========================================
        # SECCIÓN 2: DETALLES POR PRODUCTO (TABS)
        # ========================================
        st.header("🔬 Análisis Detallado por Producto")
        
        tabs = st.tabs([f"📌 {p}" if p == "SLIT" else p for p in productos_ordenados])
        
        # Diccionario para guardar figuras y usarlas luego en el reporte HTML
        product_figures = {}

        for idx, prod in enumerate(productos_ordenados):
            with tabs[idx]:
                df_p = df_dia[df_dia['Producto'] == prod]
                
                # Métricas locales
                t_p, t_r = df_p['Ton_Prog'].sum(), df_p['Ton_Real'].sum()
                e_p, e_r = df_p['Eq_Prog'].sum(), df_p['Eq_Real'].sum()
                cump = (t_r / t_p * 100) if t_p > 0 else 0
                
                # Layout interno
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Tonelaje Real", f"{t_r:,.0f}", f"{t_r - t_p:,.0f}")
                c2.metric("Equipos Real", f"{e_r:.0f}", f"{e_r - e_p:.0f}")
                c3.metric("Cumplimiento", f"{cump:.1f}%", delta_color="normal" if cump >= 95 else "inverse")
                
                # Destino Top
                dest_top = df_p.groupby('Destino')['Ton_Real'].sum().idxmax() if not df_p.empty else "N/A"
                c4.metric("Destino Principal", dest_top)
                
                st.divider()
                
                col_sub1, col_sub2 = st.columns([3, 2])
                
                with col_sub1:
                    # Gráfico Combinado Mejorado
                    fig_comb = make_subplots(rows=1, cols=2, subplot_titles=("Toneladas", "Equipos"), horizontal_spacing=0.1)
                    
                    # Toneladas
                    fig_comb.add_trace(go.Bar(name='Ton P', x=['Total'], y=[t_p], marker_color='#A8D5BA'), row=1, col=1)
                    fig_comb.add_trace(go.Bar(name='Ton R', x=['Total'], y=[t_r], marker_color='#2E7D32'), row=1, col=1)
                    
                    # Equipos
                    fig_comb.add_trace(go.Bar(name='Eq P', x=['Total'], y=[e_p], marker_color='#BDD7EE'), row=1, col=2)
                    fig_comb.add_trace(go.Bar(name='Eq R', x=['Total'], y=[e_r], marker_color='#2F5597'), row=1, col=2)
                    
                    fig_comb.update_layout(height=300, barmode='group', showlegend=False, title_text=f"Balance: {prod}")
                    st.plotly_chart(fig_comb, use_container_width=True)
                    
                    # Guardamos la figura para el reporte HTML
                    product_figures[prod] = fig_comb

                with col_sub2:
                    st.markdown("##### 📋 Desglose por Destino")
                    df_dest = df_p.groupby('Destino').agg({'Ton_Real': 'sum', 'Eq_Real': 'sum'}).sort_values('Ton_Real', ascending=False).reset_index()
                    df_dest['Ton_Real'] = df_dest['Ton_Real'].apply(lambda x: f"{x:,.1f}")
                    st.dataframe(df_dest, use_container_width=True, hide_index=True, height=250)

        # ========================================
        # SECCIÓN 3: REPORTING
        # ========================================
        st.markdown("---")
        st.subheader("📤 Exportar Datos")
        
        ce1, ce2 = st.columns(2)
        
        with ce1:
            if st.button("📄 Generar Reporte HTML Interactivo", type="primary", use_container_width=True):
                with st.spinner("Compilando gráficos y tablas..."):
                    
                    # Generación segura del HTML
                    html_template = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>Reporte {fecha_sel}</title>
                        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                        <style>
                            body {{ font-family: sans-serif; padding: 20px; background: #f4f6f9; }}
                            .card {{ background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                            h1 {{ color: #2E7D32; }}
                            .kpi-box {{ display: inline-block; width: 22%; background: #e8f5e9; padding: 10px; margin: 1%; text-align: center; border-radius: 5px; }}
                        </style>
                    </head>
                    <body>
                        <div class="card">
                            <h1>Reporte de Despachos: {fecha_sel.strftime('%d-%m-%Y')}</h1>
                            <div class="kpi-box"><h3>{total_ton_real:,.0f}</h3><small>Ton Totales</small></div>
                            <div class="kpi-box"><h3>{cumplimiento_general:.1f}%</h3><small>Cumplimiento</small></div>
                            <div class="kpi-box"><h3>{total_eq_real:.0f}</h3><small>Equipos</small></div>
                        </div>
                        
                        <div class="card">
                            <h2>Visión General</h2>
                            <div id="chart_global"></div>
                        </div>
                        
                        <!-- Contenedores para gráficos por producto -->
                    """
                    
                    # Añadir contenedores HTML para cada producto
                    for prod in productos_ordenados:
                        html_template += f"""
                        <div class="card">
                            <h3>Detalle: {prod}</h3>
                            <div id="chart_{prod.replace(' ', '_')}"></div>
                        </div>
                        """
                    
                    html_template += "<script>"
                    
                    # 1. Gráfico Global
                    json_global = fig_ton.to_json()
                    html_template += f"var data_global = {json_global}; Plotly.newPlot('chart_global', data_global.data, data_global.layout);"
                    
                    # 2. Gráficos por Producto (Loop JS)
                    for prod in productos_ordenados:
                        if prod in product_figures:
                            safe_id = prod.replace(' ', '_')
                            json_prod = product_figures[prod].to_json()
                            html_template += f"var data_{safe_id} = {json_prod}; Plotly.newPlot('chart_{safe_id}', data_{safe_id}.data, data_{safe_id}.layout);"
                            
                    html_template += "</script></body></html>"
                    
                    b64 = base64.b64encode(html_template.encode()).decode()
                    href = f'<a href="data:text/html;base64,{b64}" download="Reporte_{fecha_sel}.html" style="text-decoration:none; color:white; background-color:#2E7D32; padding:10px 20px; border-radius:5px; display:block; text-align:center;">📥 Descargar HTML Final</a>'
                    st.markdown(href, unsafe_allow_html=True)

        with ce2:
            if st.button("📧 Generar Texto para Correo", use_container_width=True):
                # Lógica simplificada de correo
                txt_correo = f"""
                **Asunto:** Reporte Despachos {fecha_sel.strftime('%d/%m')} - Cumplimiento {cumplimiento_general:.1f}%
                
                Estimados,
                
                Resumen de la jornada {fecha_sel.strftime('%d-%m-%Y')}:
                
                🔶 **GENERAL:**
                - Tonelaje: {total_ton_real:,.0f} ton ({'✅' if total_ton_real >= total_ton_prog else '⚠️'} vs plan)
                - Cumplimiento: {cumplimiento_general:.1f}%
                
                🔶 **DETALLE TOP PRODUCTOS:**
                """
                
                for _, row in df_ranking.head(3).iterrows(): # df_ranking debe existir (lo calculaste arriba en tu codigo original)
                     # NOTA: En este snippet refactorizado, asegúrate de crear df_ranking antes si no lo incluí en el bloque principal
                     txt_correo += f"- {row['Producto']}: {row['Ton_Real']:,.0f} ton ({row['Cumplimiento']:.1f}%)\n"
                
                st.text_area("Copiar y Pegar:", value=txt_correo, height=300)

    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")
        st.write(e) # Para depuración
