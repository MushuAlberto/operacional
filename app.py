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
    
    # 1. Título Centrado
    st.markdown(f"<h2 style='text-align: center;'>RESUMEN GENERAL DE LA JORNADA</h2>", unsafe_allow_html=True)
    
    # 2. Logos alineados verticalmente al CENTRO
    col_img_izq, col_espacio, col_img_der = st.columns([2, 6, 3], vertical_alignment="center")
    
    with col_img_izq:
        try:
            st.image("logoSQM-li-90.png", width=120)
        except:
            st.warning("Falta logoSQM")
        
    with col_img_der:
        try:
            st.markdown('<div style="text-align: right;">', unsafe_allow_html=True)
            st.image("Image20240314124309.png", width=250)
            st.markdown('</div>', unsafe_allow_html=True)
        except:
            st.warning("Falta Image2024")
    
    # 3. Fecha Centrada
    st.markdown(f"<h3 style='text-align: center;'>📅 {fecha_sel.strftime('%d-%m-%Y')}</h3>", unsafe_allow_html=True)
    
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
                # Gráfico Combinado (AHORA DOS BARRAS AGRUPADAS)
                fig_combinado = make_subplots(
                    rows=1, cols=2,
                    column_widths=[0.45, 0.45],
                    horizontal_spacing=0.15
                )
                
                # --- Subplot 1: TONELADAS (Barras) ---
                fig_combinado.add_trace(
                    go.Bar(
                        name='Ton. Planificado',
                        x=[''],
                        y=[t_prog],
                        marker_color='#A8D5BA', # Verde claro
                        showlegend=True
                    ),
                    row=1, col=1
                )
                
                fig_combinado.add_trace(
                    go.Bar(
                        name='Ton. Real',
                        x=[''],
                        y=[t_real],
                        marker_color='#2E7D32', # Verde oscuro
                        showlegend=True
                    ),
                    row=1, col=1
                )
                
                # --- Subplot 2: EQUIPOS (Ahora Barras también) ---
                # Equipos Planificados
                fig_combinado.add_trace(go.Bar(
                    name='Eq. Planificado',
                    x=[''],
                    y=[e_prog],
                    marker_color='#BDD7EE', # Azul claro
                    showlegend=True
                ), row=1, col=2)
                
                # Equipos Reales
                fig_combinado.add_trace(go.Bar(
                    name='Eq. Real',
                    x=[''],
                    y=[e_real],
                    marker_color='#2F5597', # Azul oscuro
                    showlegend=True
                ), row=1, col=2)
                
                fig_combinado.update_layout(
                    title=dict(
                        text=f"<b>Comparativa Toneladas vs Equipos</b>",
                        font=dict(size=16)
                    ),
                    height=400,
                    margin=dict(t=80, b=20, l=70, r=90),
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
                
                fig_combinado.update_yaxes(title_text="Toneladas", row=1, col=1, side='left', showgrid=True)
                fig_combinado.update_yaxes(title_text="Equipos", row=1, col=2, side='right', showgrid=False)
                
                st.plotly_chart(fig_combinado, use_container_width=True)

                # --- LEYENDA DETALLADA CON VALORES ---
                st.markdown(f"""
                <div style="display: flex; justify-content: center; gap: 20px; margin-top: 5px;">
                    <!-- Box Toneladas -->
                    <div style="background-color: #f0f7f0; padding: 10px; border-radius: 8px; border-left: 5px solid #2E7D32; width: 48%;">
                        <strong style="color: #2E7D32; font-size: 1.1em;">TONELADAS</strong><br>
                        <span style="color: #A8D5BA;">■</span> Planificado: <strong>{t_prog:,.0f}</strong><br>
                        <span style="color: #2E7D32;">■</span> Real: <strong>{t_real:,.0f}</strong> 
                        <span style="font-size: 0.9em; color: {'#d32f2f' if (t_real-t_prog) < 0 else '#388e3c'};">({t_real-t_prog:+,.0f})</span>
                    </div>
                    <!-- Box Equipos -->
                    <div style="background-color: #f0f4f8; padding: 10px; border-radius: 8px; border-left: 5px solid #2F5597; width: 48%;">
                        <strong style="color: #2F5597; font-size: 1.1em;">EQUIPOS</strong><br>
                        <span style="color: #BDD7EE;">■</span> Planificado: <strong>{e_prog:.0f}</strong><br>
                        <span style="color: #2F5597;">■</span> Real: <strong>{e_real:.0f}</strong>
                        <span style="font-size: 0.9em; color: {'#d32f2f' if (e_real-e_prog) < 0 else '#1976D2'};">({e_real-e_prog:+.0f})</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_chart2:
                # Indicadores adicionales
                st.markdown("#### Indicadores Adicionales")
                
                # Regulación
                st.metric("Regulación Real Promedio", f"{reg_promedio:.2f}%")
                
                # Eficiencia (ton por equipo)
                eficiencia = t_real / e_real if e_real > 0 else 0
                st.metric("Promedio de Carga", f"{eficiencia:.1f} Ton/Equipo")
                
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
                    st.info(f"Desviación significativa: {desviacion_ton:+.1f}%")
            
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
    
    st.markdown("---")
    st.markdown("<h3 style='text-align: center;'>Exportar Reportes</h3>", unsafe_allow_html=True)
    
    # Botones de exportación en la parte INFERIOR
    col_export1, col_export2, col_export3 = st.columns([1, 1, 2])
    
    with col_export1:
        generar_html = st.button("Generar Reporte HTML Interactivo", type="primary", use_container_width=True)
    
    with col_export2:
        generar_correo = st.button("Generar Texto de Correo", use_container_width=True)
    
    # Generar HTML Interactivo
    if generar_html:
        with st.spinner("Generando reporte HTML interactivo..."):
            # Crear HTML con todos los gráficos
            # NOTA: Para el reporte HTML descargable, usamos URLs públicas para que funcionen fuera de esta carpeta.
            html_content = f"""
