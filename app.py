import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard Operacional SQM", layout="wide", page_icon="📈")

def call_gemini_api(prompt, api_key, model="gemini-1.5-flash"):
    # Ruta v1beta para máxima compatibilidad con modelos 1.5
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.2}}
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        return response.json()['candidates'][0]['content']['parts'][0]['text'], None
    except:
        return "Error al conectar con la IA", "Error"

# --- 2. CARGA DE ARCHIVOS ---
st.title("📊 Control de Despachos y Cumplimiento 2025")
st.markdown("---")

col_up1, col_up2 = st.columns(2)
with col_up1:
    file_romanas = st.file_uploader("📁 02.- Histórico Romanas", type=["xlsx"])
with col_up2:
    file_tablero = st.file_uploader("📁 03.- Tablero Despachos (XLSM)", type=["xlsm"])

if file_tablero and file_romanas:
    try:
        # --- PROCESAMIENTO TABLERO (03) ---
        # Columnas: B=1, AF=31, AG=32, AH=33, AI=34, AJ=35, AK=36, AL=37
        cols_tab = [1, 31, 32, 33, 34, 35, 36, 37] 
        df_tab = pd.read_excel(file_tablero, sheet_name="Base de Datos", usecols=cols_tab, engine='openpyxl')
        df_tab.columns = ['Fecha', 'Producto', 'Destino', 'Ton_Prog', 'Ton_Real', 'Eq_Prog', 'Eq_Real', 'Cumplimiento']
        df_tab['Producto'] = df_tab['Producto'].astype(str).str.strip().str.upper()

        # --- PROCESAMIENTO ROMANAS (02) ---
        # Buscamos columnas de regulación W, X, Y (índices 22, 23, 24) y Producto para filtrar
        df_rom = pd.read_excel(file_romanas, engine='openpyxl')
        # Limpieza de nombres de columnas en Romanas para evitar errores de espacios
        df_rom.columns = df_rom.columns.str.strip().str.upper()
        
        # --- 3. FILTROS Y SELECCIÓN ---
        st.sidebar.header("🎯 Selección de Producto")
        lista_productos = sorted(df_tab['Producto'].unique())
        prod_sel = st.sidebar.selectbox("Producto a Consultar", lista_productos)
        
        df_p = df_tab[df_tab['Producto'] == prod_sel]
        
        # Filtrar regulaciones en Romanas para el producto seleccionado
        # Asumiendo que existe una columna 'PRODUCTO' en Romanas
        if 'PRODUCTO' in df_rom.columns:
            df_reg_sel = df_rom[df_rom['PRODUCTO'].astype(str).str.upper() == prod_sel]
            reg1 = df_reg_sel['REGULACION 1'].sum() if 'REGULACION 1' in df_reg_sel.columns else 0
            reg2 = df_reg_sel['REGULACION 2'].sum() if 'REGULACION 2' in df_reg_sel.columns else 0
            reg3 = df_reg_sel['REGULACION 3'].sum() if 'REGULACION 3' in df_reg_sel.columns else 0
        else:
            reg1, reg2, reg3 = 0, 0, 0

        # --- 4. TARJETAS MÉTRICAS ---
        t_prog, t_real = df_p['Ton_Prog'].sum(), df_p['Ton_Real'].sum()
        cump_tot = (t_real / t_prog * 100) if t_prog > 0 else 0
        eq_prog, eq_real = df_p['Eq_Prog'].sum(), df_p['Eq_Real'].sum()

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Cumplimiento Total", f"{cump_tot:.1f}%", delta=f"{cump_tot-100:.1f}% vs Meta")
        with m2:
            st.metric("Total Equipos Reales", f"{eq_real:.0f} camiones")
        with m3:
            total_reg = reg1 + reg2 + reg3
            st.metric("Total Regulaciones", f"{total_reg:.0f}", delta="Equipos en espera", delta_color="inverse")

        # --- 5. GRÁFICOS COMPARATIVOS ---
        st.subheader(f"Análisis de Desempeño: {prod_sel}")
        g1, g2 = st.columns(2)

        with g1:
            # Gráfico Toneladas
            fig_ton = go.Figure(data=[
                go.Bar(name='Programado', x=['Tonelaje'], y=[t_prog], marker_color='#A8D5BA'),
                go.Bar(name='Real', x=['Tonelaje'], y=[t_real], marker_color='#2E7D32')
            ])
            fig_ton.update_layout(title="Toneladas: Prog vs Real", barmode='group', height=400)
            st.plotly_chart(fig_ton, use_container_width=True)

        with g2:
            # Gráfico Equipos
            fig_eq = go.Figure(data=[
                go.Bar(name='Programado', x=['Equipos'], y=[eq_prog], marker_color='#BDD7EE'),
                go.Bar(name='Real', x=['Equipos'], y=[eq_real], marker_color='#2F5597')
            ])
            fig_eq.update_layout(title="Equipos: Prog vs Real", barmode='group', height=400)
            st.plotly_chart(fig_eq, use_container_width=True)

        # --- 6. SECCIÓN DE REGULACIONES (DETALLE) ---
        if total_reg > 0:
            st.warning(f"🚨 Se detectaron regulaciones activas para {prod_sel}")
            r1, r2, r3 = st.columns(3)
            r1.info(f"**Regulación 1**\n\n {reg1:.0f} Equipos")
            r2.info(f"**Regulación 2**\n\n {reg2:.0f} Equipos")
            r3.info(f"**Regulación 3**\n\n {reg3:.0f} Equipos")

        # --- 7. IA ANALYST ---
        st.divider()
        if st.button("🚀 Generar Informe Operacional IA"):
            api_k = st.secrets.get("GEMINI_API_KEY")
            if api_k:
                with st.spinner("Analizando brechas operativas..."):
                    prompt = f"""
                    Analiza el producto {prod_sel}. 
                    Cumplimiento: {cump_tot:.1f}%. 
                    Equipos Reales: {eq_real} de {eq_prog} programados.
                    Regulaciones detectadas: {total_reg}.
                    Tarea: Diagnostica por qué no se cumplió la meta y si las regulaciones están impactando el flujo.
                    """
                    res, err = call_gemini_api(prompt, api_k)
                    st.markdown(f"### Análisis de la IA:\n{res}")
            else:
                st.warning("API Key no configurada en Secrets.")

    except Exception as e:
        st.error(f"Error de procesamiento: {e}")
else:
    st.info("👋 Por favor, carga los archivos 02 y 03 para activar el dashboard.")
