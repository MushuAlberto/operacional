import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Reporte Diario por Producto", layout="wide")

st.title("📊 Despachos Detallados por Producto")
st.markdown("---")

file_tablero = st.file_uploader("Cargar 03.- Tablero Despachos (.xlsm)", type=["xlsm"])

if file_tablero:
    try:
        # 1. Carga y Limpieza (Mismas columnas que definimos antes)
        cols_idx = [1, 31, 32, 33, 34, 35, 36, 46]
        df = pd.read_excel(file_tablero, sheet_name="Base de Datos", usecols=cols_idx, engine='openpyxl')
        df.columns = ['Fecha', 'Producto', 'Destino', 'Ton_Prog', 'Ton_Real', 'Eq_Prog', 'Eq_Real', 'Regulacion_Real']
        
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce').dt.date
        df = df.dropna(subset=['Fecha'])
        df['Producto'] = df['Producto'].astype(str).str.upper().strip()

        # 2. Selección de Fecha
        fechas_disp = sorted(df['Fecha'].unique(), reverse=True)
        fecha_sel = st.sidebar.selectbox("Seleccione la Fecha", fechas_disp)
        
        # Filtrar datos del día
        df_dia = df[df['Fecha'] == fecha_sel]
        productos_del_dia = sorted(df_dia['Producto'].unique())

        st.header(f"📅 Jornada: {fecha_sel.strftime('%d-%m-%Y')}")
        st.info(f"Se encontraron {len(productos_del_dia)} productos transportados este día.")

        # 3. Iteración por cada Producto (Genera una sección visual como la imagen por cada uno)
        for prod in productos_del_dia:
            df_prod = df_dia[df_dia['Producto'] == prod]
            
            # Cálculo de métricas por producto
            t_prog = df_prod['Ton_Prog'].sum()
            t_real = df_prod['Ton_Real'].sum()
            e_prog = df_prod['Eq_Prog'].sum()
            e_real = df_prod['Eq_Real'].sum()
            cumplimiento = (t_real / t_prog * 100) if t_prog > 0 else 0
            reg_promedio = df_prod['Regulacion_Real'].mean() * 100
            destino_principal = df_prod.loc[df_prod['Ton_Real'].idxmax(), 'Destino'] if not df_prod.empty else "N/A"

            # --- DISEÑO SEGÚN IMAGEN ---
            st.markdown(f"### Producto: {prod}")
            
            # Fila de Métricas (Tarjetas superiores)
            m1, m2, m3 = st.columns([2, 1, 1])
            with m1:
                st.caption("📍 Destino Principal")
                st.subheader(destino_principal)
            with m2:
                st.caption("Cumplimiento Día")
                st.subheader(f"{cumplimiento:.1f}%")
            with m3:
                st.caption("% Regulación Real")
                st.subheader(f"{reg_promedio:.1f}%")

            # Fila de Gráficos (Comparativa lateral)
            g1, g2 = st.columns(2)
            
            with g1:
                fig_ton = go.Figure()
                fig_ton.add_trace(go.Bar(x=['Tonelaje'], y=[t_prog], name='Prog', marker_color='#A8D5BA', text=[t_prog], textposition='auto'))
                fig_ton.add_trace(go.Bar(x=['Tonelaje'], y=[t_real], name='Real', marker_color='#2E7D32', text=[t_real], textposition='auto'))
                fig_ton.update_layout(title="Comparativa Toneladas", barmode='group', height=300, margin=dict(t=30, b=0, l=0, r=0))
                st.plotly_chart(fig_ton, use_container_width=True)

            with g2:
                fig_eq = go.Figure()
                fig_eq.add_trace(go.Bar(x=['Equipos'], y=[e_prog], name='Prog', marker_color='#BDD7EE', text=[e_prog], textposition='auto'))
                fig_eq.add_trace(go.Bar(x=['Equipos'], y=[e_real], name='Real', marker_color='#2F5597', text=[e_real], textposition='auto'))
                fig_eq.update_layout(title="Comparativa Equipos", barmode='group', height=300, margin=dict(t=30, b=0, l=0, r=0))
                st.plotly_chart(fig_eq, use_container_width=True)
            
            st.markdown("---") # Separador entre productos

    except Exception as e:
        st.error(f"Error al procesar: {e}")
