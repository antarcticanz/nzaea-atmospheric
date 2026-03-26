from pathlib import Path
import plotly.graph_objects as go
import xarray as xr
import pandas as pd
from statsmodels.nonparametric.smoothers_lowess import lowess

def plot_n20_change(
    nc_path: str | Path,
    year_min: int = 1996,
    loess_frac: float = 0.1,
) -> go.Figure:
    """
    Plot annual rate of change in atmospheric N2O derived from the LOESS trend.

    The annual change is calculated using interpolated LOESS values at
    1 January of each year, e.g.:

        change for 1997 = LOESS(1997-01-01) - LOESS(1996-01-01)

    The resulting annual change values are shown as scatter points with
    a faint dashed connecting line.

    Parameters
    ----------
    nc_path : str or pathlib.Path
        Path to the NetCDF file.
    year_min : int, default 1996
        First year to include in the source data.
    loess_frac : float, default 0.1
        LOWESS fraction controlling smoothing strength for the original time series.

    Returns
    -------
    plotly.graph_objects.Figure
        Interactive Plotly figure of annual change points with a faint dashed connector.
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
    # 3. Select N2O mole fraction
    # --------------------------------------------------
    n20 = ds["value"]

    df = (
        n20.to_dataframe(name="n20_ppb")
        .reset_index()
        .dropna(subset=["n20_ppb", "time"])
    )

    # --------------------------------------------------
    # 4. Filter to year_min onwards
    # --------------------------------------------------
    df = df[df["time"].dt.year >= year_min].copy()

    if df.empty:
        raise ValueError(f"No valid n20 data found from {year_min} onwards.")

    df["n20_ppb"] = df["n20_ppb"].round(0)

    # --------------------------------------------------
    # 5. LOWESS smoothing on original time series
    # --------------------------------------------------
    x_numeric = df["time"].astype("int64") // 10**9  # seconds since epoch
    y = df["n20_ppb"].values

    loess_vals = lowess(
        endog=y,
        exog=x_numeric,
        frac=loess_frac,
        return_sorted=False,
    )

    df["loess_ppb"] = loess_vals

    # --------------------------------------------------
    # 6. Interpolate LOESS values to 1 January each year
    # --------------------------------------------------
    trend_series = (
        df[["time", "loess_ppb"]]
        .sort_values("time")
        .groupby("time", as_index=True)["loess_ppb"]
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

    # --------------------------------------------------
    # 7. Calculate annual rate of change
    # --------------------------------------------------
    annual_df["change_ppb_per_year"] = annual_df["loess_year_value"].diff()

    change_df = annual_df.dropna(subset=["change_ppb_per_year"]).copy()

    if change_df.empty:
        raise ValueError("Not enough annual LOESS values to calculate change.")

    change_df["period"] = (
        (change_df["year"] - 1).astype(str) +
        " to " + change_df["year"].astype(str)
    )

    # --------------------------------------------------
    # 8. Plot faint dashed connector + scatter points
    # --------------------------------------------------
    fig = go.Figure()

    # Faint dashed connecting line
    fig.add_trace(
        go.Scatter(
            x=change_df["year"],
            y=change_df["change_ppb_per_year"],
            mode="lines",
            name="Annual Change",
            line=dict(
                color="#1f77b4",
                width=1.4,
                dash="dash",
            ),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Scatter points
    fig.add_trace(
        go.Scatter(
            x=change_df["year"],
            y=change_df["change_ppb_per_year"],
            mode="markers",
            name="Annual Change",
            marker=dict(
                size=8,
                color="#1f77b4",
                opacity=0.95,
            ),
            hovertemplate=(
                "Period: %{customdata}<br>"
                "N<sub>2</sub>O Annual Change: %{y:.2f} ppb/year"
                "<extra>Annual Change</extra>"
            ),
            customdata=change_df["period"],
        )
    )

    fig.add_hline(
        y=0,
        line_width=1.0,
        line_dash="dash",
        line_color="lightgray",
    )

    fig.update_layout(
        title="Annual Rate of Change in Atmospheric Nitrous Oxide (N<sub>2</sub>O)",
        template="plotly_white",
        hovermode="x unified",
        xaxis=dict(
            tickmode="linear",
            dtick=1,
            tickangle=90,
            showline=True,
            linewidth=1.3,
            linecolor="black",
            showgrid=False,
        ),
        yaxis=dict(
            title="Rate of Change of N<sub>2</sub>O (ppb/year)",
            showline=True,
            linewidth=1.3,
            linecolor="black",
            showgrid=False,
            tickformat=".2f",
            range=[0, 2]

        ),
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
