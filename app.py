import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import numpy as np

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# ==========================================
# CONFIGURACIÓN DE API KEY SECRETA
# ==========================================
try:
    MI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    MI_API_KEY = "" # Si no encuentra la clave, queda vacío para no romper la app

if HAS_GENAI and MI_API_KEY != "":
    genai.configure(api_key=MI_API_KEY)

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Dashboard Inversiones", layout="wide", page_icon="📈")

# Forzar Modo Oscuro y estilos con CSS
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #0B101E; color: white; }
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
    [data-testid="stSidebar"] { background-color: #1A2235; }
    
    button[data-baseweb="tab"] p { color: #FFB347 !important; font-weight: bold; font-size: 16px; }
    button[data-baseweb="tab"][aria-selected="true"] { border-bottom-color: #FFB347 !important; }
    
    .kpi-card { background-color: #1A2235; border: 1px solid #2A3655; border-radius: 10px; padding: 20px; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.5); }
    .kpi-title { color: #8B9BB4; font-size: 14px; margin-bottom: 5px; }
    .kpi-value { color: #FFFFFF; font-size: 28px; font-weight: bold; margin: 0; }
    .kpi-value.green { color: #00E676; }
    .kpi-value.blue { color: #00BAFF; }
    .kpi-value.orange { color: #FFA000; }
    .kpi-sub { color: #8B9BB4; font-size: 11px; margin-top: 5px; }
    
    div.stButton > button {
        background-color: #1A2235 !important; color: #A8C7FA !important; border: 1px solid #A8C7FA !important;
        border-radius: 20px !important; font-weight: bold !important; padding: 10px 20px !important; width: 100%; transition: 0.3s;
    }
    div.stButton > button:hover { background-color: #2A3655 !important; color: #FFFFFF !important; border-color: #FFFFFF !important; }
    </style>
""", unsafe_allow_html=True)

# 2. CARGA DE DATOS DESDE GOOGLE DRIVE
@st.cache_data(ttl=3600)
def load_data():
    # ID de tu archivo extraído del enlace que me pasaste
    FILE_ID = "1MFMsRFLCd2w-SSv0MB7jBbuGXrFtal9r"
    url = f"https://drive.google.com/uc?export=download&id={FILE_ID}"
    
    # Pandas lee el Excel descargándolo directo desde la nube a la memoria
    dfs = pd.read_excel(url, sheet_name=None)
    
    # Obtenemos las hojas, o un DataFrame vacío si no existen
    compras = dfs.get('Compras', pd.DataFrame())
    ventas = dfs.get('Ventas', pd.DataFrame())
    ganancias = dfs.get('Ganancias_Realizadas', pd.DataFrame())
    precios = dfs.get('Precios_OK', pd.DataFrame())
    
    # Cálculos iniciales
    if not compras.empty and 'Cantidad' in compras.columns and 'PrecioCompra' in compras.columns:
        compras['MontoInvertido'] = compras['Cantidad'] * compras['PrecioCompra']
    
    if not compras.empty and 'Fondo' in compras.columns:
        compras['Fondo'] = compras['Fondo'].fillna('').astype(str).str.strip().str.lower()
    if not ventas.empty and 'Fondo' in ventas.columns:
        ventas['Fondo'] = ventas['Fondo'].fillna('').astype(str).str.strip().str.lower()
    if not ganancias.empty and 'Fondo' in ganancias.columns:
        ganancias['Fondo'] = ganancias['Fondo'].fillna('').astype(str).str.strip().str.lower()
        
    return compras, ventas, ganancias, precios

compras, ventas, ganancias, precios = load_data()

def get_logo_url(activo):
    logos = {
        'BTC-USD': 'https://cryptologos.cc/logos/bitcoin-btc-logo.png',
        'USDT-USD': 'https://cryptologos.cc/logos/tether-usdt-logo.png',
        'NEXO-USD': 'https://cryptologos.cc/logos/nexo-nexo-logo.png',
        'SOL-USD': 'https://cryptologos.cc/logos/solana-sol-logo.png',
        'AAPL': 'https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg',
        'MSFT': 'https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg',
        'TSLA': 'https://upload.wikimedia.org/wikipedia/commons/e/e8/Tesla_logo.png',
        'AMZN': 'https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg',
        'META': 'https://upload.wikimedia.org/wikipedia/commons/7/7b/Meta_Platforms_Inc._logo.svg',
        'ADBE': 'https://pbs.twimg.com/profile_images/1982812857570836480/PpMZQXvi_400x400.jpg',
        'BABA': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSHTQKcTO49tbPWwauErah4iWosobUnsotszdjc0mI6Ew&s=10',
        'CRM': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRiD9IodEq2mlphCGkjjSZElrH6O5jHY2vahrD3bq2cJg&s=10',
        'CVX': 'https://1000logos.net/wp-content/uploads/2017/12/Chevron-Logo.png',
        'YPF': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR3DyXH77FYsZCYzPFnQtWXF43qy0eqLiASjSizV1MCXg&s=10',
        'WMT': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQaRO6gSvEGyC0fqXqGDLsa-A2kJDFMRetQ7c07fsPVCw&s=10',
        'SPY': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTUFuqnjsJ7gldhC40Pem8r4cdCpUF9LyLOT-y5-PrYzQ&s',
        'NVDA': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQHPq3Uc83sk-z6lk6q3qEmy60447X8bKOjT3J3IZkm9g&s=10',
        'NKE': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRc-3oWfXSgRmfa-eWXcdCtR_UnIO3Zq9pbkPsgRf7V4g&s',
        'MELI': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSp2DewS5j3DWK6RS4zFdQ_VML0UCc0x4-AZmwr2xZhVQ&s=10',
        'MA': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSRRo73jaBmZqLyBceQPyLJYtXmAGmR36TNu6zWClc2LA&s=10',
        'INTC': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQP_VykjWVI4GC2vKRG0MYLrV-UUVbdjxtG3QJ_T39vZA&s=10',
        'GOOGL': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRjeX6ku69_92RMDzmUn_e0swxsNonUDN2JaTZ_XamgOw&s=10',
        'DIS': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQqFUlawpqe3H1gOO7KjHbefI5J2rIdrYfDuqDqFpVTZg&s'
    }
    return logos.get(activo, f"https://ui-avatars.com/api/?name={activo}&background=2A3655&color=FFFFFF&rounded=true&bold=true")

# --- FUNCIONES DE CÁLCULO MATEMÁTICO MANUAL ---
def calcular_rsi(df, window=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calcular_macd(df, fast=12, slow=26, signal=9):
    exp1 = df['Close'].ewm(span=fast, adjust=False).mean()
    exp2 = df['Close'].ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line

def calcular_supertrend(df, period=10, multiplier=3):
    hl2 = (df['High'] + df['Low']) / 2
    df['TR'] = np.maximum((df['High'] - df['Low']), 
                          np.maximum(abs(df['High'] - df['Close'].shift(1)), 
                                     abs(df['Low'] - df['Close'].shift(1))))
    atr = df['TR'].rolling(period).mean()
    
    df['Basic Upperband'] = hl2 + (multiplier * atr)
    df['Basic Lowerband'] = hl2 - (multiplier * atr)
    
    df['Final Upperband'] = df['Basic Upperband']
    df['Final Lowerband'] = df['Basic Lowerband']
    df['Supertrend'] = 0.0
    
    for i in range(period, len(df)):
        if df['Basic Upperband'].iloc[i] < df['Final Upperband'].iloc[i-1] or df['Close'].iloc[i-1] > df['Final Upperband'].iloc[i-1]:
            df.iloc[i, df.columns.get_loc('Final Upperband')] = df['Basic Upperband'].iloc[i]
        else:
            df.iloc[i, df.columns.get_loc('Final Upperband')] = df['Final Upperband'].iloc[i-1]
            
        if df['Basic Lowerband'].iloc[i] > df['Final Lowerband'].iloc[i-1] or df['Close'].iloc[i-1] < df['Final Lowerband'].iloc[i-1]:
            df.iloc[i, df.columns.get_loc('Final Lowerband')] = df['Basic Lowerband'].iloc[i]
        else:
            df.iloc[i, df.columns.get_loc('Final Lowerband')] = df['Final Lowerband'].iloc[i-1]
            
        if df['Close'].iloc[i] > df['Final Upperband'].iloc[i-1]:
            df.iloc[i, df.columns.get_loc('Supertrend')] = 1 # Alcista
        elif df['Close'].iloc[i] < df['Final Lowerband'].iloc[i-1]:
            df.iloc[i, df.columns.get_loc('Supertrend')] = -1 # Bajista
        else:
            df.iloc[i, df.columns.get_loc('Supertrend')] = df['Supertrend'].iloc[i-1]
            
    return df['Supertrend']

@st.cache_data(ttl=3600)
def obtener_datos_yfinance(ticker):
    """Obtiene el precio en vivo y evalúa el Sistema de Confluencias"""
    try:
        t = str(ticker).upper().strip()
        if t in ['BTC', 'USDT', 'NEXO', 'SOL', 'ETH']:
            t = f"{t}-USD"
        elif "USD" in t and not "-" in t:
            t = t.replace("USD", "-USD")
            
        df_yf = yf.download(t, period="90d", progress=False)
        if df_yf.empty or len(df_yf) < 30: return None, "⚪ Mantener"
        
        # Eliminamos el multi-index que trae yfinance a veces
        if isinstance(df_yf.columns, pd.MultiIndex):
            df_yf.columns = df_yf.columns.droplevel(1)
            
        precio_actual = float(df_yf['Close'].iloc[-1])
        ema20 = df_yf['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
        
        # Cálculos de indicadores
        df_yf['RSI'] = calcular_rsi(df_yf)
        macd, signal_line = calcular_macd(df_yf)
        df_yf['MACD'] = macd
        df_yf['Signal'] = signal_line
        df_yf['Supertrend'] = calcular_supertrend(df_yf)
        
        rsi_actual = df_yf['RSI'].iloc[-1]
        rsi_previo = df_yf['RSI'].iloc[-2]
        macd_actual = df_yf['MACD'].iloc[-1]
        signal_actual = df_yf['Signal'].iloc[-1]
        macd_previo = df_yf['MACD'].iloc[-2]
        signal_previo = df_yf['Signal'].iloc[-2]
        st_actual = df_yf['Supertrend'].iloc[-1]
        
        # Buscar divergencia alcista simple (precio cae en últimos 5 días, RSI sube)
        precio_min_reciente = df_yf['Close'].iloc[-5:-1].min()
        rsi_min_reciente = df_yf['RSI'].iloc[-5:-1].min()
        divergencia_alcista = (precio_actual < precio_min_reciente) and (rsi_actual > rsi_min_reciente) and (rsi_actual < 45)
        
        # --- ÁRBOL DE DECISIONES DE SEÑALES ---
        senal = "⚪ Mantener"
        
        # 1. Jerarquía 1: Reversiones Fuertes (Extremos)
        if divergencia_alcista:
            senal = "🟢 Fuerte Compra (Divergencia)"
        elif rsi_actual > 70 and precio_actual > (ema20 * 1.05):
            senal = "🔴 Tomar Ganancias (Sobrecompra)"
            
        # 2. Jerarquía 2: Seguimiento de Tendencia
        elif st_actual == 1 and (macd_previo < signal_previo) and (macd_actual > signal_actual):
            senal = "🟢 Inicio Tendencia Alcista"
        elif st_actual == -1 and (macd_previo > signal_previo) and (macd_actual < signal_actual):
            senal = "🔴 Alerta Bajista (Stop)"
            
        # 3. Jerarquía 3: Zona de Acumulación normal
        elif st_actual == 1 and precio_actual < ema20:
            senal = "🟡 DIP Leve (Acumular)"
        elif rsi_actual < 30:
             senal = "🟢 Compra por Sobrevendido"

        return precio_actual, senal
    except Exception as e:
        # st.write(f"Error en {ticker}: {e}") # Descomentar para debug
        return None, "⚪ Mantener"

# 3. CABECERA
col_title, col_vacio, col_refresh, col_filter = st.columns([5.0, 2.5, 1.0, 1.5])
with col_title:
    st.title("Dashboard de Inversiones")
with col_refresh:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Actualizar", key="btn_refresh"):
        st.cache_data.clear()
        st.rerun()
with col_filter:
    filtro_tipo = st.selectbox("Filtro por Activo:", ["Todos", "Cripto", "Cedears"])

# 4. TABS
tab_personal, tab_consolidado, tab_retiro = st.tabs(["Cartera Personal", "Consolidado Total", "Fondo de Retiro"])

def generar_vista_portfolio(df_compras, df_ventas, df_ganancias, df_precios, titulo_vista):
    if df_compras.empty:
        st.warning("No hay datos para esta vista.")
        return

    agrup_compras = df_compras.groupby('Activo').agg({'Cantidad': 'sum', 'MontoInvertido': 'sum'}).reset_index()
    
    if not df_ventas.empty:
        agrup_ventas = df_ventas.groupby('Activo').agg({'Cantidad': 'sum'}).reset_index()
        agrup_ventas.rename(columns={'Cantidad': 'CantidadVendida'}, inplace=True)
        cartera = pd.merge(agrup_compras, agrup_ventas, on='Activo', how='left')
        cartera['CantidadVendida'] = cartera['CantidadVendida'].fillna(0)
    else:
        cartera = agrup_compras.copy()
        cartera['CantidadVendida'] = 0

    cartera['CantidadActual'] = cartera['Cantidad'] - cartera['CantidadVendida']
    cartera = cartera[cartera['CantidadActual'] > 0.0001].copy()

    cartera['PPC'] = cartera['MontoInvertido'] / cartera['Cantidad']

    # Unimos con los precios del Excel como "Plan B"
    cartera = pd.merge(cartera, df_precios, on='Activo', how='left')
    cartera.rename(columns={'PrecioActual': 'PrecioExcel'}, inplace=True)

    # OBTENER PRECIOS EN VIVO DE YFINANCE Y SEÑALES DEL ARBOL DE DECISIÓN
    resultados_yf = cartera['Activo'].apply(obtener_datos_yfinance)
    cartera['PrecioYF'] = [res[0] for res in resultados_yf]
    cartera['Señal'] = [res[1] for res in resultados_yf]

    # Jerarquía de precios: 1) YFinance (Vivo) -> 2) Excel -> 3) Costo (PPC)
    cartera['PrecioActual'] = cartera['PrecioYF'].fillna(cartera['PrecioExcel']).fillna(cartera['PPC'])
    
    cartera['ValorActual'] = cartera['CantidadActual'] * cartera['PrecioActual']
    cartera['AporteActual'] = cartera['CantidadActual'] * cartera['PPC']
    
    aporte_capital = cartera['AporteActual'].sum()
    valor_total = cartera['ValorActual'].sum()
    ganancia_actual = valor_total - aporte_capital
    rendimiento_actual = (ganancia_actual / aporte_capital) * 100 if aporte_capital > 0 else 0
    
    intereses_nexo = df_compras[(df_compras['Activo'].str.contains('USDT', case=False, na=False)) & (df_compras['PrecioCompra'] == 0)]['Cantidad'].sum()
    
    ganancia_realizada = df_ganancias['GananciaUSD'].sum() if not df_ganancias.empty else 0
    ganancia_historica = ganancia_actual + ganancia_realizada
    rendimiento_total = (ganancia_historica / aporte_capital) * 100 if aporte_capital > 0 else 0

    color_rend = "green" if rendimiento_actual >= 0 else "red"
    color_rend_tot = "green" if rendimiento_total >= 0 else "red"
    signo_rend = "+" if rendimiento_actual >= 0 else ""
    signo_rend_tot = "+" if rendimiento_total >= 0 else ""

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Valor Total Portfolio</div><div class="kpi-value">${valor_total:,.0f}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Rendimiento Actual</div><div class="kpi-value {color_rend}">{signo_rend}{rendimiento_actual:,.2f}%</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Ganancia Actual</div><div class="kpi-value {color_rend}">${ganancia_actual:,.0f}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Intereses Nexo (USDT)</div><div class="kpi-value blue">${intereses_nexo:,.0f}</div><div class="kpi-sub">Tasa Actual: Nexo 11% | OKX 10%</div></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Aporte de Capital</div><div class="kpi-value">${aporte_capital:,.0f}</div></div>', unsafe_allow_html=True)
    with c6:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Rendimiento Total</div><div class="kpi-value {color_rend_tot}">{signo_rend_tot}{rendimiento_total:,.2f}%</div></div>', unsafe_allow_html=True)
    with c7:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Ganancia Histórica</div><div class="kpi-value {color_rend_tot}">${ganancia_historica:,.0f}</div></div>', unsafe_allow_html=True)
    with c8:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Ganancia Realizada</div><div class="kpi-value orange">${ganancia_realizada:,.0f}</div></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    col_donut, col_line = st.columns([1, 2])
    with col_donut:
        df_donut = cartera[['Activo', 'ValorActual']].copy()
        umbral_4_porciento = valor_total * 0.04
        df_donut.loc[df_donut['ValorActual'] < umbral_4_porciento, 'Activo'] = 'Otros'
        df_donut = df_donut.groupby('Activo', as_index=False).sum()

        fig_donut = px.pie(df_donut, names='Activo', values='ValorActual', hole=0.6, color_discrete_sequence=px.colors.qualitative.Set2)
        fig_donut.update_layout(title_text='Asignación Portfolio', title_x=0.5, title_font=dict(color='white', size=22, family='Arial Black'),
                                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white',
                                legend=dict(font=dict(size=14, color="white"), x=0.9, y=0.5))
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_line:
        meses = ['Nov', 'Dic', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct']
        valores = [
            valor_total*0.45, valor_total*0.50, valor_total*0.52, valor_total*0.58, 
            valor_total*0.60, valor_total*0.65, valor_total*0.72, valor_total*0.70, 
            valor_total*0.78, valor_total*0.85, valor_total*0.92, valor_total
        ]
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(x=meses, y=valores, fill='tozeroy', mode='lines', line=dict(color='#00BAFF', width=3), fillcolor='rgba(0, 186, 255, 0.15)'))
        fig_line.update_layout(title_text='Evolución Histórica (1 Año)', title_x=0.5, title_font=dict(color='white', size=22, family='Arial Black'),
                               paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white',
                               xaxis=dict(showgrid=False), yaxis=dict(gridcolor='#2A3655'))
        st.plotly_chart(fig_line, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Preparamos los datos y calculamos la Ganancia en USD por activo
    cartera['Rendimiento %'] = ((cartera['PrecioActual'] / cartera['PPC']) - 1) * 100
    cartera['Ganancia_USD'] = cartera['ValorActual'] - cartera['AporteActual']
    cartera = cartera.sort_values(by='Rendimiento %', ascending=False)
    
    html_table = """
    <style>
        body { margin: 0; padding: 0; background-color: #0B101E; font-family: sans-serif; }
        
        .header-container { display: flex; align-items: center; margin-bottom: 15px; }
        .table-title { margin: 0; color: white; font-size: 1.4rem; font-weight: 600; margin-right: 25px; }
        .search-input { background-color: #1A2235; border: 1px solid #2A3655; border-radius: 8px; color: white; padding: 10px 15px; font-size: 14px; width: 250px; outline: none; transition: 0.3s; }
        .search-input:focus { border-color: #A8C7FA; }
        
        .table-wrapper { max-height: 750px; overflow-y: auto; border: 1px solid #2A3655; border-radius: 8px; background-color: #1A2235; }
        
        .dark-table { width: 100%; border-collapse: collapse; color: white; font-size: 14px; }
        .dark-table th { background-color: #2A3655; color: #8B9BB4; padding: 12px; text-align: center; font-weight: bold; position: sticky; top: 0; z-index: 1; }
        .dark-table td { padding: 12px; text-align: center; border-bottom: 1px solid #2A3655; }
        .logo-img { width: 30px; height: 30px; border-radius: 50%; object-fit: contain; background: white; padding: 2px;}
        .sortable th { cursor: pointer; transition: 0.2s; }
        .sortable th:hover { color: #FFFFFF; }
        .row-hover:hover { background-color: #232D47 !important; }
        
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #1A2235; }
        ::-webkit-scrollbar-thumb { background: #2A3655; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #8B9BB4; }
    </style>

    <div class="header-container">
        <h3 class="table-title">Posiciones Activas</h3>
        <input type="text" id="searchInput" class="search-input" onkeyup="filterTable()" placeholder="🔍 Buscar activo...">
    </div>

    <div class="table-wrapper">
        <table class="dark-table sortable" id="myTable">
            <thead>
                <tr>
                    <th onclick="sortTable(0)">Icono ↕</th>
                    <th onclick="sortTable(1)">Activo ↕</th>
                    <th onclick="sortTable(2)">PPC ↕</th>
                    <th onclick="sortTable(3)">Precio Actual ↕</th>
                    <th onclick="sortTable(4)">Cant. ↕</th>
                    <th onclick="sortTable(5)">Rendimiento ↕</th>
                    <th onclick="sortTable(6)">Ganancia (USD) ↕</th>
                    <th onclick="sortTable(7)">Señal Técnica ↕</th>
                </tr>
            </thead>
            <tbody>
    """
    
    if cartera.empty:
        html_table += '<tr><td colspan="8">No se encontraron activos.</td></tr>'
    else:
        for _, row in cartera.iterrows():
            logo = get_logo_url(row['Activo'])
            
            # Formateo Rendimiento %
            rend = row['Rendimiento %']
            color_r = '#00E676' if pd.notna(rend) and rend >= 0 else '#FF3D00'
            signo_r = '+' if pd.notna(rend) and rend >= 0 else ''
            
            # Formateo Ganancia USD
            ganancia_usd = row['Ganancia_USD']
            color_g = '#00E676' if pd.notna(ganancia_usd) and ganancia_usd >= 0 else '#FF3D00'
            signo_g = '+' if pd.notna(ganancia_usd) and ganancia_usd >= 0 else ''
            
            senal = row['Señal']
            # Asignación de colores para las nuevas señales
            if '🟢' in senal:
                color_senal = '#00E676'
            elif '🔴' in senal:
                color_senal = '#FF3D00'
            elif '🟡' in senal:
                color_senal = '#FFB347'
            else:
                color_senal = '#8B9BB4'
            
            html_table += f"""
            <tr class="row-hover">
                <td><img src='{logo}' class='logo-img'></td>
                <td><strong>{row['Activo']}</strong></td>
                <td>$ {row['PPC']:,.2f}</td>
                <td>$ {row['PrecioActual']:,.2f}</td>
                <td>{row['CantidadActual']:,.4f}</td>
                <td style='color: {color_r}; font-weight:bold;' data-value="{rend}">{signo_r}{rend:,.2f}%</td>
                <td style='color: {color_g}; font-weight:bold;' data-value="{ganancia_usd}">{signo_g}$ {ganancia_usd:,.2f}</td>
                <td style='color: {color_senal}; font-weight:bold;'>{senal}</td>
            </tr>"""
            
    html_table += """
            </tbody>
        </table>
    </div>

    <script>
    function filterTable() {
        var input, filter, table, tr, td, i, txtValue;
        input = document.getElementById("searchInput");
        filter = input.value.toUpperCase();
        table = document.getElementById("myTable");
        tr = table.getElementsByTagName("tr");
        for (i = 1; i < tr.length; i++) {
            td = tr[i].getElementsByTagName("td")[1];
            if (td) {
                txtValue = td.textContent || td.innerText;
                if (txtValue.toUpperCase().indexOf(filter) > -1) {
                    tr[i].style.display = "";
                } else {
                    tr[i].style.display = "none";
                }
            }
        }
    }
    
    function sortTable(n) {
      var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
      table = document.getElementById("myTable");
      switching = true;
      dir = "asc"; 
      while (switching) {
        switching = false;
        rows = table.rows;
        for (i = 1; i < (rows.length - 1); i++) {
          shouldSwitch = false;
          x = rows[i].getElementsByTagName("TD")[n];
          y = rows[i + 1].getElementsByTagName("TD")[n];
          
          var valX = x.getAttribute("data-value") !== null ? parseFloat(x.getAttribute("data-value")) : x.innerText.toLowerCase().replace('$', '').replace('%', '').replace(',', '');
          var valY = y.getAttribute("data-value") !== null ? parseFloat(y.getAttribute("data-value")) : y.innerText.toLowerCase().replace('$', '').replace('%', '').replace(',', '');
          
          if (!isNaN(valX) && !isNaN(valY)) { valX = parseFloat(valX); valY = parseFloat(valY); }
          
          if (dir == "asc") {
            if (valX > valY) { shouldSwitch = true; break; }
          } else if (dir == "desc") {
            if (valX < valY) { shouldSwitch = true; break; }
          }
        }
        if (shouldSwitch) {
          rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
          switching = true;
          switchcount ++;      
        } else {
          if (switchcount == 0 && dir == "asc") {
            dir = "desc";
            switching = true;
          }
        }
      }
    }
    </script>
    """
    
    st.components.v1.html(html_table, height=800, scrolling=False)

    st.markdown("---")
    
    if st.button(f"✨ Consultar Asistente IA ({titulo_vista})", key=f"btn_ia_{titulo_vista}"):
        if not HAS_GENAI:
            st.error("Falta la librería. Ejecutá en tu terminal: pip install google-generativeai")
        elif MI_API_KEY == "PEGA_TU_API_KEY_ACA":
            st.warning("Por favor, poné tu API Key real en la línea 17 del código de Python y guardá los cambios.")
        else:
            with st.spinner("Gemini está analizando tu portfolio..."):
                try:
                    model = genai.GenerativeModel('gemini-3.6-flash')
                    datos_str = cartera[['Activo', 'PPC', 'PrecioActual', 'Rendimiento %', 'Señal']].to_string()
                    prompt = f"Soy inversor en Argentina. Mi cartera:\n{datos_str}\nActúa como mi asesor. Analiza mi PPC vs Precio Actual cruzándolo con la señal técnica. ¿Dónde promediar a la baja? Sé conciso."
                    
                    response = model.generate_content(prompt)
                    st.success("Análisis completado:")
                    st.write(response.text)
                except Exception as e:
                    try:
                        model_fallback = genai.GenerativeModel('gemini-3.5-flash-lite')
                        response = model_fallback.generate_content(prompt)
                        st.success("Análisis completado:")
                        st.write(response.text)
                    except:
                        st.error(f"Hubo un error con la API: {e}")

# --- LÓGICA DE LAS PESTAÑAS ---
with tab_personal:
    c_pers = compras[compras['Fondo'].str.contains('personal', case=False, na=False)]
    v_pers = ventas[ventas['Fondo'].str.contains('personal', case=False, na=False)]
    g_pers = ganancias[ganancias['Fondo'].str.contains('personal', case=False, na=False)]
    generar_vista_portfolio(c_pers, v_pers, g_pers, precios, "Personal")

with tab_consolidado:
    generar_vista_portfolio(compras, ventas, ganancias, precios, "Consolidado")

with tab_retiro:
    c_ret = compras[compras['Fondo'].str.contains('fondo|retiro', case=False, na=False)]
    v_ret = ventas[ventas['Fondo'].str.contains('fondo|retiro', case=False, na=False)]
    g_ret = ganancias[ganancias['Fondo'].str.contains('fondo|retiro', case=False, na=False)]
    generar_vista_portfolio(c_ret, v_ret, g_ret, precios, "Retiro")