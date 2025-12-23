import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import base64
from io import BytesIO

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Reporte Priorizado SLIT", layout="wide")

st.title("Dashboard de Despachos por Producto")

# Botones de exportación en la parte superior
col_export1, col_export2, col_export3 = st.columns([1, 1, 2])

with col_export1:
    generar_html = st.button("Generar Reporte HTML Interactivo", type="primary", use_container_width=True)

with col_export2:
    generar_correo = st.button("Generar Texto de Correo", use_container_width=True)

st.markdown("---")

file_tablero = st.file_uploader("Cargar 03.- Tablero Despachos (.xlsm)", type=["xlsm"])

if file_tablero:
    try:
        # 1. Carga de datos
        cols_idx = [1, 31, 32, 33, 34, 35, 36, 46]
        df = pd.read_excel(file_tablero, sheet_name="Base de Datos", usecols=cols_idx, engine='openpyxl')
        df.columns = ['Fecha', 'Producto', 'Destino', 'Ton_Prog', 'Ton_Real', 'Eq_Prog', 'Eq_Real', 'Regulacion_Real']
        
        # Limpieza de datos
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce').dt.date
        df = df.dropna(subset=['Fecha'])
        df['Producto'] = df['Producto'].astype(str).str.upper().str.strip()
        df['Destino'] = df['Destino'].astype(str).str.strip()
        
        # Asegurar tipos numéricos
        cols_num = ['Ton_Prog', 'Ton_Real', 'Eq_Prog', 'Eq_Real', 'Regulacion_Real']
        for col in cols_num:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

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
        st.header(f"RESUMEN EJECUTIVO DE LA JORNADA")
        
        # --- INICIO: SECCIÓN DE IMÁGENES LOGOS (LOCALES) ---
        col_img1, col_img2, col_espacio = st.columns([1, 2, 4])
        
        with col_img1:
            # Intenta cargar la imagen local, si falla no muestra error crítico
            try:
                st.image("logoSQM-li-90.png", width=120)
            except:
                st.warning("No se encontró logoSQM-li-90.png")
            
        with col_img2:
            try:
                st.image("Image20240314124309.png", width=250)
            except:
                st.warning("No se encontró Image20240314124309.png")
        # --- FIN: SECCIÓN DE IMÁGENES LOGOS ---
        
        st.subheader(f"📅 {fecha_sel.strftime('%d-%m-%Y')}")
        st.markdown("---")
        
        # Calcular totales
        total_ton_prog = df_dia['Ton_Prog'].sum()
        total_ton_real = df_dia['Ton_Real'].sum()
        total_eq_prog = df_dia['Eq_Prog'].sum()
        total_eq_real = df_dia['Eq_Real'].sum()
        cumplimiento_general = (total_ton_real / total_ton_prog * 100) if total_ton_prog > 0 else 0
        num_productos = len(productos_ordenados)
        
        # KPIs Totales
        st.markdown("### Indicadores Generales")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Tonelaje Total Real",
                f"{total_ton_real:,.0f}",
                f"{total_ton_real - total_ton_prog:,.0f} vs Prog"
            )
        
        with col2:
            st.metric(
                "Equipos Total Real",
                f"{total_eq_real:.0f}",
                f"{total_eq_real - total_eq_prog:.0f} vs Prog"
            )
        
        with col3:
            st.metric(
                "Cumplimiento General",
                f"{cumplimiento_general:.1f}%",
                f"{cumplimiento_general - 100:.1f}%"
            )
        
        with col4:
            st.metric(
                "Productos Despachados",
                f"{num_productos}"
            )
        
        with col5:
            regulacion_general = df_dia['Regulacion_Real'].mean() * 100
            st.metric(
                "Regulación Promedio",
                f"{regulacion_general:.1f}%"
            )
        
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
        
        # Gráfico Comparativo General
        st.markdown("### Comparativa por Producto")
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            # Gráfico de barras agrupadas - Toneladas
            fig_ton_general = go.Figure()
            fig_ton_general.add_trace(go.Bar(
                name='Ton. Programado',
                x=df_resumen['Producto'],
                y=df_resumen['Ton_Prog'],
                marker_color='#A8D5BA',
                text=df_resumen['Ton_Prog'].apply(lambda x: f"{x:,.0f}"),
                textposition='outside'
            ))
            fig_ton_general.add_trace(go.Bar(
                name='Ton. Real',
                x=df_resumen['Producto'],
                y=df_resumen['Ton_Real'],
                marker_color='#2E7D32',
                text=df_resumen['Ton_Real'].apply(lambda x: f"{x:,.0f}"),
                textposition='outside'
            ))
            fig_ton_general.update_layout(
                title="Toneladas por Producto",
                barmode='group',
                height=400,
                xaxis_title="",
                yaxis=dict(title=dict(text="Toneladas")),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_ton_general, use_container_width=True)
        
        with col_g2:
            # Gráfico de cumplimiento
            fig_cumplimiento = go.Figure()
            
            colores_cumplimiento = ['#2E7D32' if c >= 100 else '#FFA726' if c >= 90 else '#EF5350' 
                                   for c in df_resumen['Cumplimiento']]
            
            fig_cumplimiento.add_trace(go.Bar(
                x=df_resumen['Producto'],
                y=df_resumen['Cumplimiento'],
                marker_color=colores_cumplimiento,
                text=df_resumen['Cumplimiento'].apply(lambda x: f"{x:.1f}%"),
                textposition='outside'
            ))
            
            # Línea de referencia en 100%
            fig_cumplimiento.add_hline(y=100, line_dash="dash", line_color="gray", 
                                      annotation_text="Meta 100%", annotation_position="right")
            
            fig_cumplimiento.update_layout(
                title="% Cumplimiento por Producto",
                height=400,
                xaxis_title="",
                yaxis=dict(title=dict(text="Cumplimiento (%)")),
                showlegend=False
            )
            st.plotly_chart(fig_cumplimiento, use_container_width=True)
        
        # Ranking de Productos
        st.markdown("### Ranking de Productos")
        
        df_ranking = df_resumen.copy()
        df_ranking['Diferencia'] = df_ranking['Ton_Real'] - df_ranking['Ton_Prog']
        df_ranking = df_ranking.sort_values('Ton_Real', ascending=False)
        
        # Formatear tabla
        df_ranking_display = df_ranking.copy()
        df_ranking_display['Ton_Prog'] = df_ranking_display['Ton_Prog'].apply(lambda x: f"{x:,.0f}")
        df_ranking_display['Ton_Real'] = df_ranking_display['Ton_Real'].apply(lambda x: f"{x:,.0f}")
        df_ranking_display['Eq_Prog'] = df_ranking_display['Eq_Prog'].apply(lambda x: f"{x:.0f}")
        df_ranking_display['Eq_Real'] = df_ranking_display['Eq_Real'].apply(lambda x: f"{x:.0f}")
        df_ranking_display['Cumplimiento'] = df_ranking_display['Cumplimiento'].apply(lambda x: f"{x:.1f}%")
        df_ranking_display['Diferencia'] = df_ranking_display['Diferencia'].apply(lambda x: f"{x:+,.0f}")
        
        st.dataframe(
            df_ranking_display[['Producto', 'Ton_Prog', 'Ton_Real', 'Diferencia', 'Eq_Prog', 'Eq_Real', 'Cumplimiento']],
            use_container_width=True,
            hide_index=True
        )
        
        st.markdown("---")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # ========================================
        # SECCIÓN 2: DETALLES POR PRODUCTO (TABS)
        # ========================================
        st.header("DETALLES POR PRODUCTO")
        st.markdown("Seleccione un producto para ver su análisis detallado")
        
        # Crear tabs dinámicos
        tab_names = []
        for prod in productos_ordenados:
            if prod == "SLIT":
                tab_names.append(f"{prod}")
            else:
                tab_names.append(f"{prod}")
        
        tabs = st.tabs(tab_names)
        
        # Contenido de cada tab
        for idx, prod in enumerate(productos_ordenados):
            with tabs[idx]:
                df_p = df_dia[df_dia['Producto'] == prod]
                
                # Métricas
                t_prog = df_p['Ton_Prog'].sum()
                t_real = df_p['Ton_Real'].sum()
                e_prog = df_p['Eq_Prog'].sum()
                e_real = df_p['Eq_Real'].sum()
                cumplimiento = (t_real / t_prog * 100) if t_prog > 0 else 0
                reg_promedio = df_p['Regulacion_Real'].mean() * 100
                
                # Destino principal
                destino_principal = df_p.loc[df_p['Ton_Real'].idxmax(), 'Destino'] if not df_p.empty else "N/A"
                num_viajes = len(df_p)
                
                # Header del producto
                if prod == "SLIT":
                    st.markdown("### PRODUCTO PRIORITARIO")
                else:
                    st.markdown(f"### Análisis de {prod}")
                
                st.markdown("---")
                
                # KPIs en cards grandes
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    delta_ton = t_real - t_prog
                    delta_color = "normal" if abs(delta_ton) < (t_prog * 0.05) else ("inverse" if delta_ton < 0 else "normal")
                    st.metric(
                        "Tonelaje Real",
                        f"{t_real:,.0f} Ton",
                        f"{delta_ton:+,.0f} vs Prog",
                        delta_color=delta_color
                    )
                
                with col2:
                    delta_eq = e_real - e_prog
                    st.metric(
                        "Equipos Real",
                        f"{e_real:.0f}",
                        f"{delta_eq:+.0f} vs Prog"
                    )
                
                with col3:
                    cumpl_status = "normal" if cumplimiento >= 95 else "inverse"
                    st.metric(
                        "Cumplimiento",
                        f"{cumplimiento:.1f}%",
                        f"{cumplimiento - 100:.1f}%",
                        delta_color=cumpl_status
                    )
                
                with col4:
                    st.metric(
                        "Destino Principal",
                        destino_principal,
                        f"{num_viajes} viajes"
                    )
                
                st.markdown("---")
                
                # Sección de gráficos
                col_chart1, col_chart2 = st.columns([3, 2])
                
                with col_chart1:
                    # Gráfico Combinado (Barras AGRUPADAS + Líneas)
                    from plotly.subplots import make_subplots
                    
                    fig_combinado = make_subplots(
                        rows=1, cols=2,
                        column_widths=[0.45, 0.45],
                        specs=[[{"secondary_y": False}, {"secondary_y": True}]],
                        subplot_titles=("Toneladas", "Equipos"),
                        horizontal_spacing=0.15
                    )
                    
                    # Barras para Toneladas Planificadas (subplot 1)
                    fig_combinado.add_trace(
                        go.Bar(
                            name='Ton. Planificado',
                            x=[''],
                            y=[t_prog],
                            marker_color='#A8D5BA',
                            text=[f"{t_prog:,.0f}"],
                            textposition='outside',
                            showlegend=True
                        ),
                        row=1, col=1
                    )
                    
                    # Barras para Toneladas Reales (subplot 1)
                    fig_combinado.add_trace(
                        go.Bar(
                            name='Ton. Real',
                            x=[''],
                            y=[t_real],
                            marker_color='#2E7D32',
                            text=[f"{t_real:,.0f}"],
                            textposition='outside',
                            showlegend=True
                        ),
                        row=1, col=1
                    )
                    
                    # Líneas para Equipos
                    fig_combinado.add_trace(go.Scatter(
                        name='Equipos Reales',
                        x=['Equipos'],
                        y=[e_real],
                        mode='lines+markers+text',
                        line=dict(color='#2F5597', width=4),
                        marker=dict(size=15, color='#2F5597'),
                        text=[f"{e_real:.0f}"],
                        textposition='top center',
                        textfont=dict(size=14, color='#2F5597'),
                        yaxis='y2'
                    ))
                    
                    fig_combinado.add_trace(go.Scatter(
                        name='Equipos Planificados',
                        x=['Equipos'],
                        y=[e_prog],
                        mode='lines+markers+text',
                        line=dict(color='#BDD7EE', width=4, dash='dash'),
                        marker=dict(size=15, color='#BDD7EE', line=dict(width=2, color='#2F5597')),
                        text=[f"{e_prog:.0f}"],
                        textposition='top center',
                        textfont=dict(size=14, color='#2F5597'),
                        yaxis='y2'
                    ))
                    
                    fig_combinado.update_layout(
                        title=dict(
                            text=f"<b>Comparativa Toneladas vs Equipos</b>",
                            font=dict(size=16)
                        ),
                        height=500,
                        margin=dict(t=80, b=50, l=70, r=90),
                        xaxis=dict(
                            domain=[0, 0.42],
                            anchor='y',
                            title="",
                            tickfont=dict(size=14)
                        ),
                        xaxis2=dict(
                            domain=[0.58, 1],
                            anchor='y2',
                            title="",
                            tickfont=dict(size=14)
                        ),
                        yaxis=dict(
                            title=dict(text="Toneladas", font=dict(size=14)),
                            side='left',
                            showgrid=True,
                            gridcolor='rgba(200,200,200,0.3)',
                            tickfont=dict(size=12)
                        ),
                        yaxis2=dict(
                            title=dict(text="Equipos", font=dict(size=14)),
                            side='right',
                            overlaying='y',
                            showgrid=False,
                            rangemode="tozero", # <--- MEJORA: Eje comienza en 0
                            tickfont=dict(size=12)
                        ),
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="center",
                            x=0.5,
                            font=dict(size=12)
                        ),
                        plot_bgcolor='rgba(240,245,250,0.5)',
                        paper_bgcolor='white',
                        barmode='group',
                        bargap=0.2
                    )
                    
                    fig_combinado.update_traces(
                        selector=dict(type='scatter'),
                        xaxis='x2'
                    )
                    
                    st.plotly_chart(fig_combinado, use_container_width=True)
                
                with col_chart2:
                    # Indicadores adicionales
                    st.markdown("#### Indicadores Adicionales")
                    
                    # Regulación
                    st.metric("Regulación Real Promedio", f"{reg_promedio:.2f}%")
                    
                    # Eficiencia (ton por equipo)
                    eficiencia = t_real / e_real if e_real > 0 else 0
                    st.metric("Productividad de Carga", f"{eficiencia:.1f} Ton/Equipo")
                    
                    # Desviación
                    desviacion_ton = ((t_real - t_prog) / t_prog * 100) if t_prog > 0 else 0
                    st.metric("Desviación Tonelaje", f"{desviacion_ton:+.1f}%")
                    
                    st.markdown("---")
                    
                    # Alertas o estados
                    st.markdown("#### 🚦 Estado del Producto")
                    
                    if cumplimiento >= 100:
                        st.success("✅ Cumplimiento alcanzado")
                    elif cumplimiento >= 90:
                        st.warning("⚠️ Cumplimiento en rango aceptable")
                    else:
                        st.error("🔴 Bajo cumplimiento - Requiere atención")
                    
                    if abs(desviacion_ton) > 10:
                        st.info(f"📊 Desviación significativa: {desviacion_ton:+.1f}%")
                
                st.markdown("---")
                
                # Tabla de despachos detallada
                st.markdown("#### Despachos por Destino")
                
                df_destinos = df_p.groupby('Destino').agg({
                    'Ton_Prog': 'sum',
                    'Ton_Real': 'sum',
                    'Eq_Prog': 'sum',
                    'Eq_Real': 'sum',
                    'Fecha': 'count'
                }).rename(columns={'Fecha': 'Viajes'}).reset_index()
                
                df_destinos['Cumplimiento'] = (df_destinos['Ton_Real'] / df_destinos['Ton_Prog'] * 100).fillna(0)
                df_destinos = df_destinos.sort_values('Ton_Real', ascending=False)
                
                # Formatear para display
                df_destinos_display = df_destinos.copy()
                df_destinos_display['Ton_Prog'] = df_destinos_display['Ton_Prog'].apply(lambda x: f"{x:,.1f}")
                df_destinos_display['Ton_Real'] = df_destinos_display['Ton_Real'].apply(lambda x: f"{x:,.1f}")
                df_destinos_display['Eq_Prog'] = df_destinos_display['Eq_Prog'].apply(lambda x: f"{x:.0f}")
                df_destinos_display['Eq_Real'] = df_destinos_display['Eq_Real'].apply(lambda x: f"{x:.0f}")
                df_destinos_display['Cumplimiento'] = df_destinos_display['Cumplimiento'].apply(lambda x: f"{x:.1f}%")
                
                st.dataframe(
                    df_destinos_display,
                    use_container_width=True,
                    hide_index=True,
                    height=300
                )
        
        # ========================================
        # SECCIÓN 3: GENERACIÓN DE REPORTES
        # ========================================
        
        # Generar HTML Interactivo
        if generar_html:
            with st.spinner("Generando reporte HTML interactivo..."):
                # Crear HTML con todos los gráficos
                # NOTA: Para el reporte HTML descargable, usamos URLs públicas para que funcionen fuera de esta carpeta.
                html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte de Despachos - {fecha_sel.strftime('%d-%m-%Y')}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            border-bottom: 3px solid #2E7D32;
            padding-bottom: 20px;
        }}
        .header h1 {{
            color: #2E7D32;
            font-size: 2.5em;
            margin: 0;
        }}
        .header p {{
            color: #666;
            font-size: 1.2em;
            margin: 10px 0 0 0;
        }}
        .kpi-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .kpi-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }}
        .kpi-card:hover {{
            transform: translateY(-5px);
        }}
        .kpi-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .kpi-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .section {{
            margin: 40px 0;
        }}
        .section-title {{
            font-size: 1.8em;
            color: #333;
            border-left: 5px solid #2E7D32;
            padding-left: 15px;
            margin-bottom: 20px;
        }}
        .tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        .tab {{
            padding: 12px 24px;
            background: #f0f0f0;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s;
        }}
        .tab:hover {{
            background: #e0e0e0;
        }}
        .tab.active {{
            background: #2E7D32;
            color: white;
        }}
        .tab-content {{
            display: none;
            animation: fadeIn 0.5s;
        }}
        .tab-content.active {{
            display: block;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #2E7D32;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .alert {{
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }}
        .alert-success {{
            background: #d4edda;
            color: #155724;
            border-left: 4px solid #28a745;
        }}
        .alert-warning {{
            background: #fff3cd;
            color: #856404;
            border-left: 4px solid #ffc107;
        }}
        .alert-danger {{
            background: #f8d7da;
            color: #721c24;
            border-left: 4px solid #dc3545;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #eee;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="https://logos-world.net/wp-content/uploads/2022/12/SQM-Logo.png" alt="SQM Logo" style="max-height: 80px;">
            <h1>Reporte de Despachos por Producto</h1>
            <p>Fecha: {fecha_sel.strftime('%d de %B de %Y')}</p>
            <p style="font-size: 0.9em; color: #999;">Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
        
        <div class="section">
            <h2 class="section-title">Indicadores Clave</h2>
            <div class="kpi-container">
                <div class="kpi-card">
                    <div class="kpi-label">Tonelaje Total</div>
                    <div class="kpi-value">{total_ton_real:,.0f}</div>
                    <div class="kpi-label">Toneladas</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Equipos Totales</div>
                    <div class="kpi-value">{total_eq_real:.0f}</div>
                    <div class="kpi-label">Equipos</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Cumplimiento</div>
                    <div class="kpi-value">{cumplimiento_general:.1f}%</div>
                    <div class="kpi-label">General</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Productos</div>
                    <div class="kpi-value">{num_productos}</div>
                    <div class="kpi-label">Despachados</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">Gráficos Comparativos</h2>
            <div id="grafico_toneladas"></div>
            <div id="grafico_cumplimiento"></div>
        </div>
        
        <div class="section">
            <h2 class="section-title">Ranking de Productos</h2>
            <table>
                <thead>
                    <tr>
                        <th>Producto</th>
                        <th>Ton. Prog</th>
                        <th>Ton. Real</th>
                        <th>Diferencia</th>
                        <th>Cumplimiento</th>
                    </tr>
                </thead>
                <tbody>
"""
                
                # Agregar filas de la tabla
                for _, row in df_ranking.iterrows():
                    cumpl_color = '#28a745' if row['Cumplimiento'] >= 100 else '#ffc107' if row['Cumplimiento'] >= 90 else '#dc3545'
                    html_content += f"""
                    <tr>
                        <td><strong>{row['Producto']}</strong></td>
                        <td>{row['Ton_Prog']:,.0f}</td>
                        <td>{row['Ton_Real']:,.0f}</td>
                        <td>{row['Diferencia']:+,.0f}</td>
                        <td style="color: {cumpl_color}; font-weight: bold;">{row['Cumplimiento']:.1f}%</td>
                    </tr>
"""
                
                html_content += """
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2 class="section-title">Detalles por Producto</h2>
            <div class="tabs">
"""
                
                # Crear tabs
                for idx, prod in enumerate(productos_ordenados):
                    active_class = "active" if idx == 0 else ""
                    icon = " " if prod == "SLIT" else " "
                    html_content += f'<button class="tab {active_class}" onclick="openTab(event, \'tab{idx}\')">{icon} {prod}</button>\n'
                
                html_content += """
            </div>
"""
                
                # Contenido de cada tab
                for idx, prod in enumerate(productos_ordenados):
                    df_p = df_dia[df_dia['Producto'] == prod]
                    t_prog = df_p['Ton_Prog'].sum()
                    t_real = df_p['Ton_Real'].sum()
                    cumplimiento = (t_real / t_prog * 100) if t_prog > 0 else 0
                    
                    active_class = "active" if idx == 0 else ""
                    
                    # Alerta según cumplimiento
                    if cumplimiento >= 100:
                        alert_class = "alert-success"
                        alert_text = "✅ Cumplimiento alcanzado"
                    elif cumplimiento >= 90:
                        alert_class = "alert-warning"
                        alert_text = "⚠️ Cumplimiento en rango aceptable"
                    else:
                        alert_class = "alert-danger"
                        alert_text = "🔴 Bajo cumplimiento - Requiere atención"
                    
                    html_content += f"""
            <div id="tab{idx}" class="tab-content {active_class}">
                <div class="kpi-container">
                    <div class="kpi-card" style="background: linear-gradient(135deg, #2E7D32 0%, #1B5E20 100%);">
                        <div class="kpi-label">Tonelaje Real</div>
                        <div class="kpi-value">{t_real:,.0f}</div>
                    </div>
                    <div class="kpi-card" style="background: linear-gradient(135deg, #1976D2 0%, #0D47A1 100%);">
                        <div class="kpi-label">Cumplimiento</div>
                        <div class="kpi-value">{cumplimiento:.1f}%</div>
                    </div>
                </div>
                <div class="alert {alert_class}">{alert_text}</div>
                <div id="grafico_producto_{idx}"></div>
            </div>
"""
                
                html_content += """
        </div>
        
        <div class="footer">
            <p><strong>Dashboard de Despachos - SQM</strong></p>
            <p>Reporte generado automáticamente</p>
        </div>
    </div>
    
    <script>
        // Función para cambiar tabs
        function openTab(evt, tabName) {
            var i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tab-content");
            for (i = 0; i < tabcontent.length; i++) {
                tabcontent[i].className = tabcontent[i].className.replace(" active", "");
            }
            tablinks = document.getElementsByClassName("tab");
            for (i = 0; i < tablinks.length; i++) {
                tablinks[i].className = tablinks[i].className.replace(" active", "");
            }
            document.getElementById(tabName).className += " active";
            evt.currentTarget.className += " active";
        }
        
        // Gráfico de toneladas
        var data_ton = {fig_ton_general.to_json()};
        Plotly.newPlot('grafico_toneladas', data_ton.data, data_ton.layout);
        
        // Gráfico de cumplimiento
        var data_cumpl = {fig_cumplimiento.to_json()};
        Plotly.newPlot('grafico_cumplimiento', data_cumpl.data, data_cumpl.layout);
"""
                
                # Agregar gráficos de cada producto
                for idx, prod in enumerate(productos_ordenados):
                    df_p = df_dia[df_dia['Producto'] == prod]
                    t_prog = df_p['Ton_Prog'].sum()
                    t_real = df_p['Ton_Real'].sum()
                    e_prog = df_p['Eq_Prog'].sum()
                    e_real = df_p['Eq_Real'].sum()
                    
                    # Crear gráfico simple para el producto
                    fig_prod = go.Figure()
                    fig_prod.add_trace(go.Bar(name='Ton. Planificado', x=['Toneladas'], y=[t_prog], marker_color='#A8D5BA'))
                    fig_prod.add_trace(go.Bar(name='Ton. Real', x=['Toneladas'], y=[t_real], marker_color='#2E7D32'))
                    fig_prod.update_layout(barmode='group', height=400, title=f"Comparativa {prod}")
                    
                    html_content += f"""
        var data_prod_{idx} = {fig_prod.to_json()};
        Plotly.newPlot('grafico_producto_{idx}', data_prod_{idx}.data, data_prod_{idx}.layout);
"""
                
                html_content += """
    </script>
</body>
</html>
"""
                
                # Descargar HTML
                st.success("Reporte HTML generado exitosamente")
                st.download_button(
                    label="Descargar Reporte HTML Interactivo",
                    data=html_content,
                    file_name=f"reporte_despachos_{fecha_sel.strftime('%Y%m%d')}.html",
                    mime="text/html",
                    type="primary",
                    use_container_width=True
                )
                
                st.info("**Instrucciones:** Descarga el archivo y ábrelo en cualquier navegador. Todos los gráficos son interactivos (zoom, hover, etc.)")
        
        # Generar texto de correo
        if generar_correo:
            with st.spinner("Generando texto de correo..."):
                # Identificar productos con alertas
                productos_alerta = []
                productos_ok = []
                for _, row in df_resumen.iterrows():
                    if row['Cumplimiento'] < 90:
                        productos_alerta.append(f"{row['Producto']} ({row['Cumplimiento']:.1f}%)")
                    elif row['Cumplimiento'] >= 100:
                        productos_ok.append(f"{row['Producto']} ({row['Cumplimiento']:.1f}%)")
                
                correo_texto = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background: #2E7D32; color: white; padding: 20px; border-radius: 5px; }}
        .kpi {{ background: #f5f5f5; padding: 15px; margin: 10px 0; border-left: 4px solid #2E7D32; }}
        .alert {{ background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 15px 0; }}
        .success {{ background: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 15px 0; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background: #2E7D32; color: white; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 2px solid #eee; color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>Reporte de Despachos - {fecha_sel.strftime('%d/%m/%Y')}</h2>
        <p>Resumen Ejecutivo de Operaciones</p>
    </div>
    
    <h3>Resumen Ejecutivo</h3>
    
    <div class="kpi">
        <strong>Tonelaje Total Despachado:</strong> {total_ton_real:,.0f} toneladas<br>
        <strong>Cumplimiento General:</strong> {cumplimiento_general:.1f}%<br>
        <strong>Total de Equipos:</strong> {total_eq_real:.0f} equipos<br>
        <strong>Productos Despachados:</strong> {num_productos}
    </div>
"""
                
                if productos_alerta:
                    correo_texto += f"""
    <div class="alert">
        <strong>⚠️ Productos que Requieren Atención:</strong><br>
        {', '.join(productos_alerta)}
    </div>
"""
                
                if productos_ok:
                    correo_texto += f"""
    <div class="success">
        <strong>✅ Productos con Cumplimiento Alcanzado:</strong><br>
        {', '.join(productos_ok)}
    </div>
"""
                
                correo_texto += """
    <h3>Ranking de Productos</h3>
    <table>
        <thead>
            <tr>
                <th>Producto</th>
                <th>Ton. Real</th>
                <th>Cumplimiento</th>
            </tr>
        </thead>
        <tbody>
"""
                
                for _, row in df_ranking.head(5).iterrows():
                    correo_texto += f"""
            <tr>
                <td>{row['Producto']}</td>
                <td>{row['Ton_Real']:,.0f}</td>
                <td>{row['Cumplimiento']:.1f}%</td>
            </tr>
"""
                
                correo_texto += f"""
        </tbody>
    </table>
    
    <div class="footer">
        <p><strong>📎 Archivos Adjuntos:</strong></p>
        <ul>
            <li>reporte_despachos_{fecha_sel.strftime('%Y%m%d')}.html - Reporte interactivo completo</li>
        </ul>
        <p><em>Para ver el reporte completo con gráficos interactivos, abra el archivo HTML adjunto en su navegador.</em></p>
        <p>Reporte generado automáticamente el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}</p>
    </div>
</body>
</html>
"""
                
                st.success("Texto de correo generado")
                
                # Mostrar preview
                with st.expander("Vista Previa del Correo"):
                    st.markdown(correo_texto, unsafe_allow_html=True)
                
                # Copiar al portapapeles
                st.code(f"""
Asunto: Reporte de Despachos {fecha_sel.strftime('%d/%m/%Y')} - Cumplimiento {cumplimiento_general:.1f}%

[Pegar el HTML generado abajo en el cuerpo del correo]
                """)
                
                st.download_button(
                    label="Descargar HTML del Correo",
                    data=correo_texto,
                    file_name=f"correo_reporte_{fecha_sel.strftime('%Y%m%d')}.html",
                    mime="text/html",
                    use_container_width=True
                )
                
                st.info("""
**Instrucciones de uso:**
1. Copia el texto del asunto
2. En tu cliente de correo, cambia a modo "HTML" o "Texto enriquecido"
3. Pega el contenido HTML descargado
4. Adjunta el archivo HTML interactivo generado anteriormente
5. Envía a gerencia
                """)

    except Exception as e:
        st.error(f"Error en el procesamiento: {e}")
        with st.expander("Ver detalles del error"):
            import traceback
            st.code(traceback.format_exc())

else:
    st.info("**Bienvenido al Dashboard de Despachos**")
    st.markdown("""
    ### Instrucciones:
    1. Sube el archivo Excel (.xlsm) usando el botón de arriba
    2. Selecciona la fecha a analizar en la barra lateral
    3. Explora el resumen general en la primera sección
    4. Navega por los tabs para ver detalles de cada producto
    
    ### Características:
    - **Resumen General**: KPIs consolidados y comparativas
    - **Ranking**: Productos ordenados por desempeño
    - **Tabs por Producto**: Navegación rápida y limpia
    - **SLIT Prioritario**: Identificado claramente
    - **Gráficos Interactivos**: Barras y líneas combinadas
    - **Despachos Detallados**: Por destino en cada producto
    """)

