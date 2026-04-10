import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from plot_ozone_hole import load_year


def compute_ozone_deficit_means(read_dir: str) -> pd.DataFrame:
    records = []
    for year in range(1979, 2025):
        try:
            df = load_year(read_dir, year)
            mask = (df["Date"] >=
                    f"{year}-07-19") & (df["Date"] <= f"{year}-12-01")
            subset = df.loc[mask].copy()
            subset["Data"] = subset["Data"].replace(-9999.0, pd.NA)
            records.append(
                {"Year": year, "MeanOzoneDeficit": subset["Data"].mean()})
        except FileNotFoundError:
            pass
    return pd.DataFrame(records)



def plot_eeasc(
    source: str | pd.DataFrame,
    ozone_means: pd.DataFrame | None = None,
    title: str = "EESC | Daily Ozone Deficit - Antarctica"
) -> go.Figure:

    if isinstance(source, str):
        df = pd.read_csv(source)
    else:
        df = source.copy()

    new_col = "EESC SUM (ppt)"
    required = {"Year", new_col}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Input is missing required columns: {missing}")

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df[new_col] = pd.to_numeric(df[new_col], errors="coerce") / 1000
    df = df.dropna(subset=["Year", new_col]).sort_values("Year")
    df = df.loc[df["Year"] >= 1992].copy()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        name="EESC",
        x=df["Year"],
        y=df[new_col],
        mode="lines+markers",
        line=dict(color="#1f77b4", width=2),
        marker=dict(size=5),
        hovertemplate="%{y:.3f} ppb<extra>EESC</extra>",
        yaxis="y1",
        showlegend=True
    ))

    if ozone_means is not None:
        fig.add_trace(go.Scatter(
            name="Mean Ozone Deficit (Jul–Dec)",
            x=ozone_means["Year"],
            y=ozone_means["MeanOzoneDeficit"],
            mode="lines+markers",
            line=dict(color="#e31a1c", width=2),
            marker=dict(size=5),
            hovertemplate="%{y:.3f} Mt<extra>Mean Ozone Deficit</extra>",
            yaxis="y2",
            showlegend=True
        ))


    fig.update_layout(
        title=title,
        xaxis=dict(tickmode="linear", 
                   showgrid=False,
                   tickangle=-45,
                   tickfont=dict(size=12),
                   showline=True,
                   linecolor="black",
                   linewidth=1),

        yaxis=dict(
            title="Equivalent Effective Antarctic<br>Stratospheric Chlorine (ppb)",
            side="right",
            range=[2.5, 4.25],
            autorange=False,
            tickmode="linear",
            tick0=2.5,
            dtick=0.25,
            showgrid=False,
            showline=True,
            linecolor="black",
            linewidth=1,
            ticklabelstandoff=8,
        ),
        yaxis2=dict(
            title="Vortex period (19 July - 1 December)<br>average daily ozone deficit (million tons)",
            overlaying="y",
            side="left",
            showgrid=False,
            range=[0, 20],
            autorange=False,
            showline=True,
            linecolor="black",
            linewidth=1,
            ticklabelstandoff=8,
        ),
        hovermode="x unified",
        template="plotly_white",
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=60, r=60, t=60, b=0),
        legend=dict(orientation="h", x=0.5,
                    xanchor="center", y=-0.2, yanchor="top")
    )

    return fig
