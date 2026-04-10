from __future__ import annotations

from pathlib import Path

import xarray as xr
import pandas as pd
import plotly.graph_objects as go
from statsmodels.nonparametric.smoothers_lowess import lowess


def plot_n20_dual(
    nc_path: str | Path,
    year_min: int = 1996,
    y_range: tuple[float, float] = (300, 350),
    loess_frac: float = 0.1,
) -> go.Figure:
    """
    Combined plot of atmospheric N2O mole fraction (left axis) with LOESS trend,
    and annual rate of change (right axis).

    Parameters
    ----------
    nc_path : str or pathlib.Path
        Path to the NetCDF file.
    year_min : int, default 1996
        First year to include in the plot.
    y_range : (float, float), default (300, 350)
        Fixed y-axis limits in ppb for N2O mole fraction.
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
    # 2. Extract N2O + filter
    # --------------------------------------------------
    df = (
        ds["value"]
        .to_dataframe(name="n20_ppb")
        .reset_index()
        .dropna(subset=["n20_ppb", "time"])
    )
    df = df[df["time"].dt.year >= year_min].copy()

    if df.empty:
        raise ValueError(f"No valid N2O data found from {year_min} onwards.")

    df["n20_ppb"] = df["n20_ppb"].round(0)

    # --------------------------------------------------
    # 3. LOESS smoothing
    # --------------------------------------------------
    x_numeric = df["time"].astype("int64") // 10**9
    loess_vals = lowess(
        endog=df["n20_ppb"].values,
        exog=x_numeric,
        frac=loess_frac,
        return_sorted=False,
    )
    df["loess_ppb"] = loess_vals

    # --------------------------------------------------
    # 4. Annual rate of change from interpolated LOESS
    # --------------------------------------------------
    trend_series = (
        df[["time", "loess_ppb"]]
        .sort_values("time")
        .groupby("time")["loess_ppb"]
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
    annual_df["change_ppb_per_year"] = annual_df["loess_year_value"].diff()
    change_df = annual_df.dropna(subset=["change_ppb_per_year"]).copy()
    change_df["period"] = (
        (change_df["year"] - 1).astype(str) +
        " to " + change_df["year"].astype(str)
    )

    # --------------------------------------------------
    # 5. Build figure
    # --------------------------------------------------
    fig = go.Figure()

    # --- Left axis: observed N2O ---
    fig.add_trace(go.Scatter(
        x=df["time"],
        y=df["n20_ppb"],
        mode="markers",
        name="Observed",
        marker=dict(size=6, color="#1f77b4"),
        hovertemplate="%{y:.0f} ppb<extra>Observed</extra>",
        yaxis="y",
    ))

    # --- Left axis: LOESS trend ---
    fig.add_trace(go.Scatter(
        x=df["time"],
        y=df["loess_ppb"],
        mode="lines",
        name="Trend",
        line=dict(color="#e31a1c", width=2.3),
        hovertemplate="%{y:.0f} ppb<extra>Trend</extra>",
        yaxis="y",
    ))

    # --- Right axis: faint connector ---
    fig.add_trace(go.Scatter(
        x=change_df["time"],
        y=change_df["change_ppb_per_year"],
        mode="lines",
        line=dict(color="rgba(27,120,55,0.35)", width=1.4, dash="dash"),
        hoverinfo="skip",
        showlegend=False,
        yaxis="y2",
    ))

    # --- Right axis: annual change points ---
    fig.add_trace(go.Scatter(
        x=change_df["time"],
        y=change_df["change_ppb_per_year"],
        mode="markers",
        name="Annual Change",
        marker=dict(size=7, color="#2ca02c", opacity=0.95),
        hovertemplate=(
            "Period: %{customdata}<br>"
            "Change: %{y:.2f} ppb/year<extra></extra>"
        ),
        customdata=change_df["period"],
        yaxis="y2",
    ))

    fig.add_hline(
        y=0,
        line_width=1.0,
        line_dash="dash",
        line_color="lightgray",
    )

    # --------------------------------------------------
    # 6. Layout
    # --------------------------------------------------
    fig.update_layout(
        title="Atmospheric Nitrous Oxide (N<sub>2</sub>O), Arrival Heights, Antarctica, 1990-2024",
        template="plotly_white",
        hovermode="x unified",
        xaxis=dict(
            tickmode="linear",
            dtick="M12",
            tickformat="%Y",
            tickangle=-45,
            tickfont=dict(size=12),
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
            title="N<sub>2</sub>O Mole Fraction (ppb)",
            range=list(y_range),
            side="left",
            showline=True,
            linewidth=1.3,
            linecolor="black",
            showgrid=False,
            tickformat=".0f",
        ),
        yaxis2=dict(
            title="N<sub>2</sub>O Annual Change (ppb/year)",
            range=[0, 5],
            side="right",
            overlaying="y",
            showline=True,
            linewidth=1.3,
            linecolor="black",
            tickformat=".0f",
            showgrid=False,
        ),
        legend=dict(
            orientation="h",
            x=0.5, xanchor="center",
            y=-0.18, yanchor="top",
        ),
        margin=dict(l=60, r=60, t=70, b=120),
    )

    return fig
