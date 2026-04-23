from __future__ import annotations

from pathlib import Path

import numpy as np
import xarray as xr
import pandas as pd
import plotly.graph_objects as go
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import uniform_filter1d
from statsmodels.nonparametric.smoothers_lowess import lowess


def plot_ch4_dual(
    nc_path: str | Path,
    year_min: int = 1992,
    y_range: tuple[float, float] = (1600, 1950),
    loess_frac: float = 0.1,
) -> go.Figure:
    """
    Combined plot of atmospheric CH4 mole fraction (left axis) with LOESS trend,
    and annual rate of change (right axis).

    Input is assumed to be a monthly mean product (e.g. WDCGG NetCDF).
    PCHIP interpolation fills any missing months before the growth rate
    is computed using the MATLAB method:
        grwthrt(i) = mean(months i+1..i+12) - mean(months i-12..i-1)
    smoothed with a 12-month moving average, edges masked.
    LOESS is fitted to the filled monthly series for the trend line only.

    Parameters
    ----------
    nc_path : str or pathlib.Path
        Path to the NetCDF file.
    year_min : int, default 1992
        First year to include in the plot.
    y_range : (float, float), default (1600, 1950)
        Fixed y-axis limits in ppb for CH4 mole fraction.
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
    # 2. Extract monthly CH4 values
    # --------------------------------------------------
    df = (
        ds["value"]
        .to_dataframe(name="CH4_ppb")
        .reset_index()
        .dropna(subset=["CH4_ppb", "time"])
    )
    df = df[df["time"].dt.year >= year_min].copy()

    if df.empty:
        raise ValueError(f"No valid CH4 data found from {year_min} onwards.")

    df["CH4_ppb"] = df["CH4_ppb"].round(1)

    df["year"]  = df["time"].dt.year
    df["month"] = df["time"].dt.month

    # --------------------------------------------------
    # 3. Build complete monthly spine + PCHIP gap fill
    # --------------------------------------------------
    first_yr, first_mo = int(df["year"].iloc[0]),  int(df["month"].iloc[0])
    last_yr,  last_mo  = int(df["year"].iloc[-1]), int(df["month"].iloc[-1])

    spine = pd.DataFrame([
        {"year": yr, "month": mo}
        for yr in range(first_yr, last_yr + 1)
        for mo in range(1, 13)
        if (yr, mo) >= (first_yr, first_mo) and (yr, mo) <= (last_yr, last_mo)
    ])

    monthly = spine.merge(
        df[["year", "month", "CH4_ppb"]],
        on=["year", "month"],
        how="left",
    )
    monthly["decdate"] = monthly["year"] + (monthly["month"] - 0.5) / 12
    monthly["date"] = pd.to_datetime(
        monthly["year"].astype(str) + "-" + monthly["month"].astype(str).str.zfill(2) + "-01"
    )

    good = monthly["CH4_ppb"].notna()
    bad  = monthly["CH4_ppb"].isna()
    monthly["filled"] = bad

    if bad.any() and good.sum() >= 2:
        pchip = PchipInterpolator(
            monthly.loc[good, "decdate"].values,
            monthly.loc[good, "CH4_ppb"].values,
        )
        monthly.loc[bad, "CH4_ppb"] = pchip(monthly.loc[bad, "decdate"].values)

    # --------------------------------------------------
    # 4. Growth rate (MATLAB method)
    #    grwthrt(i) = mean(i+1:i+12) - mean(i-12:i-1)
    # --------------------------------------------------
    means = monthly["CH4_ppb"].values
    n = len(means)
    grwthrt = np.full(n, np.nan)

    for i in range(12, n - 12):
        grwthrt[i] = np.mean(means[i + 1: i + 13]) - np.mean(means[i - 12: i])

    # 12-point moving average smoothing
    grwthrt_filt = np.full(n, np.nan)
    valid = ~np.isnan(grwthrt)
    if valid.sum() > 12:
        tmp = grwthrt.copy()
        tmp[~valid] = 0.0
        smoothed = uniform_filter1d(tmp, size=12, mode="nearest")
        grwthrt_filt[valid] = smoothed[valid]

    # Mask edge contamination (first/last 24 months)
    grwthrt_filt[:24] = np.nan
    grwthrt_filt[max(0, n - 24):] = np.nan

    monthly["growth_rate"]      = grwthrt
    monthly["growth_rate_filt"] = grwthrt_filt

    # --------------------------------------------------
    # 5. LOESS trend (fitted to filled monthly series)
    # --------------------------------------------------
    x_numeric = monthly["decdate"].values.astype(float)
    monthly["loess_ppb"] = lowess(
        endog=monthly["CH4_ppb"].values,
        exog=x_numeric,
        frac=loess_frac,
        return_sorted=False,
    )

    # --------------------------------------------------
    # DEBUG
    # --------------------------------------------------
    # print("=== Monthly (observed) ===")
    # print(f"  rows: {good.sum()}, filled: {bad.sum()}")
    # print(f"  CH4_ppb range: {monthly.loc[good, 'CH4_ppb'].min():.1f} → {monthly.loc[good, 'CH4_ppb'].max():.1f}")
    # print(monthly[["date", "CH4_ppb", "filled"]].head(10).to_string(index=False))

    # print("\n=== Growth rate ===")
    # gr_valid = monthly["growth_rate_filt"].notna()
    # print(f"  valid points: {gr_valid.sum()}")
    # print(f"  range: {monthly['growth_rate_filt'].min():.2f} → {monthly['growth_rate_filt'].max():.2f}")
    # print(monthly.loc[gr_valid, ["date", "growth_rate", "growth_rate_filt"]].head(10).to_string(index=False))

    # --------------------------------------------------
    # 6. Build figure
    # --------------------------------------------------
    fig = go.Figure()

    # --- Left axis: monthly values (observed + PCHIP filled) ---
    fig.add_trace(go.Scatter(
        x=monthly["date"],
        y=monthly["CH4_ppb"],
        mode="markers",
        name="Monthly Mean",
        marker=dict(size=5, color="#7ab8d9", opacity=0.85),
        hovertemplate="%{y:.1f} ppb<extra>Monthly Mean</extra>",
        yaxis="y",
    ))

    # --- Left axis: LOESS trend ---
    fig.add_trace(go.Scatter(
        x=monthly["date"],
        y=monthly["loess_ppb"],
        mode="lines",
        name="Trend",
        line=dict(color="#003087", width=2.3),
        hovertemplate="%{y:.1f} ppb<extra>Trend</extra>",
        yaxis="y",
    ))

    # --- Right axis: smoothed growth rate ---
    growth_plot = monthly[monthly["growth_rate_filt"].notna()]
    fig.add_trace(go.Scatter(
        x=growth_plot["date"],
        y=growth_plot["growth_rate_filt"],
        mode="lines+markers",
        name="Annual Change",
        line=dict(color="#e31a1c", width=1.8),
        marker=dict(size=4, color="#e31a1c"),
        hovertemplate="Annual Change: %{y:.2f} ppb/yr<extra></extra>",
        yaxis="y2",
    ))

    # --------------------------------------------------
    # 7. Layout
    # --------------------------------------------------
    fig.update_layout(
        title="Atmospheric Methane (CH<sub>4</sub>), Arrival Heights, Antarctica, 1992-2024",
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
                monthly["date"].max(),
            ],
        ),
        yaxis=dict(
            title="CH<sub>4</sub> Mole Fraction (ppb)",
            range=[1550,1900],
            side="left",
            showline=True,
            linewidth=1.3,
            linecolor="black",
            showgrid=False,
            tickformat=".0f",
        ),
        yaxis2=dict(
            title="CH<sub>4</sub> Annual Change (ppb/year)",
            range=[-5, 50],
            side="right",
            overlaying="y",
            showline=True,
            linewidth=1.3,
            linecolor="black",
            tickformat=".0f",
            showgrid=False,
            tick0=0,
            dtick=5,
        ),
        legend=dict(
            orientation="h",
            x=0.5, xanchor="center",
            y=-0.18, yanchor="top",
        ),
        margin=dict(l=60, r=60, t=70, b=120),
    )

    return fig
