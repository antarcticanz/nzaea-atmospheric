import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from pyhdf.SD import SD, SDC

# ── Constants ─────────────────────────────────────────────────────────────
MOLEC_PER_CM2_TO_DU = 1 / 2.687e16


def read_hdf_file(filepath, instrument="FTIR"):
    """
    Read DATETIME and O3 column from a single NDACC HDF4 file.

    Parameters
    ----------
    filepath : str
        Path to the HDF4 file.
    instrument : str
        Instrument type. Supported: "FTIR", "DOBSON".

    Returns
    -------
    pd.DataFrame or None
        DataFrame with columns: datetime, o3_column, source_file.
        Returns None if file has no O3 data or fails to read.
    """
    try:
        ds = SD(filepath, SDC.READ)

        # Map instrument to O3 variable name
        o3_var_map = {
            "FTIR":   "O3.COLUMN_ABSORPTION.SOLAR",
            "DOBSON": "O3.COLUMN_ABSORPTION",
        }

        if instrument not in o3_var_map:
            raise ValueError(f"Unsupported instrument: {instrument}")

        o3_var = o3_var_map[instrument]

        datasets = ds.datasets()
        if o3_var not in datasets:
            ds.end()
            return None

        # Read variables
        datetime_raw = ds.select("DATETIME")[:]
        o3_column = ds.select(o3_var)[:]
        ds.end()

        # Convert DATETIME (fractional days since 2000-01-01) to timestamps
        base = pd.Timestamp("2000-01-01")
        timestamps = [base + pd.Timedelta(days=float(h)) for h in datetime_raw]

        df = pd.DataFrame({
            "datetime":    timestamps,
            "o3_column":   o3_column,
            "source_file": os.path.basename(filepath),
            "instrument":  instrument
        })

        return df

    except Exception as e:
        print(f"  ERROR {os.path.basename(filepath)}: {e}")
        return None


def merge_hdf_directory(data_dir, output_file, instrument="FTIR"):
    """
    Read all HDF4 files in a directory, merge into a single DataFrame,
    and write to CSV.

    Parameters
    ----------
    data_dir : str
        Path to directory containing HDF4 files.
    output_file : str
        Path to output CSV file.
    instrument : str
        Instrument type. Supported: "FTIR", "DOBSON".

    Returns
    -------
    pd.DataFrame
        Merged and sorted DataFrame of all observations.
    """
    # ── List all HDF files ───────────────────────────────────────────────
    hdf_files = [
        os.path.join(data_dir, f)
        for f in os.listdir(data_dir)
        if f.endswith(".hdf")
    ]

    # ── Read all files ───────────────────────────────────────────────────
    dfs = []
    for filepath in sorted(hdf_files):
        df = read_hdf_file(filepath, instrument=instrument)
        if df is not None:
            dfs.append(df)

    if not dfs:
        raise ValueError(
            f"No valid O3 data found for instrument '{instrument}' "
            f"in directory: {data_dir}"
        )

    # ── Merge and sort ───────────────────────────────────────────────────
    merged = pd.concat(dfs, ignore_index=True)
    merged = merged.sort_values("datetime").reset_index(drop=True)

    # ── Ensure output directory exists ───────────────────────────────────
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # ── Write to CSV ─────────────────────────────────────────────────────
    merged.to_csv(output_file, index=False)


def plot_dobson_ftir(merged):
    # ── Prep data ─────────────────────────────────────────────────────────
    df = merged.copy()
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["year"] = df["datetime"].dt.year
    df["day_of_year"] = df["datetime"].dt.dayofyear

    # Harmonise units: final ozone always in DU
    df["o3_du"] = df["o3_column"]
    mask = df["instrument"] == "FTIR"
    df.loc[mask, "o3_du"] *= MOLEC_PER_CM2_TO_DU

    # Keep day 200 onwards
    df = df[df["day_of_year"] >= 200]

    # ── Create synthetic calendar date for x-axis ────────────────────────
    # Non-leap reference year (standard practice)
    REF_YEAR = 2001

    df["x_date"] = (
        pd.Timestamp(f"{REF_YEAR}-01-01")
        + pd.to_timedelta(df["day_of_year"] - 1, unit="D")
    )

    fig = go.Figure()

    # ── Climatology (all years) ──────────────────────────────────────────
    clim = (
        df.groupby("day_of_year")["o3_du"]
          .agg(
              mean="mean",
              p025=lambda x: x.quantile(0.025),
              p975=lambda x: x.quantile(0.975),
        )
        .reset_index()
    )

    clim["x_date"] = (
        pd.Timestamp(f"{REF_YEAR}-01-01")
        + pd.to_timedelta(clim["day_of_year"] - 1, unit="D")
    )

    # Upper CI bound (invisible, needed for fill)
    fig.add_trace(go.Scatter(
        x=clim["x_date"],
        y=clim["p975"],
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip"
    ))

    # Lower CI bound + shaded range
    fig.add_trace(go.Scatter(
        x=clim["x_date"],
        y=clim["p025"],
        fill="tonexty",
        fillcolor="rgba(105,179,162,0.28)",
        mode="lines",
        line=dict(width=0),
        name="2.5–97.5% range",
        hovertemplate=(
            "2.5–97.5%: "
            "%{y:.1f}–%{customdata:.1f} DU"
            "<extra></extra>"
        ),
        customdata=clim["p975"]
    ))

    # Climatological mean
    fig.add_trace(go.Scatter(
        x=clim["x_date"],
        y=clim["mean"],
        mode="lines",
        line=dict(color="black", width=1.8, dash="dashdot"),
        name="Mean (all years)",
        hovertemplate="Mean: %{y:.1f} DU<extra></extra>"
    ))

    # ── Recent years: daily means ────────────────────────────────────────
    recent = (
        df[df["year"].isin([2024, 2025])]
        .groupby(["year", "day_of_year"])["o3_du"]
        .mean()
        .reset_index()
    )

    colors = {
        2024: "#e6550d",  # warm orange
        2025: "#1f78b4",  # blue
    }

    for year, color in colors.items():
        yd = recent[recent["year"] == year].copy()
        if yd.empty:
            continue

        yd["x_date"] = (
            pd.Timestamp(f"{REF_YEAR}-01-01")
            + pd.to_timedelta(yd["day_of_year"] - 1, unit="D")
        )

        fig.add_trace(go.Scatter(
            x=yd["x_date"],
            y=yd["o3_du"],
            mode="lines+markers",
            line=dict(color=color, width=1.8),
            marker=dict(size=4),
            name=str(year),
            hovertemplate=f"{year}: %{{y:.1f}} DU<extra></extra>"
        ))

    # ── Layout ───────────────────────────────────────────────────────────
    fig.update_layout(
        title="Ozone (O₃) Total Column, (Arrival Heights, Antarctica)",
        hovermode="x unified",
        xaxis=dict(
            range=[
                pd.Timestamp("2001-07-19"),
                pd.Timestamp("2002-01-01"),
            ],
            tickvals=[
                pd.Timestamp("2001-08-01"),
                pd.Timestamp("2001-09-01"),
                pd.Timestamp("2001-10-01"),
                pd.Timestamp("2001-11-01"),
                pd.Timestamp("2001-12-01"),
                pd.Timestamp("2002-01-01"),
            ],
            title=""
        ),
        yaxis=dict(
            title="Ozone (Dobson Units)",
            range=[100, 500]
        ),
        legend=dict(
            orientation="h",        # horizontal legend
            yanchor="top",
            y=-0.22,                # pushes legend below x-axis
            xanchor="center",
            x=0.5,                  # center align
            traceorder="normal",
            font=dict(size=12)
        ),
        template="plotly_white",
        width=1000,
        height=650                # slightly taller to make room for legend
    )

    # ✨ Formatting control (this is the key)
    fig.update_xaxes(
        hoverformat="%d %b",
        tickformat="%b"
    )

    return fig

