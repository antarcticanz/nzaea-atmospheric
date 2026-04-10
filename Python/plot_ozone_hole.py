from pathlib import Path
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import io


# =====================================================
# READ LOCAL FILE
# =====================================================

def _read_omd_file(fp: Path):

    with open(fp, "r") as f:
        lines = f.readlines()

    start = next(i for i, ln in enumerate(lines) if ln.startswith("Date"))
    table = "".join(lines[start:])

    df = pd.read_csv(
        io.StringIO(table),
        sep=r'\s+',
        na_values='-9999.0'
    )

    df["Date"] = pd.to_datetime(df["Date"])
    df["Year"] = df["Date"].dt.year
    df["DOY"] = df["Date"].dt.dayofyear

    return df


# =====================================================
# LOAD ONE YEAR
# =====================================================

def load_year(write_dir, year):

    write_dir = Path(write_dir)
    fp = write_dir / f"omds_{year}.txt"

    if not fp.exists():
        raise FileNotFoundError(f"{fp} not found.")

    return _read_omd_file(fp)


def get_plot_data(write_dir):

    current_year = datetime.now().year
    baseline_year = current_year - 1

    baseline = load_year(write_dir, baseline_year).sort_values("DOY")
    recent = load_year(write_dir, current_year).sort_values("DOY")

    return baseline, recent


# =====================================================
# PLOT
# =====================================================

def plot_ozone_mass_deficit(write_dir):

    current_year = datetime.now().year
    baseline_year = current_year - 1

    baseline = load_year(write_dir, baseline_year).sort_values("DOY")
    recent = load_year(write_dir, current_year).sort_values("DOY")

    def doy_to_date(doy_series, year):
        return pd.to_datetime(
            doy_series.apply(lambda d: f"{year}-{d:03d}"), format="%Y-%j"
        )

    bx = doy_to_date(baseline["DOY"], current_year)
    rx = doy_to_date(recent["DOY"],   current_year)

    fig = go.Figure()

    # ---------------------------
    # MIN / MAX LINES
    # ---------------------------

    fig.add_trace(go.Scatter(
        x=bx, y=baseline["Maximum"],
        mode="lines", line=dict(color="rgba(105,179,162,0.8)", width=1),
        name="Range (min-max)",
        showlegend=True,
        customdata=baseline["Minimum"],
        hovertemplate="Min-Max: %{customdata:.1f}–%{y:.1f} Mt<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=bx, y=baseline["Minimum"],
        mode="lines", line=dict(color="rgba(105,179,162,0.8)", width=1),
        name="Min-Max",
        showlegend=False,
        hoverinfo="skip",
    ))

    # ---------------------------
    # 10–90% SHADED ENVELOPE  (teal — outer band)
    # ---------------------------

    fig.add_trace(go.Scatter(
        x=pd.concat([bx, bx[::-1]]),
        y=pd.concat([baseline["90%"], baseline["10%"][::-1]]),
        fill="toself", fillcolor="rgba(105,179,162,0.28)",
        line=dict(color="rgba(255,255,255,0)"),
        name="Outer (10–90%)", hoverinfo="skip", showlegend=True,
    ))

    fig.add_trace(go.Scatter(
        x=bx, y=baseline["90%"],
        mode="lines", line=dict(color="rgba(105,179,162,0)"),
        name="Outer (10–90%)", showlegend=False,
        customdata=baseline["10%"],
        hovertemplate="10–90%%: %{customdata:.1f}–%{y:.1f} Mt<extra></extra>",
    ))

    # ---------------------------
    # 30–70% SHADED ENVELOPE  (blue — inner band)
    # ---------------------------

    fig.add_trace(go.Scatter(
        x=pd.concat([bx, bx[::-1]]),
        y=pd.concat([baseline["70%"], baseline["30%"][::-1]]),
        fill="toself", fillcolor="rgba(31,120,180,0.22)",
        line=dict(color="rgba(255,255,255,0)"),
        name="Inner (30–70%)", hoverinfo="skip", showlegend=True,
    ))

    fig.add_trace(go.Scatter(
        x=bx, y=baseline["70%"],
        mode="lines", line=dict(color="rgba(31,120,180,0)"),
        name="30–70%", showlegend=False,
        customdata=baseline["30%"],
        hovertemplate="30–70%%: %{customdata:.1f}–%{y:.1f} Mt<extra></extra>",
    ))

    # ---------------------------
    # CLIMATOLOGICAL MEAN
    # ---------------------------

    fig.add_trace(go.Scatter(
        x=bx, y=baseline["Mean"],
        mode="lines", line=dict(color="#1f78b4", width=2),
        name=f"Mean",
        hovertemplate="Mean: %{y:.1f} Mt<extra></extra>",
    ))

    # ---------------------------
    # BASELINE YEAR OBSERVED
    # ---------------------------


    fig.add_trace(go.Scatter(
        x=bx, y=baseline["Data"],
        mode="lines", line=dict(color="#e31a1c", width=1.6, dash="dash"),
        name=str(baseline_year),
        hovertemplate=f"{baseline_year}: %{{y:.1f}} Mt<extra></extra>",
    ))
    # ---------------------------
    # CURRENT YEAR OBSERVED
    # ---------------------------

    recent_aligned = baseline[["DOY"]].merge(
        recent[["DOY", "Data"]], on="DOY", how="left"
    )

    fig.add_trace(go.Scatter(
        x=bx, y=recent_aligned["Data"],
        mode="lines", line=dict(color="blue", width=2),
        name=str(current_year),
        hovertemplate=f"{current_year}: %{{y:.1f}} Mt<extra></extra>",
    ))

    # ---------------------------
    # LAYOUT
    # ---------------------------

    fig.update_layout(
        title=dict(text="Daily Ozone Mass Deficit, 1979-2025", font=dict(size=18)),
        xaxis=dict(
            title="",
            tickformat="%b",
            dtick="M1",
            showgrid=False,
        ),
        yaxis=dict(
            title="Million Tons",
            showgrid=False,
            showline=True,
            linecolor="black",
            linewidth=1,
            ticklabelstandoff=8,
            range=[None, 50],

        ),
        legend=dict(
            bgcolor="white",
            orientation="h",
            x=0.5,
            y=-0.18,
            xanchor="center",
            yanchor="top",
        ),
        hovermode="x unified",
        xaxis_hoverformat="%-d %b",
        hoverlabel=dict(namelength=-1),
        plot_bgcolor="white",
        paper_bgcolor="white",
        width=1100,
        height=500,
    )

    return fig
