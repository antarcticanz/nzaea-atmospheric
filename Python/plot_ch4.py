"""
Plot atmospheric CO₂ mole fraction with LOESS trend from a WDCGG-style NetCDF file.

Usage (as a module):
    from plot_ch4 import plot_ch4
    fig = plot_ch4("path/to/file.nc")
    fig.show()

Usage (as a script):
    python plot_ch4.py path/to/file.nc
"""

from __future__ import annotations

import sys
from pathlib import Path

import xarray as xr
import pandas as pd
import plotly.graph_objects as go
from statsmodels.nonparametric.smoothers_lowess import lowess


def plot_ch4(
    nc_path: str | Path,
    year_min: int = 1992,
    y_range: tuple[float, float] = (1500, 2000),
    loess_frac: float = 0.1,
) -> go.Figure:
    """
    Plot atmospheric CO₂ mole fraction with a LOESS trend.

    Parameters
    ----------
    nc_path : str or pathlib.Path
        Path to the NetCDF file.
    year_min : int, default 2004
        First year to include in the plot.
    y_range : (float, float), default (350, 420)
        Fixed y-axis limits in ppm.
    loess_frac : float, default 0.1
        LOWESS fraction controlling smoothing strength.

    Returns
    -------
    plotly.graph_objects.Figure
        Interactive Plotly figure.
    """

    nc_path = Path(nc_path)
    if not nc_path.exists():
        raise FileNotFoundError(f"NetCDF file not found: {nc_path}")

    # --------------------------------------------------
    # 1. Open dataset
    # --------------------------------------------------
    ds = xr.open_dataset(nc_path, decode_times=False)

    # --------------------------------------------------
    # 2. Build datetime coordinate from components
    # --------------------------------------------------
    tc = ds["start_time_components"].values

    time = pd.to_datetime(
        [
            f"{y:04d}-{m:02d}-{d:02d} {hh:02d}:{mm:02d}:{ss:02d}"
            for y, m, d, hh, mm, ss in tc
        ],
        errors="coerce",
    )

    ds = ds.assign_coords(time=("time", time))

    # --------------------------------------------------
    # 3. Select CO₂ mole fraction
    # --------------------------------------------------
    ch4 = ds["value"]

    df = (
        ch4.to_dataframe(name="CH4_ppm")
        .reset_index()
        .dropna(subset=["CH4_ppm", "time"])
    )

    # --------------------------------------------------
    # 4. Filter to year_min onwards
    # --------------------------------------------------
    df = df[df["time"].dt.year >= year_min]

    if df.empty:
        raise ValueError(f"No valid CH4 data found from {year_min} onwards.")

    df["CH4_ppm"] = df["CH4_ppm"].round(0)

    # --------------------------------------------------
    # 5. LOWESS smoothing
    # --------------------------------------------------
    x_numeric = df["time"].astype("int64") // 10**9  # seconds since epoch
    y = df["CH4_ppm"].values

    loess_vals = lowess(
        endog=y,
        exog=x_numeric,
        frac=loess_frac,
        return_sorted=False,
    ).round(0)

    # --------------------------------------------------
    # 6. Plot
    # --------------------------------------------------
    fig = go.Figure()

    # Observed points
    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["CH4_ppm"],
            mode="markers",
            name="Observed",
            marker=dict(
                size=8,
                color="#1f77b4",
                opacity=0.9,
            ),
            hovertemplate="%{y:.0f} ppb<extra>Observed</extra>",
        )
    )

    # LOESS trend
    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=loess_vals,
            mode="lines",
            name="Trend",
            line=dict(
                color="#e31a1c",
                width=2.3,
            ),
            hovertemplate="%{y:.0f} ppb<extra>Trend</extra>",
        )
    )

    fig.update_layout(
        title="Atmospheric Methane at Arrival Heights",
        template="plotly_white",
        hovermode="x unified",

        xaxis=dict(
            title="",
            tickmode="linear",
            dtick="M12",
            tickformat="%Y",
            tickangle=90,
            showline=True,
            linewidth=1.3,
            linecolor="black",
            showgrid=False,
            range=[
                pd.Timestamp(f"{year_min}-01-01") - pd.DateOffset(months=4),
                df["time"].max(),
            ],
        ),

        yaxis=dict(
            title="Methane Mole Fraction (ppb)",
            range=list(y_range),
            showline=True,
            linewidth=1.3,
            linecolor="black",
            showgrid=False,
            tickformat=".0f",
        ),

        legend=dict(
            orientation="h",
            x=0.5,
            xanchor="center",
            y=-0.18,
            yanchor="top",
        ),

        margin=dict(l=60, r=20, t=70, b=100),
    )

    return fig


# --------------------------------------------------
# Script entry point
# --------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python plot_ch4_loess.py path/to/file.nc")
        sys.exit(1)

    nc_file = sys.argv[1]
    fig = plot_ch4(nc_file)
    fig.show()
