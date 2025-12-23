import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import base64
from io import BytesIO
from plotly.subplots import make_subplots
import json

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Reporte Priorizado SLIT", layout="wide", page_icon="📊")

# --- ESTILOS CSS ---
st.markdown("""
<style>
    .metric-card {
        background-color: #f9f9f9;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

st.title("Dashboard de Despachos por Producto")
st.markdown("---")

# --- FUNCIÓN DE CARGA DE DATOS (OPTIMIZADA) ---
@st.cache_data(ttl=3600)
def cargar_datos(file):
    cols_idx = [1, 31, 32, 33, 34, 35, 36, 46]
    df = pd.read_excel(file, sheet_name="Base de Datos", usecols=cols_idx, engine='openpyxl')
    df.columns = ['Fecha', 'Producto', 'Destino', 'Ton_Prog', 'Ton_Real', 'Eq_Prog', 'Eq_Real', 'Regulacion_Real']
    
    # Limpieza
    df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce').dt.date
    df = df.dropna(subset=['Fecha'])
    df['Producto'] = df['Producto'].astype(str).str.upper().str.strip()
    df['Destino'] = df['Destino'].astype(str).str.strip()
    
    # Asegurar tipos numéricos
    cols_num = ['Ton_Prog', 'Ton_Real', 'Eq_Prog', 'Eq_Real', 'Regulacion_Real']
    for col in cols_num:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

# --- INTERFAZ PRINCIPAL ---
file_tablero = st.file_uploader("Cargar 03.- Tablero Despachos (.xlsm)", type=["xlsm"])

if file_tablero:
    try:
        # 1. Carga de datos
        df = cargar_datos(file_tablero)

        # 2. Selección de Fecha
        fechas_disp = sorted(df['Fecha'].unique(), reverse=True)
        fecha_sel = st.sidebar.selectbox("📅 Seleccione la Fecha", fechas_disp)
        
        df_dia = df[df['Fecha'] == fecha_sel]
        
        # --- PRIORIZACIÓN DE PRODUCTOS ---
        productos_nombres = sorted(df_dia['Producto'].unique())
        if "SLIT" in productos_nombres:
            productos_nombres.remove("SLIT")
            productos_ordenados = ["SLIT"] + productos_nombres
        else:
            productos_ordenados = productos_nombres

        # ========================================
        # SECCIÓN 1: RESUMEN GENERAL DE LA JORNADA
        # ========================================
        
        st.markdown(f"<h2 style='text-align: center;'>RESUMEN GENERAL DE LA JORNADA</h2>", unsafe_allow_html=True)
        
        col_img_izq, col_espacio, col_img_der = st.columns([2, 6, 3], vertical_alignment="center")
        
        with col_img_izq:
            try:
                st.image("logoSQM-li-90.png", width=120)
            except:
                st.write("**SQM**") # Placeholder si falta imagen
            
        with col_img_der:
            try:
                st.markdown('<div style="text-align: right;">', unsafe_allow_html=True)
                st.image("Image20240314124309.png", width=250)
                st.markdown('</div>', unsafe_allow_html=True)
            except:
                st.markdown('<div style="text-align: right;">**Logística**</div>', unsafe_allow_html=True)
        
        st.markdown(f"<h3 style='text-align: center;'>📅 {fecha_sel.strftime('%d-%m-%Y')}</h3>", unsafe_allow_html=True)
        st.markdown("---")
        
        # Calcular totales
        total_ton_prog = df_dia['Ton_Prog'].sum()
        total_ton_real = df_dia['Ton_Real'].sum()
        total_eq_prog = df_dia['Eq_Prog'].sum()
        total_eq_real = df_dia['Eq_Real'].sum()
        cumplimiento_general = (total_ton_real / total_ton_prog * 100) if total_ton_prog > 0 else 0
        num_productos = len(productos_ordenados)
        regulacion_general = df_dia['Regulacion_Real'].mean() * 100
        
        # KPIs Totales
        st.markdown("### Indicadores Generales")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Tonelaje Total Real", f"{total_ton_real:,.0f}", f"{total_ton_real - total_ton_prog:,.0f} vs Prog")
        col2.metric("Equipos Total Real", f"{total_eq_real:.0f}", f"{total_eq_real - total_eq_prog:.0f} vs Prog")
        col3.metric("Cumplimiento General", f"{cumplimiento_general:.1f}%", f"{cumplimiento_general - 100:.1f}%")
        col4.metric("Productos Despachados", f"{num_productos}")
        col5.metric("Regulación Promedio", f"{regulacion_general:.1f}%")
        
        st.markdown("---")
        
        # Resumen por producto
        resumen_productos = []
        for prod in productos_ordenados:
            df_p = df_dia[df_dia['Producto'] == prod]
            resumen_productos.append({
                'Producto': prod,
                'Ton_Prog': df_p['Ton_Prog'].sum(),
                'Ton_Real': df_p['Ton_Real'].sum(),
                'Eq_Prog': df_p['Eq_Prog'].sum(),
                'Eq_Real': df_p['Eq_Real'].sum(),
                'Cumplimiento': (df_p['Ton_Real'].sum() / df_p['Ton_Prog'].sum() * 100) if df_p['Ton_Prog'].sum() > 0 else 0
            })
        
        df_resumen = pd.DataFrame(resumen_productos)
        
        # Gráficos Comparativos Generales
        st.markdown("### Comparativa por Producto")
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            fig_ton_general = go.Figure()
            fig_ton_general.add_trace(go.Bar(
                name='Ton. Programado', x=df_resumen['Producto'], y=df_resumen['Ton_Prog'],
                marker_color='#A8D5BA', text=df_resumen['Ton_Prog'].apply(lambda x: f"{x:,.0f}"), textposition='outside'
            ))
            fig_ton_general.add_trace(go.Bar(
                name='Ton. Real', x=df_resumen['Producto'], y=df_resumen['Ton_Real'],
                marker_color='#2E7D32', text=df_resumen['Ton_Real'].apply(lambda x: f"{x:,.0f}"), textposition='outside'
            ))
            fig_ton_general.update_layout(title="Toneladas por Producto", barmode='group', height=400, legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig_ton_general, use_container_width=True)
        
        with col_g2:
            colores_cumplimiento = ['#2E7D32' if c >= 100 else '#FFA726' if c >= 90 else '#EF5350' for c in df_resumen['Cumplimiento']]
            fig_cumplimiento = go.Figure()
            fig_cumplimiento.add_trace(go.Bar(
                x=df_resumen['Producto'], y=df_resumen['Cumplimiento'],
                marker_color=colores_cumplimiento, text=df_resumen['Cumplimiento'].apply(lambda x: f"{x:.1f}%"), textposition='outside'
            ))
            fig_cumplimiento.add_hline(y=100, line_dash="dash", line_color="gray", annotation_text="Meta 100%")
            fig_cumplimiento.update_layout(title="% Cumplimiento por Producto", height=400)
            st.plotly_chart(fig_cumplimiento, use_container_width=True)
        
        # Ranking
        st.markdown("### Ranking de Productos")
        df_ranking = df_resumen.copy()
        df_ranking['Diferencia'] = df_ranking['Ton_Real'] - df_ranking['Ton_Prog']
        df_ranking = df_ranking.sort_values('Ton_Real', ascending=False)
        
        # Display de tabla formateada
        df_display = df_ranking.copy()
        df_display['Ton_Prog'] = df_display['Ton_Prog'].apply(lambda x: f"{x:,.0f}")
        df_display['Ton_Real'] = df_display['Ton_Real'].apply(lambda x: f"{x:,.0f}")
        df_display['Cumplimiento'] = df_display['Cumplimiento'].apply(lambda x: f"{x:.1f}%")
        df_display['Diferencia'] = df_display['Diferencia'].apply(lambda x: f"{x:+,.0f}")
        
        st.dataframe(df_display[['Producto', 'Ton_Prog', 'Ton_Real', 'Diferencia', 'Cumplimiento']], use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # ========================================
        # SECCIÓN 2: DETALLES POR PRODUCTO (TABS)
        # ========================================
        st.header("DETALLES POR PRODUCTO")
        
        tabs = st.tabs(productos_ordenados)
        
        for idx, prod in enumerate(productos_ordenados):
            with tabs[idx]:
                df_p = df_dia[df_dia['Producto'] == prod]
                
                t_prog = df_p['Ton_Prog'].sum()
                t_real = df_p['Ton_Real'].sum()
                e_prog = df_p['Eq_Prog'].sum()
                e_real = df_p['Eq_Real'].sum()
                cumplimiento = (t_real / t_prog * 100) if t_prog > 0 else 0
                destino_principal = df_p.loc[df_p['Ton_Real'].idxmax(), 'Destino'] if not df_p.empty else "N/A"
                
                st.markdown(f"### Análisis de {prod}")
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Tonelaje Real", f"{t_real:,.0f}", f"{t_real-t_prog:,.0f}")
                c2.metric("Equipos Real", f"{e_real:.0f}", f"{e_real-e_prog:.0f}")
                c3.metric("Cumplimiento", f"{cumplimiento:.1f}%", delta_color="normal" if cumplimiento >= 95 else "inverse")
                c4.metric("Destino Principal", destino_principal)
                
                st.markdown("---")
                
                col_chart, col_data = st.columns([3, 2])
                
                with col_chart:
                    fig_comb = make_subplots(rows=1, cols=2, horizontal_spacing=0.15, subplot_titles=("Toneladas", "Equipos"))
                    
                    # Toneladas
                    fig_comb.add_trace(go.Bar(name='Ton. Plan', x=[''], y=[t_prog], marker_color='#A8D5BA'), row=1, col=1)
                    fig_comb.add_trace(go.Bar(name='Ton. Real', x=[''], y=[t_real], marker_color='#2E7D32'), row=1, col=1)
                    
                    # Equipos
                    fig_comb.add_trace(go.Bar(name='Eq. Plan', x=[''], y=[e_prog], marker_color='#BDD7EE'), row=1, col=2)
                    fig_comb.add_trace(go.Bar(name='Eq. Real', x=[''], y=[e_real], marker_color='#2F5597'), row=1, col=2)
                    
                    fig_comb.update_layout(title="Comparativa", height=350, showlegend=True, barmode='group')
                    st.plotly_chart(fig_comb, use_container_width=True)
                
                with col_data:
                    st.markdown("#### Despachos por Destino")
                    df_destinos = df_p.groupby('Destino').agg({'Ton_Real': 'sum', 'Eq_Real': 'sum'}).sort_values('Ton_Real', ascending=False).reset_index()
                    df_destinos['Ton_Real'] = df_destinos['Ton_Real'].apply(lambda x: f"{x:,.1f}")
                    st.dataframe(df_destinos, use_container_width=True, hide_index=True)

        # ========================================
        # SECCIÓN 3: GENERACIÓN DE REPORTES (CORREGIDO)
        # ========================================
        st.markdown("---")
        st.header("Exportar Reportes")
        
        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            generar_html = st.button("Generar Reporte HTML Interactivo", type="primary", use_container_width=True)
            
            if generar_html:
                with st.spinner("Generando reporte HTML..."):
                    # Construcción del HTML
                    html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Reporte Despachos {fecha_sel}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: sans-serif; padding: 20px; background: #f0f2f6; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; border-bottom: 3px solid #2E7D32; padding-bottom: 20px; margin-bottom: 20px; }}
        h1 {{ color: #2E7D32; margin: 0; }}
        .kpi-row {{ display: flex; justify-content: space-between; margin: 20px 0; }}
        .kpi-card {{ background: #f8f9fa; padding: 15px; border-radius: 10px; width: 18%; text-align: center; border: 1px solid #dee2e6; }}
        .kpi-val {{ font-size: 1.5em; font-weight: bold; color: #2E7D32; }}
        .section {{ margin: 40px 0; }}
        .tabs {{ overflow: hidden; border-bottom: 1px solid #ccc; margin-bottom: 20px; }}
        .tab-btn {{ background-color: inherit; float: left; border: none; outline: none; cursor: pointer; padding: 14px 16px; transition: 0.3s; font-size: 17px; }}
        .tab-btn:hover {{ background-color: #ddd; }}
        .tab-btn.active {{ background-color: #2E7D32; color: white; }}
        .tab-content {{ display: none; padding: 6px 12px; border-top: none; animation: fadeEffect 1s; }}
        @keyframes fadeEffect {{ from {{opacity: 0;}} to {{opacity: 1;}} }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; border-bottom: 1px solid #ddd; text-align: left; }}
        th {{ background-color: #2E7D32; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Reporte de Despachos</h1>
            <p>{fecha_sel.strftime('%d de %B de %Y')}</p>
        </div>

        <div class="kpi-row">
            <div class="kpi-card"><div>Ton. Real</div><div class="kpi-val">{total_ton_real:,.0f}</div></div>
            <div class="kpi-card"><div>Equipos</div><div class="kpi-val">{total_eq_real:.0f}</div></div>
            <div class="kpi-card"><div>Cumplimiento</div><div class="kpi-val">{cumplimiento_general:.1f}%</div></div>
            <div class="kpi-card"><div>Productos</div><div class="kpi-val">{num_productos}</div></div>
        </div>

        <div class="section">
            <h2>Gráficos Comparativos Generales</h2>
            <!-- DIVS PARA GRÁFICOS GENERALES (CORREGIDO) -->
            <div style="display: flex; gap: 20px;">
                <div id="grafico_toneladas" style="width: 50%;"></div>
                <div id="grafico_cumplimiento" style="width: 50%;"></div>
            </div>
        </div>

        <div class="section">
            <h2>Ranking de Productos</h2>
            <table>
                <thead><tr><th>Producto</th><th>Ton. Prog</th><th>Ton. Real</th><th>Cumplimiento</th></tr></thead>
                <tbody>
"""
                    for _, row in df_ranking.iterrows():
                        color = "green" if row['Cumplimiento'] >= 100 else "orange" if row['Cumplimiento'] >= 90 else "red"
                        html_content += f"<tr><td><b>{row['Producto']}</b></td><td>{row['Ton_Prog']:,.0f}</td><td>{row['Ton_Real']:,.0f}</td><td style='color:{color}'><b>{row['Cumplimiento']:.1f}%</b></td></tr>"
                    
                    html_content += """
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>Detalles por Producto</h2>
            <div class="tabs">
"""
                    # Crear botones de tabs
                    for idx, prod in enumerate(productos_ordenados):
                        active = "active" if idx == 0 else ""
                        html_content += f"<button class='tab-btn {active}' onclick=\"openTab(event, 'tab_{idx}')\">{prod}</button>"
                    
                    html_content += "</div>"
                    
                    # Contenido de tabs
                    for idx, prod in enumerate(productos_ordenados):
                        display = "block" if idx == 0 else "none"
                        html_content += f"<div id='tab_{idx}' class='tab-content' style='display: {display};'><h3>{prod}</h3><div id='chart_{idx}'></div></div>"

                    # SCRIPT JAVASCRIPT
                    html_content += """
    </div>
    <script>
        function openTab(evt, tabName) {
            var i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tab-content");
            for (i = 0; i < tabcontent.length; i++) { tabcontent[i].style.display = "none"; }
            tablinks = document.getElementsByClassName("tab-btn");
            for (i = 0; i < tablinks.length; i++) { tablinks[i].className = tablinks[i].className.replace(" active", ""); }
            document.getElementById(tabName).style.display = "block";
            evt.currentTarget.className += " active";
        }
"""
                    
                    # --- INYECCIÓN DE GRÁFICOS (AQUÍ ESTÁ LA MAGIA) ---
                    
                    # 1. Gráficos Generales
                    json_ton = fig_ton_general.to_json()
                    json_cump = fig_cumplimiento.to_json()
                    html_content += f"""
        var data_ton = {json_ton};
        Plotly.newPlot('grafico_toneladas', data_ton.data, data_ton.layout);
        
        var data_cump = {json_cump};
        Plotly.newPlot('grafico_cumplimiento', data_cump.data, data_cump.layout);
"""

                    # 2. Gráficos por Producto
                    for idx, prod in enumerate(productos_ordenados):
                        df_p = df_dia[df_dia['Producto'] == prod]
                        t_p, t_r = df_p['Ton_Prog'].sum(), df_p['Ton_Real'].sum()
                        
                        # Creamos figura simple para el reporte
                        fig_simple = go.Figure()
                        fig_simple.add_trace(go.Bar(name='Prog', x=['Toneladas'], y=[t_p], marker_color='#A8D5BA'))
                        fig_simple.add_trace(go.Bar(name='Real', x=['Toneladas'], y=[t_r], marker_color='#2E7D32'))
                        fig_simple.update_layout(title=f"Balance {prod}", height=350, barmode='group')
                        
                        json_prod = fig_simple.to_json()
                        html_content += f"var d_{idx} = {json_prod}; Plotly.newPlot('chart_{idx}', d_{idx}.data, d_{idx}.layout);\n"

                    html_content += """
    </script>
</body>
</html>
"""
                    
                    # Descargar
                    b64 = base64.b64encode(html_content.encode()).decode()
                    href = f'<a href="data:text/html;base64,{b64}" download="Reporte_{fecha_sel}.html" style="text-decoration:none; display:inline-block; padding:10px 20px; background-color:#2E7D32; color:white; border-radius:5px;">📥 Descargar HTML Completo</a>'
                    st.markdown(href, unsafe_allow_html=True)

        with col_exp2:
            st.button("Generar Texto de Correo", disabled=True, help="Funcionalidad simplificada para este ejemplo")
            st.info("Para generar el correo, usa el HTML descargado que contiene toda la información.")

    except Exception as e:
        st.error(f"Ocurrió un error: {e}")
        st.write(e)
else:
    st.info("👆 Por favor carga el archivo Excel para comenzar.")
