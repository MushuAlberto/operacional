import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Reporte Priorizado SLIT", layout="wide")

st.title("📊 Despachos Detallados por Producto (Priorizado SLIT)")
st.markdown("---")

file_tablero = st.file_uploader("Cargar 03.- Tablero Despachos (.xlsm)", type=["xlsm"])

if file_tablero:
    try:
        # 1. Carga de datos (Columnas B, AF, AG, AH, AI, AJ, AK, AU)
        cols_idx = [1, 31, 32, 33, 34, 35, 36, 46]
        df = pd.read_excel(file_tablero, sheet_name="Base de Datos", usecols=cols_idx, engine='openpyxl')
        df.columns = ['Fecha', 'Producto', 'Destino', 'Ton_Prog', 'Ton_Real', 'Eq_Prog', 'Eq_Real', 'Regulacion_Real']
        
        # Limpieza de fechas y textos
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce').dt.date
        df = df.dropna(subset=['Fecha'])
        df['Producto'] = df['Producto'].astype(str).str.upper().str.strip()
        df['Destino'] = df['Destino'].astype(str).str.strip()

        # 2. Selección de Fecha
        fechas_disp = sorted(df['Fecha'].unique(), reverse=True)
        fecha_sel = st.sidebar.selectbox("Seleccione la Fecha", fechas_disp)
        
        df_dia = df[df['Fecha'] == fecha_sel]
        
        # --- LÓGICA DE PRIORIZACIÓN DE SLIT ---
        productos_nombres = sorted(df_dia['Producto'].unique())
        
        # Si SLIT está en la lista, lo movemos al índice 0
        if "SLIT" in productos_nombres:
            productos_nombres.remove("SLIT")
            productos_ordenados = ["SLIT"] + productos_nombres
        else:
            productos_ordenados = productos_nombres

        st.header(f"📅 Jornada: {fecha_sel.strftime('%d-%m-%Y')}")
        
        # 3. Renderizado en el orden definido
        for prod in productos_ordenados:
            df_p = df_dia[df_dia['Producto'] == prod]
            
            # Métricas
            t_prog = df_p['Ton_Prog'].sum()
            t_real = df_p['Ton_Real'].sum()
            e_prog = df_p['Eq_Prog'].sum()
            e_real = df_p['Eq_Real'].sum()
            cumplimiento = (t_real / t_prog * 100) if t_prog > 0 else 0
            reg_promedio = df_p['Regulacion_Real'].mean() * 100
            
            # Destino principal (por volumen)
            destino_principal = df_p.loc[df_p['Ton_Real'].idxmax(), 'Destino'] if not df_p.empty else "N/A"

            # Color especial para la cabecera si es SLIT
            header_color = "🔵" if prod == "SLIT" else "📦"
            st.subheader(f"{header_color} Producto: {prod}")
            
            # Layout de Tarjetas
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                st.caption("📍 Destino Principal")
                st.markdown(f"**{destino_principal}**")
            with c2:
                st.caption("Cumplimiento Día")
                st.markdown(f"### {cumplimiento:.1f}%")
            with c3:
                st.caption("% Regulación Real")
                st.markdown(f"### {reg_promedio:.1f}%")

            # Gráfico Combinado (Barras para Toneladas + Líneas para Equipos)
            fig_combinado = go.Figure()
            
            # Barras para Toneladas Programadas
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
            
            # Barras para Toneladas Reales
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
            
            # Línea para Equipos Reales
            fig_combinado.add_trace(go.Scatter(
                name='Equipos Reales',
                x=['Equipos'],
                y=[e_real],
                mode='lines+markers+text',
                line=dict(color='#2F5597', width=3),
                marker=dict(size=10, color='#2F5597'),
                text=[f"{e_real:.0f}"],
                textposition='top center',
                yaxis='y2'
            ))
            
            # Línea para Equipos Planificados
            fig_combinado.add_trace(go.Scatter(
                name='Equipos Planificados',
                x=['Equipos'],
                y=[e_prog],
                mode='lines+markers+text',
                line=dict(color='#BDD7EE', width=3, dash='dash'),
                marker=dict(size=10, color='#BDD7EE'),
                text=[f"{e_prog:.0f}"],
                textposition='top center',
                yaxis='y2'
            ))
            
            fig_combinado.update_layout(
                title="Comparativa Toneladas (Barras) vs Equipos (Líneas)",
                height=450,
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
            
            # Actualizar trazos para usar el eje X correcto
            fig_combinado.update_traces(
                selector=dict(type='scatter'),
                xaxis='x2'
            )
            
            st.plotly_chart(fig_combinado, use_container_width=True)
            
            st.divider()

    except Exception as e:
        st.error(f"Error en el procesamiento: {e}")
