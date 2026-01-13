import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import urllib.request
import ftplib
import os
from pathlib import Path
import sqlite3
import json

APP_DIR = Path(__file__).resolve().parent
THI_LOGO_PATH = APP_DIR / "thi_logo.png"

# Default UI: normal/light Streamlit styling with THI blue accents.
# Set to True if you explicitly want to load the licensed DayNight template CSS.
USE_TEMPLATE_CSS = False

TEMPLATE_CSS_PATHS = [
    APP_DIR / "templatemo-daynight-style.css",
    APP_DIR / "assets" / "templatemo-daynight-style.css",
    APP_DIR / "assets" / "daynight.css",
]

STREAMLIT_TEMPLATE_OVERRIDES_PATHS = [
    APP_DIR / "streamlit-daynight-overrides.css",
    APP_DIR / "assets" / "streamlit-daynight-overrides.css",
]

# Page configuration
st.set_page_config(
    page_title=" THI Photovoltaic Dashboard",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)


def _fmt_number(value, decimals: int = 2, thousands: bool = False) -> str:
    try:
        number = float(value)
    except Exception:
        return "—"

    if thousands:
        return f"{number:,.{decimals}f}"
    return f"{number:.{decimals}f}"


def _inject_css() -> None:
    """Inject CSS into the Streamlit app.

    If a template CSS file is present in the repo, load it from disk (user-provided)
    and apply small variable overrides for THI branding.

    Returns True when a template stylesheet was loaded.
    """
    if not USE_TEMPLATE_CSS:
        return False

    for css_path in TEMPLATE_CSS_PATHS:
        if css_path.exists():
            css = css_path.read_text(encoding="utf-8")
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
            st.markdown(
                """
<style>
    /* THI brand accents (overrides for template CSS vars if they exist) */
    :root {
        --accent: #005AA3;
        --accent-hover: #0B6FC7;
    }
</style>
                """,
                unsafe_allow_html=True,
            )

            for override_path in STREAMLIT_TEMPLATE_OVERRIDES_PATHS:
                if override_path.exists():
                    override_css = override_path.read_text(encoding="utf-8")
                    st.markdown(f"<style>{override_css}</style>", unsafe_allow_html=True)
                    break

            return True

    return False


_template_loaded = _inject_css()

# Custom CSS to match the dashboard design
if not _template_loaded:
    st.markdown("""
<style>
    :root {
        /* Enterprise light theme (THI blue accents) */
        --thi-primary: #005AA3;
        --thi-primary-hover: #0B6FC7;
        --thi-primary-soft: rgba(0, 90, 163, 0.08);
        --accent: var(--thi-primary);
        --accent-hover: var(--thi-primary-hover);
        --accent-light: var(--thi-primary-soft);
        --thi-bg: #F6F8FB;
        --thi-surface: #FFFFFF;
        --thi-card: #FFFFFF;
        --thi-text: #0F172A;
        --thi-muted: #475569;
        --thi-border: rgba(15, 23, 42, 0.10);
        --thi-success: #16a34a;
        --thi-shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.06);
        --thi-shadow-md: 0 10px 28px rgba(15, 23, 42, 0.08);
    }

    html, body, [data-testid="stAppViewContainer"], .stApp {
        background: var(--thi-bg) !important;
        color: var(--thi-text);
        font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, "Noto Sans", "Apple Color Emoji", "Segoe UI Emoji";
    }

    /* Make the content area feel like a modern admin layout */
    [data-testid="stAppViewContainer"] .main {
        padding-top: 1.25rem;
        padding-bottom: 2rem;
    }

    .main {
        background: transparent;
        padding: 1.25rem;
    }
    
    .dashboard-container {
        background: var(--thi-surface);
        border-radius: 14px;
        padding: 1.25rem;
        border: 1px solid var(--thi-border);
        box-shadow: var(--thi-shadow-md);
    }
    
    .metric-card {
        background: var(--thi-card);
        border-radius: 16px;
        padding: 1.25rem;
        text-align: center;
        box-shadow: var(--thi-shadow-sm);
        height: 100%;
        border: 1px solid var(--thi-border);
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    
    .metric-card:hover {
        border-color: rgba(0, 90, 163, 0.55);
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.10);
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 750;
        color: var(--thi-text);
        margin: 0.5rem 0;
    }

    /* Template-like classnames (so the UI still looks correct without the template CSS) */
    .page-header {
        background: transparent;
        margin-bottom: 0.5rem;
    }

    .greeting {
        margin: 0;
        font-size: 2.2rem;
        font-weight: 800;
        color: var(--thi-text);
        letter-spacing: -0.02em;
    }

    .greeting-sub {
        margin: 0.35rem 0 0;
        font-weight: 650;
        color: var(--thi-muted);
        letter-spacing: 0.06em;
    }

    .stat-card {
        background: var(--thi-card);
        border-radius: 16px;
        padding: 1.25rem;
        text-align: center;
        box-shadow: var(--thi-shadow-sm);
        height: 100%;
        border: 1px solid var(--thi-border);
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .stat-card:hover {
        border-color: rgba(0, 90, 163, 0.55);
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.10);
    }
    .stat-label {
        font-size: 0.85rem;
        font-weight: 700;
        color: var(--thi-muted);
        letter-spacing: 0.06em;
    }
    .stat-value {
        font-size: 2.2rem;
        font-weight: 750;
        color: var(--thi-text);
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: var(--thi-muted);
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.08em;
    }
    
    .header-title {
        font-size: 2.4rem;
        font-weight: 800;
        color: var(--thi-text);
        text-align: center;
        margin: 0;
        padding: 0.75rem 0;
        letter-spacing: -0.5px;
    }
    
    .header-subtitle {
        font-size: 1.05rem;
        color: var(--thi-muted);
        text-align: center;
        margin-top: -0.5rem;
        font-weight: 500;
        letter-spacing: 0.14em;
    }
    
    .live-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        background-color: var(--thi-success);
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .gauge-container {
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
    }
    
    .stPlotlyChart {
        background: var(--thi-card);
        border-radius: 12px;
        padding: 0.75rem;
        border: 1px solid var(--thi-border);
    }

    /* Streamlit widgets (keep high contrast so letters never disappear) */
    .stTextInput input, .stNumberInput input, .stDateInput input,
    .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
        background: #ffffff !important;
        color: var(--thi-text) !important;
        border-radius: 12px !important;
        border: 1px solid var(--thi-border) !important;
        box-shadow: none !important;
    }

    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
        border-color: rgba(0, 90, 163, 0.45) !important;
        box-shadow: 0 0 0 4px var(--thi-primary-soft) !important;
    }

    /* Buttons */
    .stButton > button {
        background: var(--thi-primary) !important;
        color: #ffffff !important;
        border: 1px solid rgba(0, 0, 0, 0) !important;
        border-radius: 12px !important;
        padding: 0.65rem 0.95rem !important;
        font-weight: 650 !important;
        box-shadow: var(--thi-shadow-sm) !important;
    }
    .stButton > button:hover {
        background: var(--thi-primary-hover) !important;
    }
    
    .refresh-button {
        background: var(--thi-primary);
        color: white;
        padding: 0.75rem 2rem;
        border-radius: 10px;
        border: none;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s ease;
    }
    
    .refresh-button:hover {
        background: var(--thi-primary-hover);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid var(--thi-border);
    }
    
    [data-testid="stSidebar"] .stRadio > label {
        color: var(--thi-text);
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    [data-testid="stSidebar"] .stRadio > div {
        background: transparent;
        padding: 1rem;
        border-radius: 10px;
    }

    /* Sidebar nav options styled like admin menu items */
    [data-testid="stSidebar"] div[role="radiogroup"] label {
        border-radius: 12px;
        padding: 0.55rem 0.75rem;
        margin: 0.25rem 0;
        border: 1px solid rgba(0, 0, 0, 0);
        transition: background 0.15s ease, border-color 0.15s ease;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: var(--thi-primary-soft);
        border-color: rgba(0, 90, 163, 0.18);
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
        background: rgba(0, 90, 163, 0.12);
        border-color: rgba(0, 90, 163, 0.28);
    }

    /* Sidebar header + tip (always readable in light mode) */
    [data-testid="stSidebar"] .nav-title {
        color: var(--thi-primary) !important;
        font-weight: 800;
        letter-spacing: -0.01em;
    }

    [data-testid="stSidebar"] .nav-subtitle {
        color: var(--thi-muted) !important;
        font-weight: 600;
    }

    [data-testid="stSidebar"] .sidebar-tip {
        color: var(--thi-muted) !important;
        background: rgba(0, 90, 163, 0.06);
        border: 1px solid rgba(0, 90, 163, 0.14);
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

def fetch_pv_data():
    """Fetch live PV data from FTP `pvdaten/pv.csv` and parse into dashboard fields.

    This function requires network access to `jupyterhub-wi` (THI network or VPN).
    It will NOT fall back to local/sample CSVs. If the FTP fetch fails the app will
    show an error and instruct the user to connect to the THI network.
    """
    data_file = 'pv.csv'
    data_source = 'live'

    def _download_ftp_csv(local_path: str, timeout_s: int = 10) -> None:
        host = 'jupyterhub-wi'
        user = 'ftpuser'
        password = 'ftpuser123'
        remote_path = 'pvdaten/pv.csv'

        ftp = ftplib.FTP(host, timeout=timeout_s)
        try:
            ftp.login(user=user, passwd=password)
            remote_dir, remote_name = os.path.split(remote_path)
            if remote_dir:
                ftp.cwd(remote_dir)
            with open(local_path, 'wb') as f:
                ftp.retrbinary(f'RETR {remote_name}', f.write)
        finally:
            try:
                ftp.quit()
            except Exception:
                pass

    # Attempt to download the CSV from the FTP server (THI network/VPN required)
    try:
        _download_ftp_csv(data_file, timeout_s=10)
        st.success('✓ Connected to THI network — using live pv.csv')
    except Exception as e:
        st.error('❌ Live data unavailable')
        st.error('Connect to THI Wi‑Fi (on campus) or THI VPN, then refresh.')
        st.error(str(e))
        st.stop()

    # Parse pv.csv with pandas
    try:
        df = pd.read_csv(data_file)
        # Use the last row as the most recent snapshot
        row = df.iloc[-1]

        # Collect PV-point columns
        prod_cols = [c for c in df.columns if c.startswith('energy_ptot_') and c.endswith('_kWh')]
        # Sort by numeric index in the column name (energy_ptot_<N>_kWh)
        def _ptot_index(col):
            try:
                return int(col.split('_')[2])
            except Exception:
                return 10**9
        prod_cols = sorted(prod_cols, key=_ptot_index)
        production_values = [float(row[c]) for c in prod_cols if pd.notna(row[c])]

        # Map fields to dashboard structure
        live_power = float(production_values[-1]) if production_values else 0.0
        energy_today = float(row.get('total_energy_kWh', sum(production_values)))
        total_energy = float(row.get('total_energy_kWh', 0.0))
        co2_avoided = total_energy * 0.366

        parsed = {
            'live_power': live_power,
            'energy_today': energy_today,
            'ac_power': live_power * 0.92 if live_power else 0.0,
            'dc_power': live_power * 1.02 if live_power else 0.0,
            'efficiency': 92.0,
            'uv_index': 0.0,
            'total_energy': total_energy,
            'system_temp': 0.0,
            'co2_avoided': co2_avoided,
            'ambient_temp': 0.0,
            'production_curve': {
                # These values represent per-point energy columns, not hourly time.
                'hours': list(range(len(production_values))),
                'values': production_values,
            },
            'data_timestamp': str(row.get('timestamp', '')),
            'data_source': data_source,
        }

        log_data(parsed, data_source)
        return parsed
    except Exception as e:
        st.error(f'Error parsing pv.csv: {e}')
        return {
            'live_power': 0.0,
            'energy_today': 0.0,
            'ac_power': 0.0,
            'dc_power': 0.0,
            'efficiency': 0.0,
            'uv_index': 0.0,
            'total_energy': 0.0,
            'system_temp': 0.0,
            'co2_avoided': 0.0,
            'ambient_temp': 0.0,
            'production_curve': {
                'hours': [datetime.now().replace(hour=h, minute=0, second=0) for h in range(24)],
                'values': [0] * 24
            }
        }

def parse_pv_file(content):
    """Parse the actual PV data file format"""
    try:
        data = {}
        lines = content.strip().split('\n')
        
        # Try to parse key:value format
        for line in lines:
            if ':' in line:
                key, value = line.strip().split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()
                
                # Try to convert to float if possible
                try:
                    data[key] = float(value)
                except:
                    data[key] = value
        
        # Map to expected format if keys exist
        # Adjust these mappings based on actual file keys
        if data:
            # Generate hourly data if not provided
            now = datetime.now()
            hours = [(now.replace(hour=h, minute=0, second=0)) for h in range(24)]
            
            # Try to get current production curve or generate it
            production = generate_production_curve()
            
            return {
                'live_power': data.get('live_power', data.get('current_power', 5.2)),
                'energy_today': data.get('energy_today', data.get('daily_energy', 35.8)),
                'ac_power': data.get('ac_power', 4.9),
                'dc_power': data.get('dc_power', 5.5),
                'efficiency': data.get('efficiency', 87),
                'uv_index': data.get('uv_index', 7),
                'total_energy': data.get('total_energy', data.get('lifetime_energy', 12345)),
                'system_temp': data.get('system_temp', data.get('temperature', 45)),
                'co2_avoided': data.get('co2_avoided', 8900),
                'ambient_temp': data.get('ambient_temp', data.get('ambient_temperature', 25)),
                'production_curve': {
                    'hours': hours,
                    'values': production
                }
            }
        
        return None
    except Exception as e:
        st.error(f"Parse error: {e}")
        return None

def generate_production_curve():
    """Generate realistic production curve"""
    import random
    production = []
    for h in range(24):
        if 6 <= h <= 20:  # Daylight hours
            peak = 12
            width = 4
            value = 8 * np.exp(-((h - peak) ** 2) / (2 * width ** 2))
            production.append(value + random.uniform(-0.5, 0.5))
        else:
            production.append(0)
    return production

def generate_sample_data():
    """Generate sample data matching the dashboard format"""
    import random
    
    # Generate hourly data for today
    now = datetime.now()
    hours = [(now.replace(hour=h, minute=0, second=0)) for h in range(24)]
    
    # Generate realistic production curve (bell curve peaking at noon)
    production = []
    for h in range(24):
        if 6 <= h <= 20:  # Daylight hours
            # Bell curve formula
            peak = 12
            width = 4
            value = 8 * np.exp(-((h - peak) ** 2) / (2 * width ** 2))
            production.append(value + random.uniform(-0.5, 0.5))
        else:
            production.append(0)
    
    # Current values
    current_hour = now.hour
    live_power = production[current_hour] if 0 <= current_hour < len(production) else 5.2
    
    return {
        'live_power': live_power,
        'energy_today': 35.8,
        'ac_power': 4.9,
        'dc_power': 5.5,
        'efficiency': 87,
        'uv_index': 7,
        'total_energy': 12345,
        'system_temp': 45,
        'co2_avoided': 8900,
        'ambient_temp': 25,
        'production_curve': {
            'hours': hours,
            'values': production
        }
    }

def create_gauge_chart(value, max_value, title, unit="", decimals: int = 2):
    """Create a gauge chart for live power"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 16, 'color': '#64748b'}},
        number={
            'suffix': f" {unit}",
            'valueformat': f'.{decimals}f',
            'font': {'size': 36, 'color': '#1e40af'},
        },
        gauge={
            'axis': {'range': [None, max_value], 'tickwidth': 2, 'tickcolor': "#94a3b8"},
            'bar': {'color': "#005AA3"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#cbd5e1",
            'steps': [
                {'range': [0, max_value * 0.33], 'color': '#EAF2FB'},
                {'range': [max_value * 0.33, max_value * 0.66], 'color': '#D5E6F7'},
                {'range': [max_value * 0.66, max_value], 'color': '#B9D7F0'}
            ],
        }
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='rgba(255, 255, 255, 0)',
        plot_bgcolor='rgba(255, 255, 255, 0)',
        font={'color': "#0F172A", 'family': "Arial"}
    )
    
    return fig

def create_production_curve(hours, values):
    """Create a chart for the values returned by the live data source.

    For `pv.csv`, the values represent per-point energy columns (energy_ptot_*_kWh),
    not hourly time series.
    """
    df = pd.DataFrame({'X': hours, 'Value': values})

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['X'],
        y=df['Value'],
        marker=dict(color='rgba(0, 90, 163, 0.75)'),
        name='Energy (kWh)'
    ))

    fig.update_layout(
        title="PV POINT ENERGIES (energy_ptot_*_kWh)",
        title_font=dict(size=14, color='#475569', family='Arial'),
        xaxis=dict(
            title="PV point index",
            showgrid=False,
            color='#475569'
        ),
        yaxis=dict(
            title="kWh",
            showgrid=True,
            gridcolor='rgba(15, 23, 42, 0.08)',
            color='#475569'
        ),
        plot_bgcolor='#FFFFFF',
        paper_bgcolor='rgba(255, 255, 255, 0)',
        height=300,
        margin=dict(l=40, r=40, t=50, b=40),
        hovermode='x unified',
        showlegend=False
    )

    return fig

def create_circular_metric(value, label, max_value=100, unit=""):
    """Create circular progress indicators"""
    percentage = (value / max_value) * 100 if max_value > 0 else 0
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'suffix': unit, 'font': {'size': 24, 'color': '#1e40af'}},
        gauge={
            'axis': {'range': [None, max_value], 'visible': False},
            'bar': {'color': "#3b82f6", 'thickness': 0.7},
            'bgcolor': "#e0e7ff",
            'borderwidth': 0,
        },
        title={'text': label, 'font': {'size': 12, 'color': '#64748b'}}
    ))
    
    fig.update_layout(
        height=150,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor='rgba(224, 231, 255, 0.3)',
    )
    
    return fig

def show_historical_view():
    """Display historical data analysis view"""
    st.markdown('''
    <div class="page-header">
        <h1 class="greeting">Historical Data</h1>
        <p class="greeting-sub">PHOTOVOLTAIC SYSTEM RECORDS</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Time range selector
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        time_range = st.selectbox(
            "Time Range",
            options=[6, 12, 24, 48, 168],  # hours
            format_func=lambda x: f"Last {x} hours" if x < 24 else f"Last {x//24} days",
            index=2
        )
    
    with col2:
        metric_to_view = st.selectbox(
            "Metric",
            options=["live_power", "energy_today", "efficiency", "system_temp", "ambient_temp", "ac_power", "dc_power"],
            format_func=lambda x: x.replace("_", " ").title()
        )
    
    with col3:
        if st.button("🔄 Refresh Data"):
            st.rerun()
    
    # Fetch historical data
    historical_df = get_historical_data(time_range)
    
    # If no data, show a clear message (no sample fallback)
    if historical_df.empty:
        st.warning("No historical data yet.")
        st.info("Keep the Live Dashboard running while connected to THI Wi‑Fi/VPN to collect readings into `pv_data.db`.")
        return
    
    # Statistics cards
    st.markdown("### 📈 Summary Statistics")
    stats = get_data_statistics(time_range)
    
    # If no stats from DB, calculate from dataframe
    if not stats or stats.get('reading_count', 0) == 0:
        stats = {
            'reading_count': len(historical_df),
            'avg_power': historical_df['live_power'].mean(),
            'max_power': historical_df['live_power'].max(),
            'min_power': historical_df['live_power'].min(),
            'avg_efficiency': historical_df['efficiency'].mean(),
            'avg_daily_energy': historical_df['energy_today'].mean()
        }
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Total Readings</div>
            <div class="stat-value">{stats.get('reading_count', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Avg Power</div>
            <div class="stat-value">{stats.get('avg_power', 0):.2f} kW</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Max Power</div>
            <div class="stat-value">{stats.get('max_power', 0):.2f} kW</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Min Power</div>
            <div class="stat-value">{stats.get('min_power', 0):.2f} kW</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Avg Efficiency</div>
            <div class="stat-value">{stats.get('avg_efficiency', 0):.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Historical trend chart
    st.markdown(f"### 📊 {metric_to_view.replace('_', ' ').title()} Trend")
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=historical_df['timestamp'],
        y=historical_df[metric_to_view],
        mode='lines+markers',
        name=metric_to_view.replace('_', ' ').title(),
        line=dict(color='#3b82f6', width=2),
        marker=dict(size=6, color='#3b82f6'),
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.2)'
    ))
    
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title=metric_to_view.replace('_', ' ').title(),
        plot_bgcolor='rgba(255, 255, 255, 0.9)',
        paper_bgcolor='rgba(224, 231, 255, 0.3)',
        height=400,
        hovermode='x unified',
        showlegend=False
    )
    
    st.plotly_chart(fig, width="stretch")
    
    # Data table
    st.markdown("### 📋 Detailed Records")
    
    # Format the dataframe for display
    display_df = historical_df.copy()
    display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Select columns to display
    columns_to_show = ['timestamp', 'live_power', 'energy_today', 'efficiency', 
                       'ac_power', 'dc_power', 'system_temp', 'ambient_temp', 'data_source']
    
    display_df = display_df[columns_to_show]
    
    # Rename columns for better readability
    display_df.columns = ['Time', 'Live Power (kW)', 'Energy Today (kWh)', 'Efficiency (%)',
                          'AC Power (kW)', 'DC Power (kW)', 'System Temp (°C)', 
                          'Ambient Temp (°C)', 'Source']
    
    st.dataframe(
        display_df,
        width="stretch",
        height=400
    )
    
    # Download options
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        csv = historical_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"pv_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        json_data = historical_df.to_json(orient='records', date_format='iso')
        st.download_button(
            label="📥 Download JSON",
            data=json_data,
            file_name=f"pv_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

# Import numpy for calculations
import numpy as np

# Database functions
def init_database():
    """Initialize SQLite database for historical data"""
    conn = sqlite3.connect('pv_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pv_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            live_power REAL,
            energy_today REAL,
            ac_power REAL,
            dc_power REAL,
            efficiency REAL,
            uv_index REAL,
            total_energy REAL,
            system_temp REAL,
            co2_avoided REAL,
            ambient_temp REAL,
            data_source TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def log_data(data, source="sample"):
    """Log current data to database"""
    try:
        conn = sqlite3.connect('pv_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO pv_readings 
            (live_power, energy_today, ac_power, dc_power, efficiency, 
             uv_index, total_energy, system_temp, co2_avoided, ambient_temp, data_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['live_power'],
            data['energy_today'],
            data['ac_power'],
            data['dc_power'],
            data['efficiency'],
            data['uv_index'],
            data['total_energy'],
            data['system_temp'],
            data['co2_avoided'],
            data['ambient_temp'],
            source
        ))
        
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Error logging data: {e}")

def get_historical_data(hours=24):
    """Retrieve historical data from database"""
    try:
        conn = sqlite3.connect('pv_data.db')
        
        query = f'''
            SELECT * FROM pv_readings 
            WHERE timestamp >= datetime('now', '-{hours} hours')
            ORDER BY timestamp DESC
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df
    except Exception as e:
        st.error(f"Error retrieving historical data: {e}")
        return pd.DataFrame()

def get_data_statistics(hours=24):
    """Get statistical summary of historical data"""
    try:
        conn = sqlite3.connect('pv_data.db')
        
        query = f'''
            SELECT 
                COUNT(*) as reading_count,
                AVG(live_power) as avg_power,
                MAX(live_power) as max_power,
                MIN(live_power) as min_power,
                AVG(efficiency) as avg_efficiency,
                SUM(energy_today) / COUNT(*) as avg_daily_energy
            FROM pv_readings 
            WHERE timestamp >= datetime('now', '-{hours} hours')
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df.iloc[0].to_dict() if not df.empty else {}
    except Exception as e:
        st.error(f"Error getting statistics: {e}")
        return {}

# Main dashboard
def main():
    # Initialize database
    init_database()
    
    # Sidebar for navigation
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-header" style="text-align: center; padding: 1rem; margin-bottom: 1.25rem;">
            <h2 class="nav-title" style="margin: 0;">📊 Navigation</h2>
            <p class="nav-subtitle" style="font-size: 0.9rem; margin-top: 0.5rem;">Switch between views</p>
        </div>
        """, unsafe_allow_html=True)
        
        view_mode = st.radio(
            "Select View",
            ["🔴 Live Dashboard", "📈 Historical Data"],
            label_visibility="collapsed",
            index=0
        )
        
        # Clean up the view mode string
        view_mode = "Historical Data" if "Historical" in view_mode else "Live Dashboard"
        
        st.markdown("---")
        st.markdown("""
        <div class="sidebar-tip" style="font-size: 0.85rem; padding: 1rem;">
            <p style="margin: 0 0 0.35rem 0;"><strong>💡 Tip:</strong></p>
            <p style="margin: 0;">Historical Data shows past readings and allows you to download data as CSV or JSON.</p>
        </div>
        """, unsafe_allow_html=True)
    
    if view_mode == "Historical Data":
        show_historical_view()
        return
    
    # Header with logo and title
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        # THI Logo
        if THI_LOGO_PATH.exists():
            st.image(str(THI_LOGO_PATH), width=180)
        else:
            st.markdown('<div style="font-size: 2.5rem; color: #3b82f6; margin-top: 1rem;">🏢 THI</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('''
        <div class="page-header" style="text-align: center; margin-top: 0.5rem;">
            <h1 class="greeting">THI Dashboard</h1>
            <p class="greeting-sub">PHOTOVOLTAIC SYSTEM MONITORING</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        # Live status with refresh button
        st.markdown('''
        <div style="text-align: right; margin-top: 2rem;">
            <div style="font-size: 0.9rem; color: #64748b; margin-bottom: 0.5rem;">
                <span class="live-indicator"></span>LIVE
            </div>
        </div>
        ''', unsafe_allow_html=True)
        if st.button('⟳ Refresh', width="stretch"):
            st.rerun()
    
    # Fetch data (live-only). If not connected, `fetch_pv_data()` will show an error and stop.
    data = fetch_pv_data()

    # Display formatting (live dashboard only). Keep raw values in `data` for logging/history.
    display = {
        'live_power': _fmt_number(data.get('live_power'), 2),
        'energy_today': _fmt_number(data.get('energy_today'), 2),
        'ac_power': _fmt_number(data.get('ac_power'), 2),
        'dc_power': _fmt_number(data.get('dc_power'), 2),
        'efficiency': _fmt_number(data.get('efficiency'), 1),
        'uv_index': _fmt_number(data.get('uv_index'), 1),
        'total_energy': _fmt_number(data.get('total_energy'), 2, thousands=True),
        'system_temp': _fmt_number(data.get('system_temp'), 1),
        'co2_avoided': _fmt_number(data.get('co2_avoided'), 0, thousands=True),
        'ambient_temp': _fmt_number(data.get('ambient_temp'), 1),
    }

    if 'data_timestamp' in data and data['data_timestamp']:
        st.caption(f"Last data timestamp: {data['data_timestamp']} (source: {data.get('data_source', 'live')})")
    
    # Top row - 4 main metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Live Power Gauge
        fig_gauge = create_gauge_chart(float(data['live_power']), 10, "LIVE POWER", "kW", decimals=2)
        st.plotly_chart(fig_gauge, width="stretch", key="live_power")
    
    with col2:
        # Energy Today
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">ENERGY TODAY</div>
            <div class="stat-value">{display['energy_today']} kWh</div>
            <div style="margin-top: 1rem;">
                <svg width="100%" height="40" viewBox="0 0 200 40">
                    <polyline points="0,30 40,25 80,20 120,15 160,18 200,10" 
                              stroke="var(--thi-primary)" stroke-width="2" fill="none"/>
                    <polyline points="0,30 40,25 80,20 120,15 160,18 200,10 200,40 0,40" 
                              fill="var(--thi-primary-soft)"/>
                </svg>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # AC/DC Power
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label" style="margin-bottom: 1rem;">POWER</div>
            <div style="display: flex; justify-content: space-around;">
                <div>
                    <div class="stat-label">AC Power (kW)</div>
                    <div class="stat-value" style="font-size: 1.5rem;">{display['ac_power']}</div>
                </div>
                <div>
                    <div class="stat-label">DC Power (kW)</div>
                    <div class="stat-value" style="font-size: 1.5rem;">{display['dc_power']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # Efficiency and UV Index
        st.markdown(f"""
        <div class="stat-card">
            <div style="margin-bottom: 1rem;">
                <div class="stat-label">Efficiency</div>
                <div class="stat-value">{display['efficiency']}%</div>
            </div>
            <div style="margin-top: 1rem; padding-top: 1rem; border-top: 2px solid #cbd5e1;">
                <div class="stat-label">☀️ UV INDEX</div>
                <div class="stat-value" style="font-size: 1.5rem;">{display['uv_index']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Middle row - Production curve and smaller metrics
    col1, col2, col3 = st.columns([3, 1.5, 1.5])
    
    with col1:
        # Production curve
        rounded_curve_values = [round(float(v), 2) for v in data['production_curve']['values']]
        fig_curve = create_production_curve(
            data['production_curve']['hours'],
            rounded_curve_values
        )
        st.plotly_chart(fig_curve, width="stretch", key="production_curve")
    
    with col2:
        # Total Energy
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">TOTAL ENERGY (kWh)</div>
            <div class="stat-value">{display['total_energy']}</div>
            <div class="stat-label">kWh</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # System Temperature
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">SYSTEM TEMP.</div>
            <div class="stat-value">{display['system_temp']}°C</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # CO2 Avoided
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">CO2 AVOIDED</div>
            <div class="stat-value">{display['co2_avoided']}</div>
            <div class="stat-label">kg</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Ambient Temperature
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">AMBIENT TEMP.</div>
            <div class="stat-value">{display['ambient_temp']}°C</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Auto-refresh with interactive controls
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        st.markdown(f"<div style='color: #64748b; font-size: 0.9rem; margin-top: 0.5rem;'>Last updated: {current_time}</div>", unsafe_allow_html=True)
    
    with col2:
        auto_refresh = st.checkbox("Auto-refresh", value=False, key="auto_refresh_toggle")
    
    with col3:
        if auto_refresh:
            refresh_interval = st.selectbox(
                "Interval",
                options=[10, 30, 60, 120],
                format_func=lambda x: f"{x}s",
                index=1,
                key="refresh_interval"
            )
    
    # Auto-refresh logic
    if auto_refresh:
        import time
        time.sleep(refresh_interval)
        st.rerun()

if __name__ == "__main__":
    main()
