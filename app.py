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

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stButton>button { width: 100% !important; border-radius: 5px; height: 3em; }
    .stDownloadButton>button { width: 100% !important; border-radius: 5px; height: 3em; background-color: #2E7D32 !important; color: white !important; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #2E7D32; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES ---
def get_img_as_base64(file_path):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    except: return None

def generar_excel_pbi(df_dia, df_resumen):
    """Genera Excel profesional para Power BI"""
    output = BytesIO()
    # Es vital usar xlsxwriter para el formato
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_dia.to_excel(writer, sheet_name='Data_PowerBI', index=False)
        df_resumen.to_excel(writer, sheet_name='Resumen_Ejecutivo', index=False)
        
        workbook = writer.book
        header_fmt = workbook.add_format({'bold': True, 'fg_color': '#2E7D32', 'font_color': 'white', 'border': 1})
        
        for sheet in ['Data_PowerBI', 'Resumen_Ejecutivo']:
            ws = writer.sheets[sheet]
            cols = df_dia.columns if sheet == 'Data_PowerBI' else df_resumen.columns
            for col_num, value in enumerate(cols):
                ws.write(0, col_num, value, header_fmt)
                ws.set_column(col_num, col_num, 15)
    return output.getvalue()

# --- APP ---
st.title("Dashboard de Despachos por Producto")
file_tablero = st.sidebar.file_uploader("Cargar 03.- Tablero Despachos (.xlsm)", type=["xlsm"])

if file_tablero:
    try:
        # 1. Procesamiento de datos
        cols_idx = [1, 31, 32, 33, 34, 35, 36, 46]
        df = pd.read_excel(file_tablero, sheet_name="Base de Datos", usecols=cols_idx, engine='openpyxl')
        df.columns = ['Fecha', 'Producto', 'Destino', 'Ton_Prog', 'Ton_Real', 'Eq_Prog', 'Eq_Real', 'Regulacion_Real']
        
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce').dt.date
        df = df.dropna(subset=['Fecha'])
        df['Producto'] = df['Producto'].astype(str).str.upper().str.strip()
        
        for c in ['Ton_Prog', 'Ton_Real', 'Eq_Prog', 'Eq_Real', 'Regulacion_Real']:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

        fechas_disp = sorted(df['Fecha'].unique(), reverse=True)
        fecha_sel = st.sidebar.selectbox("📅 Seleccione la Fecha", fechas_disp)
        df_dia = df[df['Fecha'] == fecha_sel]
        
        # --- HEADER ---
        col_l, col_c, col_r = st.columns([1, 3, 1], vertical_alignment="center")
        with col_l:
            if os.path.exists("logoSQM-li-90.png"): st.image("logoSQM-li-90.png", width=120)
        with col_c:
            st.markdown(f"<h2 style='text-align: center;'>RESUMEN JORNADA {fecha_sel.strftime('%d-%m-%Y')}</h2>", unsafe_allow_html=True)
        with col_r:
            if os.path.exists("Image20240314124309.png"): st.image("Image20240314124309.png", width=200)

        # --- RESUMEN ---
        t_prog, t_real = df_dia['Ton_Prog'].sum(), df_dia['Ton_Real'].sum()
        st.columns(4)[0].metric("Ton. Real", f"{t_real:,.0f} T", f"{t_real-t_prog:+,.0f}")
        
        # Preparar data para el Excel y Gráficos
        productos_ordenados = (["SLIT"] + [p for p in sorted(df_dia['Producto'].unique()) if p != "SLIT"]) if "SLIT" in df_dia['Producto'].unique() else sorted(df_dia['Producto'].unique())
        
        resumen_data = []
        for p in productos_ordenados:
            d_p = df_dia[df_dia['Producto'] == p]
            resumen_data.append({
                'Producto': p,
                'Ton_Prog': d_p['Ton_Prog'].sum(),
                'Ton_Real': d_p['Ton_Real'].sum(),
                'Cumplimiento': (d_p['Ton_Real'].sum()/d_p['Ton_Prog'].sum()) if d_p['Ton_Prog'].sum()>0 else 0
            })
        df_resumen = pd.DataFrame(resumen_data)

        # Gráficos
        st.plotly_chart(px.bar(df_resumen, x='Producto', y=['Ton_Prog', 'Ton_Real'], barmode='group', title="Tonelaje por Producto", color_discrete_sequence=['#A8D5BA', '#2E7D32']), use_container_width=True)

        # ========================================
        # SECCIÓN DE EXPORTACIÓN (CORREGIDA)
        # ========================================
        st.markdown("---")
        st.markdown("<h3 style='text-align: center;'>Exportar Reportes</h3>", unsafe_allow_html=True)
        
        # CREAMOS 3 COLUMNAS IGUALES
        exp_col1, exp_col2, exp_col3 = st.columns(3)
        
        # --- BOTÓN 1: HTML ---
        with exp_col1:
            if st.button("Generar Reporte HTML Interactivo", type="primary"):
                st.info("Función HTML generada (Descárguela en el botón que aparecerá abajo)")
                html_code = f"<html><body><h1>Reporte {fecha_sel}</h1></body></html>"
                st.download_button("⬇️ Descargar HTML", html_code, "reporte.html", "text/html")

        # --- BOTÓN 2: CORREO ---
        with exp_col2:
            if st.button("Generar Texto de Correo"):
                texto = f"Resumen {fecha_sel}\nTotal: {t_real:,.0f} Ton"
                st.text_area("Copiar texto:", texto, height=100)

        # --- BOTÓN 3: POWER BI (Excel) ---
        with exp_col3:
            try:
                # Generamos el archivo antes del botón para asegurar que exista
                excel_file = generar_excel_pbi(df_dia, df_resumen)
                
                st.download_button(
                    label="Descargar para POWER BI",
                    data=excel_file,
                    file_name=f"Data_Despachos_{fecha_sel}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Haga clic para descargar el archivo Excel estructurado para Power BI"
                )
            except Exception as e:
                st.error("Error al preparar Excel")
                st.caption(str(e))

    except Exception as e:
        st.error(f"Error general: {e}")
else:
    st.info("Suba el archivo Excel en el menú lateral.")
