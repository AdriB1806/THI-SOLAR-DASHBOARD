# THI Photovoltaic Dashboard

A real-time solar PV monitoring dashboard built with Streamlit, designed to match the THI Photovoltaic Dashboard interface.

## Features

- **Live Power Monitoring**: Real-time gauge showing current power generation
- **Energy Today**: Total energy produced today with trend visualization
- **AC/DC Power Display**: Separate displays for AC and DC power output
- **Efficiency Metrics**: System efficiency percentage and UV index
- **Daily Production Curve**: Hour-by-hour visualization of energy production
- **Environmental Impact**: Total energy generated and CO2 emissions avoided
- **Temperature Monitoring**: System and ambient temperature tracking

## Installation and Usage

1. Clone this repository:
```bash
git clone https://github.com/AdriB1806/THI-SOLAR-DASHBOARD
cd THI-SOLAR-DASHBOARD
```

2. Install dependencies (recommended: virtualenv)


```bash
./setup_venv.sh
source .venv/bin/activate
```

3. Before running the dashboard, test if you're connected to THI network:
```bash
./test_network.sh
```

4. Run the Dashboard
```bash
streamlit run app.py
```

Note: `python app.py` will fail because this is a Streamlit app; it must be started via `streamlit run`.

The dashboard will open in your browser at `http://localhost:8501`

### Testing and Validation

Parallel to running the testing network script up , we created also another script to do a mroe detailed testing and validation of our web app before deployment. To do this you will have to run the script:

```bash
python validate.py                    # Generate all formats (HTML, Markdown, DOCX)
    python validate.py --html-only        # Generate HTML only
    python validate.py --quick            # Skip slow checks (Streamlit smoke test)

```

**Note: There might be some issues with importing docx so try to run while generating html only.**

This will also generate a report with detailed analysis.


### Theme (night shift)

The app is configured with an enterprise light theme by default (THI blue accents, high contrast). You can still switch Streamlit themes via the Streamlit menu (top-right) if you want a different look.


### Logo

If you add a file named `thi_logo.png` in the project root, the app will display it in the header automatically. If it is missing, the app shows a simple “THI” fallback.

**Network Status:**
- ✓ **On THI Network / VPN**: Dashboard fetches and displays live PV data
- ❌ **Not on THI Network / VPN**: The app shows an error (no fallback)

## Data Source

The dashboard fetches data from the THI FTP server. It downloads `pvdaten/pv.csv` on each refresh.

Important: this repository is configured to use live data only (no sample fallback). Ensure students are on the THI network or connected to the THI VPN before running.

Connection URL (inside `app.py`):

```python
import ftplib

ftp = ftplib.FTP('jupyterhub-wi', timeout=10)
ftp.login('ftpuser', 'ftpuser123')
ftp.cwd('pvdaten')
with open('pv.csv', 'wb') as f:
    ftp.retrbinary('RETR pv.csv', f.write)
ftp.quit()
```

## Troubleshooting

### Error: "ValueError: numpy.dtype size changed" (binary incompatibility)

This happens when `numpy` and compiled packages like `pandas`/`pyarrow` are installed from incompatible wheels (often due to mixing global site-packages or upgrading only one dependency).

Fix (recommended): delete the venv and recreate it cleanly:

```bash
rm -rf .venv
./setup_venv.sh
source .venv/bin/activate
streamlit run app.py
```

If you're using a non-venv global Python installation, switch to the venv approach above. It avoids system Python conflicts and is the easiest workflow for students.

## Data storage, retention, and caching

### What gets stored locally

The app stores **historical readings** in a local SQLite database file:

- **Database file**: `pv_data.db` (created in the current working directory)
- **Table**: `pv_readings`
- **Write behavior**: every time live data is fetched successfully, a row is inserted via `log_data()`

Stored fields include:

- `timestamp` (defaults to SQLite `CURRENT_TIMESTAMP`)
- `live_power`, `energy_today`, `ac_power`, `dc_power`, `efficiency`, `uv_index`
- `total_energy`, `system_temp`, `co2_avoided`, `ambient_temp`
- `data_source` (e.g. `live`)

### Retention policy (current behavior)

There is **no automatic cleanup** of `pv_data.db`. Data is retained indefinitely until you delete the file.

To reset all stored history:

```bash
rm -f pv_data.db
```

If you enable auto-refresh for long periods, the database will grow over time.

### Temporary/local files

When live data is available, the app downloads the FTP file to a local file:

- `pv.csv` (downloaded from FTP on each refresh/run, then read by pandas; overwritten on each successful fetch)

This file is only a local working copy to make CSV parsing simple and reliable. The long-term historical storage is `pv_data.db`.

Tip for students: don’t commit `pv.csv` or `pv_data.db` to git. They are generated locally.

If you don’t want this file left on disk, you can delete it after running, or adjust `fetch_pv_data()` to download into a temp directory.

### Caching and refresh behavior

- **Live fetch**: `fetch_pv_data()` downloads `pv.csv` each time the app runs/reruns (no sample fallback).
- **Manual refresh**: the dashboard has a refresh button that triggers a rerun.
- **Auto-refresh**: there is an optional auto-refresh toggle with a selectable interval (10s/30s/60s/120s). When enabled, the app sleeps for the interval and then reruns.

## Data export

In the **Historical Data** view, you can download the currently queried history as:

- CSV
- JSON

These downloads are generated on demand from the SQLite data.

## Security notes

- The FTP URL (including credentials) is currently hard-coded in the app. Treat this as sensitive.
- If you plan to share the project, consider moving credentials to environment variables and/or Streamlit secrets.
- Be careful not to commit generated files like `pv_data.db` or `test.txt` if they may contain sensitive information.

## Customization

### Updating Data Source
Modify the `fetch_pv_data()` function in `app.py` to connect to your specific data source.

### Adjusting Metrics
Update the metric calculations in the `generate_sample_data()` function to match your PV system specifications.

### Styling
Customize colors and layout in the CSS section at the top of `app.py`.

## Data Format

The dashboard expects data with the following fields:
- `live_power`: Current power generation (kW)
- `energy_today`: Total energy today (kWh)
- `ac_power`: AC power output (kW)
- `dc_power`: DC power output (kW)
- `efficiency`: System efficiency (%)
- `uv_index`: Current UV index
- `total_energy`: Lifetime energy production (kWh)
- `system_temp`: System temperature (°C)
- `co2_avoided`: Total CO2 emissions avoided (kg)
- `ambient_temp`: Ambient temperature (°C)
- `production_curve`: Hourly production data

## Auto-Refresh

The dashboard supports optional auto-refresh from the UI. Data fetching is cached for 60 seconds via `@st.cache_data(ttl=60)`.


## License

MIT License

## Support

For issues or questions, please open an issue on GitHub.
