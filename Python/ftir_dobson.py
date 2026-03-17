import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from pyhdf.SD import SD, SDC

# ── Constants ─────────────────────────────────────────────────────────────
MOLEC_PER_CM2_TO_DU = 1 / 2.687e16


def read_hdf_file(filepath):
    """
    Read DATETIME and O3 column from a single NDACC HDF4 file.

    Parameters
    ----------
    filepath : str
        Path to the HDF4 file.

    Returns
    -------
    pd.DataFrame or None
        DataFrame with columns: datetime, o3_column, source_file.
        Returns None if file has no O3 data or fails to read.
    """
    try:
        ds = SD(filepath, SDC.READ)

        # Check this file actually has O3 data
        datasets = ds.datasets()
        if 'O3.COLUMN_ABSORPTION.SOLAR' not in datasets:
            #print(f"  SKIP (no O3): {os.path.basename(filepath)}")
            ds.end()
            return None

        # Read variables
        datetime_raw = ds.select('DATETIME')[:]
        o3_column    = ds.select('O3.COLUMN_ABSORPTION.SOLAR')[:]
        ds.end()

        # Convert DATETIME (fractional days since 2000-01-01) to timestamps
        base = pd.Timestamp('2000-01-01')
        timestamps = [base + pd.Timedelta(days=float(h)) for h in datetime_raw]

        df = pd.DataFrame({
            'datetime':    timestamps,
            'o3_column':   o3_column,
            'source_file': os.path.basename(filepath)
        })

        #print(f"  OK ({len(df)} obs): {os.path.basename(filepath)}")
        return df

    except Exception as e:
        print(f"  ERROR {os.path.basename(filepath)}: {e}")
        return None


def merge_hdf_directory(data_dir, output_file):
    """
    Read all HDF4 files in a directory, merge into a single DataFrame,
    and write to CSV.

    Parameters
    ----------
    data_dir : str
        Path to directory containing HDF4 files.
    output_file : str
        Path to output CSV file.

    Returns
    -------
    pd.DataFrame
        Merged and sorted DataFrame of all observations.
    """
    # ── List all HDF files ───────────────────────────────────────────────
    hdf_files = [
        os.path.join(data_dir, f)
        for f in os.listdir(data_dir)
        if f.endswith('.hdf')
    ]
    # print(f"Found {len(hdf_files)} HDF files\n")

    # ── Read all files ───────────────────────────────────────────────────
    dfs = []
    for filepath in sorted(hdf_files):
        df = read_hdf_file(filepath)
        if df is not None:
            dfs.append(df)

    if not dfs:
        raise ValueError("No valid O3 data found in any HDF files.")

    # ── Merge and sort ───────────────────────────────────────────────────
    merged = pd.concat(dfs, ignore_index=True)
    merged = merged.sort_values('datetime').reset_index(drop=True)

    # print(f"\nMerged dataset: {len(merged)} total observations")
    # print(f"Date range: {merged['datetime'].min()} → {merged['datetime'].max()}")
    # print(merged.head())

    # ── Ensure output directory exists ───────────────────────────────────
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # ── Write to CSV ─────────────────────────────────────────────────────
    merged.to_csv(output_file, index=False)
    # print(f"\nSaved to: {output_file}")

    return merged


def plot_ftir(merged, year_colors=None):
    """
    Plot O3 total column in Dobson Units vs day of year (day 200 onwards),
    with 1996-2019 as a grey background and individual years from 2020
    plotted in distinct colors.

    Parameters
    ----------
    merged : pd.DataFrame
        Merged DataFrame from merge_hdf_directory(), with columns:
        datetime, o3_column, source_file.
    year_colors : dict, optional
        Mapping of {year: color} for foreground years (2020+).
        Defaults to {2020: 'green', 2021: 'blue', 2022: 'orange', 2023: 'red'}.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    if year_colors is None:
        year_colors = {
            2020: 'green',
            2021: 'blue',
            2022: 'orange',
            2023: 'red',
        }

    # ── Prep data ─────────────────────────────────────────────────────────
    df = merged.copy()
    df['datetime']    = pd.to_datetime(df['datetime'])
    df['year']        = df['datetime'].dt.year
    df['day_of_year'] = df['datetime'].dt.dayofyear
    df['o3_du']       = df['o3_column'] * MOLEC_PER_CM2_TO_DU

    # ── Filter to day 200 onwards ─────────────────────────────────────────
    df = df[df['day_of_year'] >= 200]

    # ── Build figure ──────────────────────────────────────────────────────
    fig = go.Figure()

    # Background: pre-2020 (grey)
    bg = df[df['year'] < 2020]
    fig.add_trace(go.Scatter(
        x=bg['day_of_year'],
        y=bg['o3_du'],
        mode='markers',
        marker=dict(color='darkgrey', size=5, opacity=0.7),
        name='1996–2019',
        hovertemplate='Day: %{x}<br>O₃: %{y:.1f} DU<br>%{text}',
        text=bg['datetime'].dt.strftime('%Y-%m-%d')
    ))

    # Foreground: explicit colors per year
    for year, color in year_colors.items():
        yd = df[df['year'] == year]
        if len(yd) == 0:
            continue
        fig.add_trace(go.Scatter(
            x=yd['day_of_year'],
            y=yd['o3_du'],
            mode='markers',
            marker=dict(color=color, size=7, opacity=0.85),
            name=str(year),
            hovertemplate='Day: %{x}<br>O₃: %{y:.1f} DU<br>%{text}',
            text=yd['datetime'].dt.strftime('%Y-%m-%d')
        ))

    # ── Layout ────────────────────────────────────────────────────────────
    fig.update_layout(
        title='MIR-FTIR O3: Arrival Heights total column',
        xaxis=dict(title='Day of Year', range=[200, 366]),
        yaxis=dict(title='Dobson units'),
        legend=dict(title='Year', itemsizing='constant'),
        hovermode='closest',
        template='plotly_white',
        width=1000,
        height=600
    )

    return fig


if __name__ == "__main__":
    DATA_DIR    = r"C:\Users\ANTNZDEV\michaelmeredythyoung\github\nzaea-atmospheric\data\ftir"
    OUTPUT_FILE = r"C:\Users\ANTNZDEV\michaelmeredythyoung\github\nzaea-atmospheric\data\ftir\merged_data\ftir_o3_merged.csv"

    merged = merge_hdf_directory(DATA_DIR, OUTPUT_FILE)
