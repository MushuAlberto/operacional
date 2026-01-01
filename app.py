import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import base64
from io import BytesIO
from plotly.subplots import make_subplots
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="RESUMEN GENERAL DE LA JORNADA", layout="wide", page_icon="📊")

# --- ESTILOS CSS PARA MEJORAR LA UI ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #2E7D32; }
    .stButton>button { border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES AUXILIARES ---
def get_img_as_base64(file_path):
    """Lee una imagen local y la convierte a string Base64"""
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    except Exception:
        return None

def generar_excel_profesional(df_dia, df_resumen, fecha_sel):
    """Genera un Excel con múltiples hojas y formato usando xlsxwriter"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # 1. Hoja de Datos Planos (Para Power BI)
        df_dia.to_excel(writer, sheet_name='Data_PowerBI', index=False)
        
        # 2. Hoja de Resumen (Para Humanos)
        df_resumen.to_excel(writer, sheet_name='Resumen_Ejecutivo', index=False)
        
        # --- Formateo con XlsxWriter ---
        workbook  = writer.book
        sheet_res = writer.sheets['Resumen_Ejecutivo']
        sheet_dat = writer.sheets['Data_PowerBI']
        
        # Definir Formatos
        header_format = workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'vcenter',
            'fg_color': '#2E7D32', 'font_color': 'white', 'border': 1
        })
        num_format = workbook.add_format({'num_format': '#,##0', 'border': 1})
        pct_format = workbook.add_format({'num_format': '0.0%', 'border': 1})
        
        # Aplicar formatos a Resumen
        for col_num, value in enumerate(df_resumen.columns.values):
            sheet_res.write(0, col_num, value, header_format)
            sheet_res.set_column(col_num, col_num, 15)
            
        # Aplicar formatos a Data Power BI
        for col_num, value in enumerate(df_dia.columns.values):
            sheet_dat.write(0, col_num, value, header_format)
            sheet_dat.set_column(col_num, col_num, 18)

    return output.getvalue()

# --- LÓGICA PRINCIPAL ---
st.title("Dashboard de Despachos por Producto")
st.markdown("---")

file_tablero = st.sidebar.file_uploader("Cargar 03.- Tablero Despachos (.xlsm)", type=["xlsm"])

if file_tablero:
    try:
        # 1. Carga y limpieza de datos
        cols_idx = [1, 31, 32, 33, 34, 35, 36, 46]
        df = pd.read_excel(file_tablero, sheet_name="Base de Datos", usecols=cols_idx, engine='openpyxl')
        df.columns = ['Fecha', 'Producto', 'Destino', 'Ton_Prog', 'Ton_Real', 'Eq_Prog', 'Eq_Real', 'Regulacion_Real']
        
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce').dt.date
        df = df.dropna(subset=['Fecha'])
        df['Producto'] = df['Producto'].astype(str).str.upper().str.strip()
        df['Destino'] = df['Destino'].astype(str).str.strip()
        
        cols_num = ['Ton_Prog', 'Ton_Real', 'Eq_Prog', 'Eq_Real', 'Regulacion_Real']
        for col in cols_num:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 2. Selección de Fecha
        fechas_disp = sorted(df['Fecha'].unique(), reverse=True)
        fecha_sel = st.sidebar.selectbox("📅 Seleccione la Fecha", fechas_disp)
        df_dia = df[df['Fecha'] == fecha_sel]
        
        # Priorización
        productos_nombres = sorted(df_dia['Producto'].unique())
        productos_ordenados = (["SLIT"] + [p for p in productos_nombres if p != "SLIT"]) if "SLIT" in productos_nombres else productos_nombres

        # ========================================
        # SECCIÓN 1: CABECERA Y LOGOS
        # ========================================
        col_img_izq, col_espacio, col_img_der = st.columns([2, 6, 3], vertical_alignment="center")
        with col_img_izq:
            if os.path.exists("logoSQM-li-90.png"): st.image("logoSQM-li-90.png", width=120)
        with col_img_der:
            if os.path.exists("Image20240314124309.png"): st.image("Image20240314124309.png", width=250)
        
        st.markdown(f"<h2 style='text-align: center;'>RESUMEN GENERAL DE LA JORNADA</h2>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align: center;'>📅 {fecha_sel.strftime('%d-%m-%Y')}</h3>", unsafe_allow_html=True)
        st.markdown("---")
        
        # Cálculos Generales
        total_ton_prog = df_dia['Ton_Prog'].sum()
        total_ton_real = df_dia['Ton_Real'].sum()
        total_eq_prog = df_dia['Eq_Prog'].sum()
        total_eq_real = df_dia['Eq_Real'].sum()
        cumplimiento_general = (total_ton_real / total_ton_prog * 100) if total_ton_prog > 0 else 0
        
        # KPIs
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ton. Real Total", f"{total_ton_real:,.0f}", f"{total_ton_real - total_ton_prog:+,.0f} vs Prog")
        c2.metric("Equipos Real", f"{total_eq_real:.0f}", f"{total_eq_real - total_eq_prog:+.0f} vs Prog")
        c3.metric("Cumplimiento", f"{cumplimiento_general:.1f}%")
        c4.metric("N° Productos", len(productos_ordenados))
        
        # Preparar DataFrame de Resumen para Gráficos y Excel
        resumen_list = []
        for prod in productos_ordenados:
            df_p = df_dia[df_dia['Producto'] == prod]
            t_p, t_r = df_p['Ton_Prog'].sum(), df_p['Ton_Real'].sum()
            resumen_list.append({
                'Producto': prod,
                'Ton_Prog': t_p,
                'Ton_Real': t_r,
                'Eq_Prog': df_p['Eq_Prog'].sum(),
                'Eq_Real': df_p['Eq_Real'].sum(),
                'Cumplimiento': (t_r / t_p) if t_p > 0 else 0
            })
        df_resumen = pd.DataFrame(resumen_list)

        # Gráficos Principales
        cg1, cg2 = st.columns(2)
        with cg1:
            fig_ton = px.bar(df_resumen, x='Producto', y=['Ton_Prog', 'Ton_Real'], barmode='group', 
                             title="Comparativa Toneladas", color_discrete_sequence=['#A8D5BA', '#2E7D32'])
            st.plotly_chart(fig_ton, use_container_width=True)
        with cg2:
            fig_cump = px.bar(df_resumen, x='Producto', y='Cumplimiento', title="% Cumplimiento",
                              color='Cumplimiento', color_continuous_scale='RdYlGn')
            st.plotly_chart(fig_cump, use_container_width=True)

        # ========================================
        # SECCIÓN 2: DETALLES POR PRODUCTO (TABS)
        # ========================================
        st.header("DETALLES POR PRODUCTO")
        tabs = st.tabs([f"📦 {p}" for p in productos_ordenados])
        
        for idx, prod in enumerate(productos_ordenados):
            with tabs[idx]:
                df_p = df_dia[df_dia['Producto'] == prod]
                st.subheader(f"Análisis {prod}")
                col_tab1, col_tab2 = st.columns([2, 1])
                with col_tab1:
                    st.dataframe(df_p[['Destino', 'Ton_Prog', 'Ton_Real', 'Eq_Prog', 'Eq_Real']], use_container_width=True, hide_index=True)
                with col_tab2:
                    st.metric("Promedio Carga", f"{df_p['Ton_Real'].sum()/df_p['Eq_Real'].sum() if df_p['Eq_Real'].sum()>0 else 0:.1f} Ton/Eq")
                    st.metric("Regulación", f"{df_p['Regulacion_Real'].mean()*100:.1f}%")

        # ========================================
        # SECCIÓN 3: GENERACIÓN DE REPORTES (LOS 3 BOTONES)
        # ========================================
        st.markdown("---")
        st.markdown("<h3 style='text-align: center;'>Exportar Reportes</h3>", unsafe_allow_html=True)
        
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        with col_exp1:
            # BOTÓN HTML (Lógica simplificada para el ejemplo)
            if st.button("Generar HTML Interactivo", type="primary", use_container_width=True):
                st.info("Función HTML procesada (ver código original para string completo)")

        with col_exp2:
            # BOTÓN CORREO
            if st.button("Generar Texto de Correo", use_container_width=True):
                st.success("Texto listo (ver expansor abajo)")
                with st.expander("Copiar Texto de Correo"):
                    st.code(f"Resumen Jornada {fecha_sel}\nCumplimiento: {cumplimiento_general:.1f}%\nTotal Ton: {total_ton_real:,.0f}")

        with col_exp3:
            # BOTÓN POWER BI (EXCEL PROFESIONAL)
            excel_data = generar_excel_profesional(df_dia, df_resumen, fecha_sel)
            st.download_button(
                label="Descargar para POWER BI",
                data=excel_data,
                file_name=f"Reporte_Despachos_{fecha_sel.strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                help="Genera un Excel con hoja de datos limpia para Power BI y hoja de resumen formateada."
            )

    except Exception as e:
        st.error(f"Error: {e}")
        st.exception(e)
else:
    st.info("Suba un archivo para comenzar.")
