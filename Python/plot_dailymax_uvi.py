"""
Plot a Sep–Jan climatology of daily maximum UV Index with variability shading.

Input may be:
  - a CSV file path, or
  - a pandas DataFrame (output of compute_daily_max_uvi)

Required columns:
  - Date (datetime)
  - DailyMaxUVI (float)
  - season_year (int)
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd
import plotly.graph_objects as go


SourceLike = Union[str, Path, pd.DataFrame]


def plot_dailymax_uvi(
    source: SourceLike,
    *,
    show_inner_band: bool = True,
    year_to_overlay: int | None = None,
    title: str = "UV Index (Arrival Heights, Antarctica)",
) -> go.Figure:
    """
    Plot Sep 1 → Jan 31 climatology of Daily Maximum UVI with shaded variability.
    """

    # --------------------------------------------------
    # Load input
    # --------------------------------------------------
    if isinstance(source, pd.DataFrame):
        df = source.copy()
    else:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path}")
        df = pd.read_csv(path)

    # --------------------------------------------------
    # Guard rails and types
    # --------------------------------------------------
    required_cols = {"Date", "DailyMaxUVI", "season_year"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Input is missing required columns: {missing}")

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    # --------------------------------------------------
    # Keep Sep–Dec + January
    # --------------------------------------------------
    m = df["Date"].dt.month
    df = df.loc[m.isin([9, 10, 11, 12, 1])].copy()

    # --------------------------------------------------
    # Map each date to a "season day"
    # --------------------------------------------------
    season_start = pd.to_datetime(df["season_year"].astype(str) + "-09-01")
    df["season_day"] = (df["Date"] - season_start).dt.days + 1

    # Anchor x-axis
    anchor = pd.Timestamp(2000, 9, 1)
    df["x_date"] = anchor + pd.to_timedelta(df["season_day"] - 1, unit="D")

    # Cap at Jan 1
    end_date = pd.Timestamp(2001, 1, 1)
    df = df.loc[(df["x_date"] >= anchor) & (df["x_date"] <= end_date)].copy()

    # --------------------------------------------------
    # Climatology
    # --------------------------------------------------
    clim = (
        df.groupby("season_day")
        .agg(
            min=("DailyMaxUVI", "min"),
            mean=("DailyMaxUVI", "mean"),
            max=("DailyMaxUVI", "max"),
            p10=("DailyMaxUVI", lambda s: np.nanpercentile(s, 10)),
            p90=("DailyMaxUVI", lambda s: np.nanpercentile(s, 90)),
        )
        .reset_index()
    )

    clim["x_date"] = anchor + pd.to_timedelta(clim["season_day"] - 1, unit="D")
    clim = clim.sort_values("x_date")

    # --------------------------------------------------
    # Figure
    # --------------------------------------------------
    x = clim["x_date"]
    fig = go.Figure()

    # Outer band
    fig.add_trace(go.Scatter(
        x=x,
        y=clim["max"],
        mode="lines",
        line=dict(color="rgba(105,179,162,0)"),
        showlegend=False,
        hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        name="Range (min–max)",
        x=x,
        y=clim["min"],
        mode="lines",
        line=dict(color="rgba(105,179,162,0)"),
        fill="tonexty",
        fillcolor="rgba(105,179,162,0.28)",
        customdata=np.c_[clim["max"].to_numpy()],
        hovertemplate="Min–Max: %{y:.2f} – %{customdata:.2f}<extra></extra>",
        showlegend=True,
    ))

    # Inner band
    if show_inner_band:
        fig.add_trace(go.Scatter(
            x=x,
            y=clim["p90"],
            mode="lines",
            line=dict(color="rgba(31,120,180,0)"),
            showlegend=False,
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            name="Inner 10–90%",
            x=x,
            y=clim["p10"],
            mode="lines",
            line=dict(color="rgba(31,120,180,0)"),
            fill="tonexty",
            fillcolor="rgba(31,120,180,0.22)",
            customdata=np.c_[clim["p90"].to_numpy()],
            hovertemplate="P10–P90: %{y:.2f} – %{customdata:.2f}<extra></extra>",
            showlegend=True,
        ))

    # Mean
    fig.add_trace(go.Scatter(
        name="Mean",
        x=x,
        y=clim["mean"],
        mode="lines",
        line=dict(color="#1f78b4", width=2),
        hovertemplate="Mean: %{y:.2f}<extra></extra>",
        showlegend=True,
    ))

    # Optional overlay year
    if year_to_overlay is not None:
        one = df.loc[df["season_year"] == int(
            year_to_overlay)].sort_values("x_date")
        if not one.empty:
            fig.add_trace(go.Scatter(
                name=str(year_to_overlay),
                x=one["x_date"],
                y=one["DailyMaxUVI"],
                mode="lines",
                line=dict(color="#e31a1c", width=1.6, dash="dash"),
                hovertemplate=(
                    f"{year_to_overlay}: "
                    "%{y:.2f}<extra></extra>"
                ),
                showlegend=True,
            ))

    # --------------------------------------------------
    # Layout
    # --------------------------------------------------
    fig.update_layout(
        title=title,
        template="plotly_white",
        hovermode="x unified",
        xaxis=dict(
            type="date",
            tickformat="%d-%b",
            dtick=14 * 24 * 60 * 60 * 1000,
            range=[anchor, end_date],
        ),
        yaxis=dict(title="UV Index"),
        legend=dict(
            orientation="h",
            x=0.5,
            xanchor="center",
            y=-0.12,
            yanchor="top",
        ),
        margin=dict(l=60, r=20, t=70, b=100),
    )

    return fig
