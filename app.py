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

# --- ESTILOS PERSONALIZADOS ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #2E7D32; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
    }
    .stTabs [aria-selected="true"] { background-color: #2E7D32 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES AUXILIARES ---
def get_img_as_base64(file_path):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    except: return None

def generar_excel_pbi(df_dia, df_resumen):
    """Genera Excel con formato para Power BI"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Hoja limpia para Power BI
        df_dia.to_excel(writer, sheet_name='Data_PowerBI', index=False)
        # Hoja de Resumen
        df_resumen.to_excel(writer, sheet_name='Resumen_Ejecutivo', index=False)
        
        workbook  = writer.book
        header_format = workbook.add_format({'bold': True, 'fg_color': '#2E7D32', 'font_color': 'white', 'border': 1})
        
        for sheetname in ['Data_PowerBI', 'Resumen_Ejecutivo']:
            worksheet = writer.sheets[sheetname]
            cols = df_dia.columns if sheetname == 'Data_PowerBI' else df_resumen.columns
            for col_num, value in enumerate(cols):
                worksheet.write(0, col_num, value, header_format)
                worksheet.set_column(col_num, col_num, 15)
    return output.getvalue()

# --- CARGA DE DATOS ---
st.title("Dashboard de Despachos por Producto")
file_tablero = st.sidebar.file_uploader("Cargar 03.- Tablero Despachos (.xlsm)", type=["xlsm"])

if file_tablero:
    try:
        # 1. Procesamiento
        cols_idx = [1, 31, 32, 33, 34, 35, 36, 46]
        df = pd.read_excel(file_tablero, sheet_name="Base de Datos", usecols=cols_idx, engine='openpyxl')
        df.columns = ['Fecha', 'Producto', 'Destino', 'Ton_Prog', 'Ton_Real', 'Eq_Prog', 'Eq_Real', 'Regulacion_Real']
        
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce').dt.date
        df = df.dropna(subset=['Fecha'])
        df['Producto'] = df['Producto'].astype(str).str.upper().str.strip()
        
        cols_num = ['Ton_Prog', 'Ton_Real', 'Eq_Prog', 'Eq_Real', 'Regulacion_Real']
        for col in cols_num:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 2. Filtros
        fechas_disp = sorted(df['Fecha'].unique(), reverse=True)
        fecha_sel = st.sidebar.selectbox("📅 Seleccione la Fecha", fechas_disp)
        df_dia = df[df['Fecha'] == fecha_sel]
        
        # Productos ordenados (SLIT primero)
        productos_nombres = sorted(df_dia['Producto'].unique())
        productos_ordenados = (["SLIT"] + [p for p in productos_nombres if p != "SLIT"]) if "SLIT" in productos_nombres else productos_nombres

        # --- CABECERA ---
        col_img_izq, col_tit, col_img_der = st.columns([1, 3, 1], vertical_alignment="center")
        with col_img_izq:
            if os.path.exists("logoSQM-li-90.png"): st.image("logoSQM-li-90.png", width=120)
        with col_tit:
            st.markdown(f"<h2 style='text-align: center;'>RESUMEN JORNADA {fecha_sel.strftime('%d-%m-%Y')}</h2>", unsafe_allow_html=True)
        with col_img_der:
            if os.path.exists("Image20240314124309.png"): st.image("Image20240314124309.png", width=200)

        # --- KPIs ---
        t_prog, t_real = df_dia['Ton_Prog'].sum(), df_dia['Ton_Real'].sum()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tonelaje Real", f"{t_real:,.0f} T", f"{t_real - t_prog:+,.0f} vs Prog")
        c2.metric("Equipos Reales", f"{df_dia['Eq_Real'].sum():.0f}")
        c3.metric("Cumplimiento", f"{(t_real/t_prog*100) if t_prog>0 else 0:.1f}%")
        c4.metric("Productos", len(productos_ordenados))

        # --- GRÁFICOS ---
        resumen_list = []
        for prod in productos_ordenados:
            df_p = df_dia[df_dia['Producto'] == prod]
            resumen_list.append({
                'Producto': prod,
                'Ton_Prog': df_p['Ton_Prog'].sum(),
                'Ton_Real': df_p['Ton_Real'].sum(),
                'Cumplimiento': (df_p['Ton_Real'].sum()/df_p['Ton_Prog'].sum()*100) if df_p['Ton_Prog'].sum()>0 else 0
            })
        df_resumen = pd.DataFrame(resumen_list)

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig_ton = px.bar(df_resumen, x='Producto', y=['Ton_Prog', 'Ton_Real'], barmode='group', title="Toneladas por Producto", color_discrete_sequence=['#A8D5BA', '#2E7D32'])
            st.plotly_chart(fig_ton, use_container_width=True)
        with col_g2:
            fig_cump = px.bar(df_resumen, x='Producto', y='Cumplimiento', title="% Cumplimiento", color='Cumplimiento', color_continuous_scale='RdYlGn')
            st.plotly_chart(fig_cump, use_container_width=True)

        # --- TABS DETALLE ---
        st.markdown("---")
        tabs = st.tabs([f"📦 {p}" for p in productos_ordenados])
        for i, prod in enumerate(productos_ordenados):
            with tabs[i]:
                df_p = df_dia[df_dia['Producto'] == prod]
                st.dataframe(df_p, hide_index=True, use_container_width=True)

        # ========================================
        # SECCIÓN DE EXPORTACIÓN (LOS 3 BOTONES)
        # ========================================
        st.markdown("---")
        st.markdown("<h3 style='text-align: center;'>📤 Exportar Reportes</h3>", unsafe_allow_html=True)
        
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        with col_exp1:
            # BOTÓN 1: HTML INTERACTIVO (Copiado de tu lógica original)
            if st.button("Generar HTML Interactivo", type="primary", use_container_width=True):
                logo_b64 = get_img_as_base64("logoSQM-li-90.png")
                html_report = f"""
                <html>
                <body style="font-family: sans-serif;">
                    <h1 style="color: #2E7D32;">Reporte de Despachos {fecha_sel}</h1>
                    <p>Tonelaje Total: {t_real:,.0f} Ton</p>
                    <table border="1" style="border-collapse: collapse; width: 100%;">
                        <tr style="background: #2E7D32; color: white;"><th>Producto</th><th>Real</th><th>Cumplimiento</th></tr>
                """
                for _, row in df_resumen.iterrows():
                    html_report += f"<tr><td>{row['Producto']}</td><td>{row['Ton_Real']:,.0f}</td><td>{row['Cumplimiento']:.1f}%</td></tr>"
                html_report += "</table></body></html>"
                
                st.download_button("Descargar Archivo HTML", html_report, f"reporte_{fecha_sel}.html", "text/html", use_container_width=True)

        with col_exp2:
            # BOTÓN 2: TEXTO DE CORREO
            if st.button("Generar Texto de Correo", use_container_width=True):
                cuerpo = f"Resumen Jornada {fecha_sel}:\n\n- Tonelaje Total: {t_real:,.0f}\n- Cumplimiento: {(t_real/t_prog*100) if t_prog>0 else 0:.1f}%\n\nRanking:\n"
                for _, row in df_resumen.head(5).iterrows():
                    cuerpo += f"- {row['Producto']}: {row['Ton_Real']:,.0f} Ton ({row['Cumplimiento']:.1f}%)\n"
                st.text_area("Copiar texto:", cuerpo, height=200)

        with col_exp3:
            # BOTÓN 3: POWER BI (Excel Profesional)
            excel_bin = generar_excel_pbi(df_dia, df_resumen)
            st.download_button(
                label="Descargar para POWER BI",
                data=excel_bin,
                file_name=f"Data_PBI_{fecha_sel}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")

else:
    st.info("Cargue el archivo Excel para activar el Dashboard.")
