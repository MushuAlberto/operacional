import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Reporte Priorizado SLIT", layout="wide")

st.title("📊 Dashboard de Despachos por Producto")
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
        st.header(f"📊 RESUMEN GENERAL DE LA JORNADA")
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
        st.markdown("### 📈 Indicadores Generales")
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
        st.markdown("### 📊 Comparativa por Producto")
        
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
                yaxis_title="Toneladas",
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
                yaxis_title="Cumplimiento (%)",
                showlegend=False
            )
            st.plotly_chart(fig_cumplimiento, use_container_width=True)
        
        # Ranking de Productos
        st.markdown("### 🏆 Ranking de Productos")
        
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
        # SECCIÓN 2: DETALLES POR PRODUCTO
        # ========================================
        st.header("📦 DETALLES POR PRODUCTO")
        st.markdown("---")
        
        for prod in productos_ordenados:
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

            # Cabecera del producto
            if prod == "SLIT":
                st.markdown(f"## 🔵 {prod}")
                st.markdown("**Producto Prioritario**")
            else:
                st.markdown(f"## 📦 {prod}")
            
            # Métricas del producto
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Destino Principal", destino_principal)
            
            with col2:
                delta_ton = t_real - t_prog
                st.metric("Tonelaje Real", f"{t_real:,.0f}", f"{delta_ton:+,.0f}")
            
            with col3:
                st.metric("Cumplimiento", f"{cumplimiento:.1f}%", f"{cumplimiento - 100:.1f}%")
            
            with col4:
                st.metric("Regulación Real", f"{reg_promedio:.1f}%")
            
            # Gráfico Combinado (Barras + Líneas)
            fig_combinado = go.Figure()
            
            # Barras para Toneladas
            fig_combinado.add_trace(go.Bar(
                name='Ton. Real',
                x=['Toneladas'],
                y=[t_real],
                marker_color='#2E7D32',
                text=[f"{t_real:,.0f}"],
                textposition='outside',
                yaxis='y',
                offsetgroup=0
            ))
            
            fig_combinado.add_trace(go.Bar(
                name='Ton. Planificado',
                x=['Toneladas'],
                y=[t_prog],
                marker_color='#A8D5BA',
                text=[f"{t_prog:,.0f}"],
                textposition='outside',
                yaxis='y',
                offsetgroup=0
            ))
            
            # Líneas para Equipos
            fig_combinado.add_trace(go.Scatter(
                name='Equipos Reales',
                x=['Equipos'],
                y=[e_real],
                mode='lines+markers+text',
                line=dict(color='#2F5597', width=3),
                marker=dict(size=12, color='#2F5597'),
                text=[f"{e_real:.0f}"],
                textposition='top center',
                yaxis='y2'
            ))
            
            fig_combinado.add_trace(go.Scatter(
                name='Equipos Planificados',
                x=['Equipos'],
                y=[e_prog],
                mode='lines+markers+text',
                line=dict(color='#BDD7EE', width=3, dash='dash'),
                marker=dict(size=12, color='#BDD7EE'),
                text=[f"{e_prog:.0f}"],
                textposition='top center',
                yaxis='y2'
            ))
            
            fig_combinado.update_layout(
                title=f"Comparativa {prod}: Toneladas (Barras) vs Equipos (Líneas)",
                height=400,
                margin=dict(t=60, b=40, l=60, r=80),
                xaxis=dict(
                    domain=[0, 0.45],
                    anchor='y',
                    title=""
                ),
                xaxis2=dict(
                    domain=[0.55, 1],
                    anchor='y2',
                    title=""
                ),
                yaxis=dict(
                    title="Toneladas",
                    side='left',
                    showgrid=True
                ),
                yaxis2=dict(
                    title="Equipos",
                    side='right',
                    overlaying='y',
                    showgrid=False
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5
                ),
                plot_bgcolor='rgba(240,240,240,0.2)',
                barmode='group',
                bargap=0.3
            )
            
            fig_combinado.update_traces(
                selector=dict(type='scatter'),
                xaxis='x2'
            )
            
            st.plotly_chart(fig_combinado, use_container_width=True)
            
            st.markdown("---")
            st.markdown("<br>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Error en el procesamiento: {e}")
        with st.expander("Ver detalles del error"):
            import traceback
            st.code(traceback.format_exc())

else:
    st.info("👋 **Bienvenido al Dashboard de Despachos**")
    st.markdown("""
    ### 📋 Instrucciones:
    1. Sube el archivo Excel (.xlsm) usando el botón de arriba
    2. Selecciona la fecha a analizar en la barra lateral
    3. Explora el resumen general y los detalles por producto
    
    ### ✨ Características:
    - 📊 Resumen general con KPIs consolidados
    - 🏆 Ranking de productos por desempeño
    - 📈 Gráficos comparativos interactivos
    - 🔵 Priorización automática de SLIT
    - 📦 Detalles individuales por producto
    """)
