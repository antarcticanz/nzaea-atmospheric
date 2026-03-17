from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests


SourceLike = Union[str, Path, pd.DataFrame]


# -----------------------------
# Helpers
# -----------------------------
def _is_url(s: str) -> bool:
    return bool(re.match(r"^(https?|ftp)://", s.strip(), flags=re.I))


def _read_nasa_text_table_from_url(url: str) -> tuple[pd.DataFrame, dict]:
    """
    Download the NASA text file, strip the metadata block, and parse the table via FWF.
    Returns (df, meta) where meta contains simple 'Key: Value' from the header.
    """
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    text = resp.text

    lines = text.splitlines()
    meta: dict[str, str] = {}

    # Collect metadata up to the table header line that starts with "Year"
    for ln in lines:
        if ln.strip().startswith("Year"):
            break
        if ":" in ln:
            k, v = ln.split(":", 1)
            meta[k.strip()] = v.strip()

    try:
        start = next(i for i, ln in enumerate(lines)
                     if ln.strip().startswith("Year"))
    except StopIteration:
        raise ValueError(
            "Could not find a header line starting with 'Year' in the URL content.")

    table_text = "\n".join(lines[start:])

    # Fixed-width table; treat only -9999.00 as NA here (more robust handling later too)
    df = pd.read_fwf(io.StringIO(table_text), na_values=['-9999.00'])

    return df, meta


def _sanitize_units(units: str | None) -> str:
    if not units:
        return "million km²"
    # Normalize 'km2' to 'km²' for nicer rendering
    return units.replace("km2", "km²")


# -----------------------------
# Main plotting function
# -----------------------------
def plot_sh_ozone_hole_area_annual(
    source: SourceLike,
    show_band: bool = True,
    split_band_at_nans: bool = True,
) -> go.Figure:
    """
    Plot Southern Hemisphere ozone hole *area* annual statistics.

    Parameters
    ----------
    source : str | pathlib.Path | pandas.DataFrame
        - URL to NASA text file with metadata header and fixed-width table
        - Local CSV filepath (columns: Year, Data, Minumum/Minimum, Maximum)
        - or a pandas DataFrame already in memory
    show_band : bool
        If True and min/max columns exist, draw a shaded band between Minimum and Maximum.
    split_band_at_nans : bool
        If True, the band is split into contiguous segments of valid data so gaps
        (e.g., 1995) do not get bridged.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    # -----------------------------
    # Read / parse
    # -----------------------------
    meta: dict[str, str] = {}

    if isinstance(source, pd.DataFrame):
        df = source.copy()
        title = "Southern Hemisphere Ozone Hole Area"
        units = "million km²"

    elif isinstance(source, (str, Path)):
        s = str(source)
        if _is_url(s):
            # NASA URL → text + metadata header
            df, meta = _read_nasa_text_table_from_url(s)
            title = meta.get("Name", "Southern Hemisphere Ozone Hole Area")
            units = _sanitize_units(meta.get("Units", "million km²"))
        else:
            # Local file path
            p = Path(s)
            if not p.exists():
                raise FileNotFoundError(f"Path not found: {p}")

            if p.suffix.lower() == ".csv":
                df = pd.read_csv(p)
                title = "Southern Hemisphere Ozone Hole Area"
                units = "million km²"
            else:
                # Fallback: treat as a NASA-formatted text file (metadata + table)
                text = p.read_text(encoding="utf-8")
                lines = text.splitlines()
                for ln in lines:
                    if ln.strip().startswith("Year"):
                        break
                    if ":" in ln:
                        k, v = ln.split(":", 1)
                        meta[k.strip()] = v.strip()
                try:
                    start = next(i for i, ln in enumerate(lines)
                                 if ln.strip().startswith("Year"))
                except StopIteration:
                    raise ValueError(
                        "Could not find a header line starting with 'Year' in the file.")
                table_text = "\n".join(lines[start:])
                df = pd.read_fwf(io.StringIO(table_text),
                                 na_values=['-9999.00'])

                title = meta.get("Name", "Southern Hemisphere Ozone Hole Area")
                units = _sanitize_units(meta.get("Units", "million km²"))
    else:
        raise TypeError(
            "source must be a URL string, local filepath, or pandas.DataFrame")

    # -----------------------------
    # Cleaning
    # -----------------------------
    required = {"Year", "Data"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Input is missing required columns: {missing}")

    # Tolerate misspelling in NASA file
    min_col = "Minumum" if "Minumum" in df.columns else (
        "Minimum" if "Minimum" in df.columns else None)
    max_col = "Maximum" if "Maximum" in df.columns else None

    # Cast numerics & apply sentinel replacement
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")

    numeric_cols = ["Data"] + [c for c in (min_col, max_col) if c]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
        # Replace typical NASA sentinel values with NaN; keep other values intact
        df[c] = df[c].replace(-9999.0, np.nan)

    df = df.dropna(subset=["Year"]).sort_values("Year")
    df["Year"] = df["Year"].astype(int)

    # -----------------------------
    # Figure
    # -----------------------------
    fig = go.Figure()

    # ==========================================================
    # MIN / MAX SHADED BAND
    # ==========================================================
    if show_band and min_col and max_col:
        if split_band_at_nans:
            # Build a mask where BOTH min & max are present
            valid = df[min_col].notna() & df[max_col].notna()
            # Identify contiguous runs of validity: each time validity changes, increment a group id
            runs = (valid != valid.shift()).cumsum()

            show_leg = True  # Only show one legend entry
            for _, seg in df[valid].groupby(runs[valid]):
                # Need at least two points to form a polygon
                if len(seg) < 2:
                    continue

                # Hidden MAX segment to anchor the fill
                fig.add_trace(go.Scatter(
                    x=seg["Year"],
                    y=seg[max_col],
                    mode="lines",
                    line=dict(color="rgba(0,0,0,0)"),
                    showlegend=False,
                    hoverinfo="skip",
                    connectgaps=False
                ))

                # Visible MIN segment filled to the previous (MAX) segment
                fig.add_trace(go.Scatter(
                    name="Minimum/Maximum",
                    x=seg["Year"],
                    y=seg[min_col],
                    mode="lines",
                    line=dict(color="rgba(105,179,162,0)"),
                    fill="tonexty",
                    fillcolor="rgba(105,179,162,0.28)",
                    customdata=np.c_[seg[min_col], seg[max_col]],
                    hovertemplate=(
                        "Minimum: %{customdata[0]:.2f} "
                        "<br>Maximum: %{customdata[1]:.2f} "
                        "<extra></extra>"
                    ),
                    connectgaps=False,
                    showlegend=show_leg
                ))
                show_leg = False
        else:
            # Original behavior (continuous band with interpolation on MAX)
            band = df.copy()
            fig.add_trace(go.Scatter(
                x=band["Year"],
                y=band[max_col].interpolate(),
                mode="lines",
                line=dict(color="rgba(0,0,0,0)"),
                showlegend=False,
                hoverinfo="skip"
            ))
            fig.add_trace(go.Scatter(
                name="Minimum/Maximum",
                x=band["Year"],
                y=band[min_col],
                mode="lines",
                line=dict(color="rgba(105,179,162,0)"),
                fill="tonexty",
                fillcolor="rgba(105,179,162,0.28)",
                customdata=np.c_[band[min_col], band[max_col]],
                hovertemplate=(
                    "Minimum: %{customdata[0]:.2f} "
                    "<br>Maximum: %{customdata[1]:.2f} "
                    "<extra></extra>"
                ),
                connectgaps=False
            ))

    # ==========================================================
    # MEAN (NaNs produce breaks in the line automatically)
    # ==========================================================
    fig.add_trace(go.Scatter(
        name="Mean",
        x=df["Year"],
        y=df["Data"],
        mode="lines+markers",
        line=dict(color="#5B9BD5", width=2),
        marker=dict(size=5),
        hovertemplate="Mean: %{y:.2f} <extra></extra>",
        connectgaps=False
    ))

    # ==========================================================
    # AXIS
    # ==========================================================
    df_valid = df.dropna(subset=["Data"])

    if not df_valid.empty:
        xmin = int(df_valid["Year"].min())
        xmax = int(df_valid["Year"].max())
        xaxis_cfg = dict(
            title="Year",
            tickmode="linear",
            tick0=xmin,
            dtick=1,
            range=[xmin - 0.5, xmax + 0.5],
            tickformat="d",
            separatethousands=False,
            tickangle=-45,
            tickfont=dict(size=12),
            automargin=True
        )
    else:
        xaxis_cfg = dict(title="Year")

    fig.update_layout(
        title=meta.get(
            "Name", "Southern Hemisphere Ozone Hole Area") if meta else "Southern Hemisphere Ozone Hole Area",
        xaxis=xaxis_cfg,
        yaxis=dict(
            title=f"Area ({_sanitize_units(meta.get('Units') if meta else 'million km²')})"),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            x=0.5,
            xanchor="center",
            y=-0.22,
            yanchor="top"
        ),
        template="plotly_white",
        margin=dict(l=60, r=20, t=70, b=0),
        height=520
    )

    return fig
