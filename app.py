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
        
        # Limpieza de fechas y textos (Uso de .str para evitar error de 'Series')
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

            # Layout de Gráficos
            g1, g2 = st.columns(2)
            
            with g1:
                fig_ton = go.Figure()
                fig_ton.add_trace(go.Bar(x=['Tonelaje'], y=[t_prog], name='Prog', marker_color='#A8D5BA', text=[f"{t_prog:,.0f}"], textposition='auto'))
                fig_ton.add_trace(go.Bar(x=['Tonelaje'], y=[t_real], name='Real', marker_color='#2E7D32', text=[f"{t_real:,.0f}"], textposition='auto'))
                fig_ton.update_layout(title="Comparativa Toneladas", barmode='group', height=280, margin=dict(t=30, b=0))
                st.plotly_chart(fig_ton, use_container_width=True)

            with g2:
                fig_eq = go.Figure()
                fig_eq.add_trace(go.Bar(x=['Equipos'], y=[e_prog], name='Prog', marker_color='#BDD7EE', text=[f"{e_prog:.0f}"], textposition='auto'))
                fig_eq.add_trace(go.Bar(x=['Equipos'], y=[e_real], name='Real', marker_color='#2F5597', text=[f"{e_real:.0f}"], textposition='auto'))
                fig_eq.update_layout(title="Comparativa Equipos", barmode='group', height=280, margin=dict(t=30, b=0))
                st.plotly_chart(fig_eq, use_container_width=True)
            
            st.divider()

    except Exception as e:
        st.error(f"Error en el procesamiento: {e}")
