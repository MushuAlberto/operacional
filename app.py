import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Reporte Detallado por Producto", layout="wide")

st.title("📊 Despachos Detallados por Producto")
st.markdown("---")

file_tablero = st.file_uploader("Cargar 03.- Tablero Despachos (.xlsm)", type=["xlsm"])

if file_tablero:
    try:
        # 1. Carga de datos
        # Columnas: B=1, AF=31, AG=32, AH=33, AI=34, AJ=35, AK=36, AU=46
        cols_idx = [1, 31, 32, 33, 34, 35, 36, 46]
        df = pd.read_excel(file_tablero, sheet_name="Base de Datos", usecols=cols_idx, engine='openpyxl')
        df.columns = ['Fecha', 'Producto', 'Destino', 'Ton_Prog', 'Ton_Real', 'Eq_Prog', 'Eq_Real', 'Regulacion_Real']
        
        # CORRECCIÓN DE ERROR DE FECHA: Usar format='mixed' y dayfirst
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce').dt.date
        df = df.dropna(subset=['Fecha'])
        
        # CORRECCIÓN DE ERROR 'strip': Usar .str.strip() correctamente
        df['Producto'] = df['Producto'].astype(str).str.upper().str.strip()
        df['Destino'] = df['Destino'].astype(str).str.strip()

        # 2. Selección de Fecha
        fechas_disp = sorted(df['Fecha'].unique(), reverse=True)
        fecha_sel = st.sidebar.selectbox("Seleccione la Fecha", fechas_disp)
        
        # Filtrar datos del día
        df_dia = df[df['Fecha'] == fecha_sel]
        productos_del_dia = sorted(df_dia['Producto'].unique())

        st.header(f"📅 Jornada: {fecha_sel.strftime('%d-%m-%Y')}")
        st.write(f"Total de productos el día de hoy: **{len(productos_del_dia)}**")

        # 3. Generar Dashboard por cada producto
        for prod in productos_del_dia:
            df_p = df_dia[df_dia['Producto'] == prod]
            
            # Sumatorias por producto
            t_prog = df_p['Ton_Prog'].sum()
            t_real = df_p['Ton_Real'].sum()
            e_prog = df_p['Eq_Prog'].sum()
            e_real = df_p['Eq_Real'].sum()
            cumplimiento = (t_real / t_prog * 100) if t_prog > 0 else 0
            reg_promedio = df_p['Regulacion_Real'].mean() * 100
            
            # Obtener el destino que tuvo más carga real
            id_max = df_p['Ton_Real'].idxmax()
            destino_principal = df_p.loc[id_max, 'Destino']

            # --- RENDERIZADO VISUAL ---
            with st.container():
                st.subheader(f"Producto: {prod}")
                
                # Fila de Tarjetas (Métricas)
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

                # Fila de Gráficos Comparativos
                g1, g2 = st.columns(2)
                
                with g1:
                    fig_ton = go.Figure()
                    fig_ton.add_trace(go.Bar(x=['Tonelaje'], y=[t_prog], name='Prog', marker_color='#A8D5BA', text=[f"{t_prog:,.0f}"], textposition='auto'))
                    fig_ton.add_trace(go.Bar(x=['Tonelaje'], y=[t_real], name='Real', marker_color='#2E7D32', text=[f"{t_real:,.0f}"], textposition='auto'))
                    fig_ton.update_layout(title="Comparativa Toneladas", barmode='group', height=300, margin=dict(t=30, b=0))
                    st.plotly_chart(fig_ton, use_container_width=True)

                with g2:
                    fig_eq = go.Figure()
                    fig_eq.add_trace(go.Bar(x=['Equipos'], y=[e_prog], name='Prog', marker_color='#BDD7EE', text=[f"{e_prog:.0f}"], textposition='auto'))
                    fig_eq.add_trace(go.Bar(x=['Equipos'], y=[e_real], name='Real', marker_color='#2F5597', text=[f"{e_real:.0f}"], textposition='auto'))
                    fig_eq.update_layout(title="Comparativa Equipos", barmode='group', height=300, margin=dict(t=30, b=0))
                    st.plotly_chart(fig_eq, use_container_width=True)
                
                st.divider()

    except Exception as e:
        st.error(f"Error crítico al procesar: {e}")
        st.info("Asegúrate de que la hoja se llame 'Base de Datos' y el archivo sea .xlsm")
