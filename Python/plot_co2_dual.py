from __future__ import annotations

from pathlib import Path

import xarray as xr
import pandas as pd
import plotly.graph_objects as go
from statsmodels.nonparametric.smoothers_lowess import lowess


def plot_co2_dual(
    nc_path: str | Path,
    year_min: int = 2004,
    y_range: tuple[float, float] = (350, 420),
    loess_frac: float = 0.1,
) -> go.Figure:
    """
    Combined plot of atmospheric CO2 mole fraction (left axis) with LOESS trend,
    and annual rate of change (right axis).

    Parameters
    ----------
    nc_path : str or pathlib.Path
        Path to the NetCDF file.
    year_min : int, default 2004
        First year to include in the plot.
    y_range : (float, float), default (350, 420)
        Fixed y-axis limits in ppm for CO2 mole fraction.
    loess_frac : float, default 0.1
        LOWESS fraction controlling smoothing strength.

    Returns
    -------
    plotly.graph_objects.Figure
    """

    nc_path = Path(nc_path)
    if not nc_path.exists():
        raise FileNotFoundError(f"NetCDF file not found: {nc_path}")

    # --------------------------------------------------
    # 1. Open dataset + build datetime coordinate
    # --------------------------------------------------
    ds = xr.open_dataset(nc_path, decode_times=False)
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
    # 2. Extract CO2 + filter
    # --------------------------------------------------
    df = (
        ds["value"]
        .to_dataframe(name="CO2_ppm")
        .reset_index()
        .dropna(subset=["CO2_ppm", "time"])
    )
    df = df[df["time"].dt.year >= year_min].copy()

    if df.empty:
        raise ValueError(f"No valid CO2 data found from {year_min} onwards.")

    # --------------------------------------------------
    # 3. LOESS smoothing
    # --------------------------------------------------
    x_numeric = df["time"].astype("int64") // 10**9
    loess_vals = lowess(
        endog=df["CO2_ppm"].values,
        exog=x_numeric,
        frac=loess_frac,
        return_sorted=False,
    )
    df["loess_ppm"] = loess_vals

    # --------------------------------------------------
    # 4. Annual rate of change from interpolated LOESS
    # --------------------------------------------------
    trend_series = (
        df[["time", "loess_ppm"]]
        .sort_values("time")
        .groupby("time")["loess_ppm"]
        .mean()
    )

    max_year = int(df["time"].max().year)
    year_starts = pd.date_range(
        start=f"{year_min}-01-01",
        end=f"{max_year}-01-01",
        freq="YS",
    )

    loess_at_year_start = (
        trend_series
        .reindex(trend_series.index.union(year_starts))
        .sort_index()
        .interpolate(method="time")
        .reindex(year_starts)
    )

    annual_df = pd.DataFrame({
        "time": year_starts,
        "year": year_starts.year,
        "loess_year_value": loess_at_year_start.values,
    })
    annual_df["change_ppm_per_year"] = annual_df["loess_year_value"].diff()
    change_df = annual_df.dropna(subset=["change_ppm_per_year"]).copy()
    change_df["period"] = (
        (change_df["year"] - 1).astype(str) +
        " to " + change_df["year"].astype(str)
    )

    # --------------------------------------------------
    # 5. Build figure
    # --------------------------------------------------
    fig = go.Figure()

    # --- Left axis: observed CO2 ---
    fig.add_trace(go.Scatter(
        x=df["time"],
        y=df["CO2_ppm"],
        mode="markers",
        name="Observed",
        marker=dict(size=6, color="#1f77b4", opacity=0.95),
        hovertemplate="%{y:.2f} ppm<extra>Observed</extra>",
        yaxis="y",
    ))

    # --- Left axis: LOESS trend ---
    fig.add_trace(go.Scatter(
        x=df["time"],
        y=df["loess_ppm"],
        mode="lines",
        name="Trend",
        line=dict(color="#e31a1c", width=2.3),
        hovertemplate="%{y:.2f} ppm<extra>Trend</extra>",
        yaxis="y",
    ))

    # --- Right axis: faint connector ---
    fig.add_trace(go.Scatter(
        x=change_df["time"],
        y=change_df["change_ppm_per_year"],
        mode="lines",
        line=dict(color="rgba(27,120,55,0.35)", width=1.4, dash="dash"),
        hoverinfo="skip",
        showlegend=False,
        yaxis="y2",
    ))

    # --- Right axis: annual change points ---
    fig.add_trace(go.Scatter(
        x=change_df["time"],
        y=change_df["change_ppm_per_year"],
        mode="markers",
        name="Annual Change",
        marker=dict(size=7, color="#2ca02c", opacity=0.95),
        hovertemplate=(
            "Period: %{customdata}<br>"
            "Change: %{y:.2f} ppm/year<extra></extra>"
        ),
        customdata=change_df["period"],
        yaxis="y2",
    ))

    # --------------------------------------------------
    # 6. Layout
    # --------------------------------------------------
    fig.update_layout(
        title="Atmospheric Carbon Dioxide (CO<sub>2</sub>) at Arrival Heights",
        template="plotly_white",
        hovermode="x unified",
        xaxis=dict(
            tickmode="linear",
            dtick="M12",
            tickformat="%Y",
            showline=True,
            linewidth=1.3,
            tickangle=0,
            tickfont=dict(size=12),
            linecolor="black",
            showgrid=False,
            range=[
                pd.Timestamp(f"{year_min}-01-01") - pd.DateOffset(months=4),
                df["time"].max(),
            ],
        ),
        yaxis=dict(
            title="CO<sub>2</sub> Mole Fraction (ppm)",
            range=list(y_range),
            side="left",
            showline=True,
            linewidth=1.3,
            linecolor="black",
            showgrid=False,
            tickformat=".0f",
        ),
        yaxis2=dict(
            title="CO<sub>2</sub> Annual Change (ppm/year)",
            side="right",
            overlaying="y",
            showline=True,
            linewidth=1.3,
            linecolor="#1b7837",
            tickformat=".0f",
            showgrid=False,
            range=[0,5],
        ),
        legend=dict(
            orientation="h",
            x=0.5, xanchor="center",
            y=-0.18, yanchor="top",
        ),
        margin=dict(l=60, r=60, t=70, b=120),
    )

    return fig
