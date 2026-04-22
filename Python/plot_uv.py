# # """
# # Plot a Sep–Jan climatology of daily maximum UV Index with variability shading.

# # Input may be:
# #   - a CSV file path, or
# #   - a pandas DataFrame (output of compute_daily_max_uvi)

# # Required columns:
# #   - Date (datetime)
# #   - DailyMax_UVI (float)
# #   - season_year (int)
# # """

# from __future__ import annotations

# from pathlib import Path
# from typing import Union

# import numpy as np
# import pandas as pd
# import plotly.graph_objects as go


# SourceLike = Union[str, Path, pd.DataFrame]


# def plot_dailymax_uvi(
#     source: SourceLike,
#     *,
#     show_inner_band: bool = True,
#     year_to_overlay: int | None = None,
#     title: str = "UV Index (Arrival Heights, Antarctica)",
# ) -> go.Figure:
#     """
#     Plot Sep 1 → Jan 31 climatology of Daily Maximum UVI with shaded variability.
#     """

#     # --------------------------------------------------
#     # Load input
#     # --------------------------------------------------
#     if isinstance(source, pd.DataFrame):
#         df = source.copy()
#     else:
#         path = Path(source)
#         if not path.exists():
#             raise FileNotFoundError(f"Input file not found: {path}")
#         df = pd.read_csv(path)

#     # --------------------------------------------------
#     # Guard rails and types
#     # --------------------------------------------------
#     required_cols = {"Date", "DailyMax_UVI", "season_year"}
#     missing = required_cols - set(df.columns)
#     if missing:
#         raise ValueError(f"Input is missing required columns: {missing}")

#     df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
#     df = df.dropna(subset=["Date"])

#     # --------------------------------------------------
#     # Keep Sep–Dec + January
#     # --------------------------------------------------
#     m = df["Date"].dt.month
#     df = df.loc[m.isin([9, 10, 11, 12, 1])].copy()

#     # --------------------------------------------------
#     # Map each date to a "season day"
#     # --------------------------------------------------
#     season_start = pd.to_datetime(df["season_year"].astype(str) + "-09-01")
#     df["season_day"] = (df["Date"] - season_start).dt.days + 1

#     # Anchor x-axis
#     anchor = pd.Timestamp(2000, 9, 1)
#     df["x_date"] = anchor + pd.to_timedelta(df["season_day"] - 1, unit="D")

#     # Cap at Jan 1
#     end_date = pd.Timestamp(2001, 1, 1)
#     df = df.loc[(df["x_date"] >= anchor) & (df["x_date"] <= end_date)].copy()

#     # --------------------------------------------------
#     # Climatology
#     # --------------------------------------------------
#     clim = (
#         df.groupby("season_day")
#         .agg(
#             min=("DailyMax_UVI", "min"),
#             mean=("DailyMax_UVI", "mean"),
#             max=("DailyMax_UVI", "max"),
#             p10=("DailyMax_UVI", lambda s: np.nanpercentile(s, 10)),
#             p90=("DailyMax_UVI", lambda s: np.nanpercentile(s, 90)),
#         )
#         .reset_index()
#     )

#     clim["x_date"] = anchor + pd.to_timedelta(clim["season_day"] - 1, unit="D")
#     clim = clim.sort_values("x_date")

#     # --------------------------------------------------
#     # Figure
#     # --------------------------------------------------
#     x = clim["x_date"]
#     fig = go.Figure()

#     # Outer band
#     fig.add_trace(go.Scatter(
#         x=x,
#         y=clim["max"],
#         mode="lines",
#         line=dict(color="rgba(105,179,162,0)"),
#         showlegend=False,
#         hoverinfo="skip",
#     ))
#     fig.add_trace(go.Scatter(
#         name="Range (min–max)",
#         x=x,
#         y=clim["min"],
#         mode="lines",
#         line=dict(color="rgba(105,179,162,0)"),
#         fill="tonexty",
#         fillcolor="rgba(105,179,162,0.28)",
#         customdata=np.c_[clim["max"].to_numpy()],
#         hovertemplate="Min–Max: %{y:.2f} – %{customdata:.2f}<extra></extra>",
#         showlegend=True,
#     ))

#     # Inner band
#     if show_inner_band:
#         fig.add_trace(go.Scatter(
#             x=x,
#             y=clim["p90"],
#             mode="lines",
#             line=dict(color="rgba(31,120,180,0)"),
#             showlegend=False,
#             hoverinfo="skip",
#         ))
#         fig.add_trace(go.Scatter(
#             name="Inner 10–90%",
#             x=x,
#             y=clim["p10"],
#             mode="lines",
#             line=dict(color="rgba(31,120,180,0)"),
#             fill="tonexty",
#             fillcolor="rgba(31,120,180,0.22)",
#             customdata=np.c_[clim["p90"].to_numpy()],
#             hovertemplate="P10–P90: %{y:.2f} – %{customdata:.2f}<extra></extra>",
#             showlegend=True,
#         ))

#     # Mean
#     fig.add_trace(go.Scatter(
#         name="Mean",
#         x=x,
#         y=clim["mean"],
#         mode="lines",
#         line=dict(color="#1f78b4", width=2),
#         hovertemplate="Mean: %{y:.2f}<extra></extra>",
#         showlegend=True,
#     ))

#     # Optional overlay year
#     if year_to_overlay is not None:
#         one = df.loc[df["season_year"] == int(
#             year_to_overlay)].sort_values("x_date")
#         if not one.empty:
#             fig.add_trace(go.Scatter(
#                 name=str(year_to_overlay),
#                 x=one["x_date"],
#                 y=one["DailyMax_UVI"],
#                 mode="lines",
#                 line=dict(color="#e31a1c", width=1.6, dash="dash"),
#                 hovertemplate=(
#                     f"{year_to_overlay}: "
#                     "%{y:.2f}<extra></extra>"
#                 ),
#                 showlegend=True,
#             ))

#     # --------------------------------------------------
#     # Layout
#     # --------------------------------------------------
#     fig.update_layout(
#         title=title,
#         template="plotly_white",
#         hovermode="x unified",
#         xaxis=dict(
#             type="date",
#             tickformat="%d-%b",
#             dtick=14 * 24 * 60 * 60 * 1000,
#             range=[anchor, end_date],
#         ),
#         yaxis=dict(title="UV Index"),
#         legend=dict(
#             orientation="h",
#             x=0.5,
#             xanchor="center",
#             y=-0.12,
#             yanchor="top",
#         ),
#         margin=dict(l=60, r=20, t=70, b=100),
#     )

#     return fig


# """
# Plot a Sep–Jan climatology of daily maximum UVA and UVB with variability shading.

# Input may be:
#   - a CSV file path, or
#   - a pandas DataFrame (output of compute_daily_max_uvi)

# Required columns:
#   - Date (datetime)
#   - DailyMax_UVA or DailyMax_UVB (float)
#   - season_year (int)
# """


# SourceLike = Union[str, Path, pd.DataFrame]


# def plot_dailymax_uva(
#     source: SourceLike,
#     *,
#     show_inner_band: bool = True,
#     year_to_overlay: int | None = None,
#     title: str = "UVA (Arrival Heights, Antarctica)",
# ) -> go.Figure:
#     """
#     Plot Sep 1 → Jan 31 climatology of Daily Maximum UVA with shaded variability.
#     """

#     # --------------------------------------------------
#     # Load input
#     # --------------------------------------------------
#     if isinstance(source, pd.DataFrame):
#         df = source.copy()
#     else:
#         path = Path(source)
#         if not path.exists():
#             raise FileNotFoundError(f"Input file not found: {path}")
#         df = pd.read_csv(path)

#     # --------------------------------------------------
#     # Guard rails and types
#     # --------------------------------------------------
#     required_cols = {"Date", "DailyMax_UVA", "season_year"}
#     missing = required_cols - set(df.columns)
#     if missing:
#         raise ValueError(f"Input is missing required columns: {missing}")

#     df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
#     df = df.dropna(subset=["Date"])

#     # --------------------------------------------------
#     # Keep Sep–Dec + January
#     # --------------------------------------------------
#     m = df["Date"].dt.month
#     df = df.loc[m.isin([9, 10, 11, 12, 1])].copy()

#     # --------------------------------------------------
#     # Map each date to a "season day"
#     # --------------------------------------------------
#     season_start = pd.to_datetime(df["season_year"].astype(str) + "-09-01")
#     df["season_day"] = (df["Date"] - season_start).dt.days + 1

#     # Anchor x-axis
#     anchor = pd.Timestamp(2000, 9, 1)
#     df["x_date"] = anchor + pd.to_timedelta(df["season_day"] - 1, unit="D")

#     # Cap at Jan 1
#     end_date = pd.Timestamp(2001, 1, 1)
#     df = df.loc[(df["x_date"] >= anchor) & (df["x_date"] <= end_date)].copy()

#     # --------------------------------------------------
#     # Climatology
#     # --------------------------------------------------
#     clim = (
#         df.groupby("season_day")
#         .agg(
#             min=("DailyMax_UVA", "min"),
#             mean=("DailyMax_UVA", "mean"),
#             max=("DailyMax_UVA", "max"),
#             p10=("DailyMax_UVA", lambda s: np.nanpercentile(s, 10)),
#             p90=("DailyMax_UVA", lambda s: np.nanpercentile(s, 90)),
#         )
#         .reset_index()
#     )

#     clim["x_date"] = anchor + pd.to_timedelta(clim["season_day"] - 1, unit="D")
#     clim = clim.sort_values("x_date")

#     # --------------------------------------------------
#     # Figure
#     # --------------------------------------------------
#     x = clim["x_date"]
#     fig = go.Figure()

#     # Outer band
#     fig.add_trace(go.Scatter(
#         x=x,
#         y=clim["max"],
#         mode="lines",
#         line=dict(color="rgba(105,179,162,0)"),
#         showlegend=False,
#         hoverinfo="skip",
#     ))
#     fig.add_trace(go.Scatter(
#         name="Range (min–max)",
#         x=x,
#         y=clim["min"],
#         mode="lines",
#         line=dict(color="rgba(105,179,162,0)"),
#         fill="tonexty",
#         fillcolor="rgba(105,179,162,0.28)",
#         customdata=np.c_[clim["max"].to_numpy()],
#         hovertemplate="Min–Max: %{y:.2f} – %{customdata:.2f}<extra></extra>",
#         showlegend=True,
#     ))

#     # Inner band
#     if show_inner_band:
#         fig.add_trace(go.Scatter(
#             x=x,
#             y=clim["p90"],
#             mode="lines",
#             line=dict(color="rgba(31,120,180,0)"),
#             showlegend=False,
#             hoverinfo="skip",
#         ))
#         fig.add_trace(go.Scatter(
#             name="Inner 10–90%",
#             x=x,
#             y=clim["p10"],
#             mode="lines",
#             line=dict(color="rgba(31,120,180,0)"),
#             fill="tonexty",
#             fillcolor="rgba(31,120,180,0.22)",
#             customdata=np.c_[clim["p90"].to_numpy()],
#             hovertemplate="P10–P90: %{y:.2f} – %{customdata:.2f}<extra></extra>",
#             showlegend=True,
#         ))

#     # Mean
#     fig.add_trace(go.Scatter(
#         name="Mean",
#         x=x,
#         y=clim["mean"],
#         mode="lines",
#         line=dict(color="#1f78b4", width=2),
#         hovertemplate="Mean: %{y:.2f}<extra></extra>",
#         showlegend=True,
#     ))

#     # Optional overlay year
#     if year_to_overlay is not None:
#         one = df.loc[df["season_year"] == int(
#             year_to_overlay)].sort_values("x_date")
#         if not one.empty:
#             fig.add_trace(go.Scatter(
#                 name=str(year_to_overlay),
#                 x=one["x_date"],
#                 y=one["DailyMax_UVA"],
#                 mode="lines",
#                 line=dict(color="#e31a1c", width=1.6, dash="dash"),
#                 hovertemplate=(
#                     f"{year_to_overlay}: "
#                     "%{y:.2f}<extra></extra>"
#                 ),
#                 showlegend=True,
#             ))

#     # --------------------------------------------------
#     # Layout
#     # --------------------------------------------------
#     fig.update_layout(
#         title=title,
#         template="plotly_white",
#         hovermode="x unified",
#         xaxis=dict(
#             type="date",
#             tickformat="%d-%b",
#             dtick=14 * 24 * 60 * 60 * 1000,
#             range=[anchor, end_date],
#         ),
#         yaxis=dict(title="UVA"),
#         legend=dict(
#             orientation="h",
#             x=0.5,
#             xanchor="center",
#             y=-0.12,
#             yanchor="top",
#         ),
#         margin=dict(l=60, r=20, t=70, b=100),
#     )

#     return fig


# def plot_dailymax_uvb(
#     source: SourceLike,
#     *,
#     show_inner_band: bool = True,
#     year_to_overlay: int | None = None,
#     title: str = "UVB (Arrival Heights, Antarctica)",
# ) -> go.Figure:
#     """
#     Plot Sep 1 → Jan 31 climatology of Daily Maximum UVB with shaded variability.
#     """

#     # --------------------------------------------------
#     # Load input
#     # --------------------------------------------------
#     if isinstance(source, pd.DataFrame):
#         df = source.copy()
#     else:
#         path = Path(source)
#         if not path.exists():
#             raise FileNotFoundError(f"Input file not found: {path}")
#         df = pd.read_csv(path)

#     # --------------------------------------------------
#     # Guard rails and types
#     # --------------------------------------------------
#     required_cols = {"Date", "DailyMax_UVB", "season_year"}
#     missing = required_cols - set(df.columns)
#     if missing:
#         raise ValueError(f"Input is missing required columns: {missing}")

#     df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
#     df = df.dropna(subset=["Date"])

#     # --------------------------------------------------
#     # Keep Sep–Dec + January
#     # --------------------------------------------------
#     m = df["Date"].dt.month
#     df = df.loc[m.isin([9, 10, 11, 12, 1])].copy()

#     # --------------------------------------------------
#     # Map each date to a "season day"
#     # --------------------------------------------------
#     season_start = pd.to_datetime(df["season_year"].astype(str) + "-09-01")
#     df["season_day"] = (df["Date"] - season_start).dt.days + 1

#     # Anchor x-axis
#     anchor = pd.Timestamp(2000, 9, 1)
#     df["x_date"] = anchor + pd.to_timedelta(df["season_day"] - 1, unit="D")

#     # Cap at Jan 1
#     end_date = pd.Timestamp(2001, 1, 1)
#     df = df.loc[(df["x_date"] >= anchor) & (df["x_date"] <= end_date)].copy()

#     # --------------------------------------------------
#     # Climatology
#     # --------------------------------------------------
#     clim = (
#         df.groupby("season_day")
#         .agg(
#             min=("DailyMax_UVB", "min"),
#             mean=("DailyMax_UVB", "mean"),
#             max=("DailyMax_UVB", "max"),
#             p10=("DailyMax_UVB", lambda s: np.nanpercentile(s, 10)),
#             p90=("DailyMax_UVB", lambda s: np.nanpercentile(s, 90)),
#         )
#         .reset_index()
#     )

#     clim["x_date"] = anchor + pd.to_timedelta(clim["season_day"] - 1, unit="D")
#     clim = clim.sort_values("x_date")

#     # --------------------------------------------------
#     # Figure
#     # --------------------------------------------------
#     x = clim["x_date"]
#     fig = go.Figure()

#     # Outer band
#     fig.add_trace(go.Scatter(
#         x=x,
#         y=clim["max"],
#         mode="lines",
#         line=dict(color="rgba(105,179,162,0)"),
#         showlegend=False,
#         hoverinfo="skip",
#     ))
#     fig.add_trace(go.Scatter(
#         name="Range (min–max)",
#         x=x,
#         y=clim["min"],
#         mode="lines",
#         line=dict(color="rgba(105,179,162,0)"),
#         fill="tonexty",
#         fillcolor="rgba(105,179,162,0.28)",
#         customdata=np.c_[clim["max"].to_numpy()],
#         hovertemplate="Min–Max: %{y:.2f} – %{customdata:.2f}<extra></extra>",
#         showlegend=True,
#     ))

#     # Inner band
#     if show_inner_band:
#         fig.add_trace(go.Scatter(
#             x=x,
#             y=clim["p90"],
#             mode="lines",
#             line=dict(color="rgba(31,120,180,0)"),
#             showlegend=False,
#             hoverinfo="skip",
#         ))
#         fig.add_trace(go.Scatter(
#             name="Inner 10–90%",
#             x=x,
#             y=clim["p10"],
#             mode="lines",
#             line=dict(color="rgba(31,120,180,0)"),
#             fill="tonexty",
#             fillcolor="rgba(31,120,180,0.22)",
#             customdata=np.c_[clim["p90"].to_numpy()],
#             hovertemplate="P10–P90: %{y:.2f} – %{customdata:.2f}<extra></extra>",
#             showlegend=True,
#         ))

#     # Mean
#     fig.add_trace(go.Scatter(
#         name="Mean",
#         x=x,
#         y=clim["mean"],
#         mode="lines",
#         line=dict(color="#1f78b4", width=2),
#         hovertemplate="Mean: %{y:.2f}<extra></extra>",
#         showlegend=True,
#     ))

#     # Optional overlay year
#     if year_to_overlay is not None:
#         one = df.loc[df["season_year"] == int(
#             year_to_overlay)].sort_values("x_date")
#         if not one.empty:
#             fig.add_trace(go.Scatter(
#                 name=str(year_to_overlay),
#                 x=one["x_date"],
#                 y=one["DailyMax_UVB"],
#                 mode="lines",
#                 line=dict(color="#e31a1c", width=1.6, dash="dash"),
#                 hovertemplate=(
#                     f"{year_to_overlay}: "
#                     "%{y:.2f}<extra></extra>"
#                 ),
#                 showlegend=True,
#             ))

#     # --------------------------------------------------
#     # Layout
#     # --------------------------------------------------
#     fig.update_layout(
#         title=title,
#         template="plotly_white",
#         hovermode="x unified",
#         xaxis=dict(
#             type="date",
#             tickformat="%d-%b",
#             dtick=14 * 24 * 60 * 60 * 1000,
#             range=[anchor, end_date],
#         ),
#         yaxis=dict(title="UVB"),
#         legend=dict(
#             orientation="h",
#             x=0.5,
#             xanchor="center",
#             y=-0.12,
#             yanchor="top",
#         ),
#         margin=dict(l=60, r=20, t=70, b=100),
#     )

#     return fig


# """
# Plot a Sep–Jan climatology of daily maximum UV Index with variability shading.

# Input may be:
#   - a CSV file path, or
#   - a pandas DataFrame (output of compute_daily_max_uvi)

# Required columns:
#   - Date (datetime)
#   - DailyMax_UVI (float)
#   - season_year (int)
# """

from __future__ import annotations

from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd
import plotly.graph_objects as go


SourceLike = Union[str, Path, pd.DataFrame]


def plot_daily_uvi(
    source: SourceLike,
    *,
    show_inner_band: bool = True,
    year_to_overlay: int | None = None,
    title: str = "UV Index, Arrival Heights, Antarctica, 1990-2024",
) -> go.Figure:
    """
    Plot Sep 1 → Jan 1 climatology of Daily Maximum UVI with shaded variability.

    Expects pre-filtered, pre-aggregated input from compute_daily_max_uv()
    with columns: Date, DailyMax_UVI, season_year.
    Missing days should already be NaN in the input.
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
    # Guard rails
    # --------------------------------------------------
    required_cols = {"Date", "DailyMax_UVI", "season_year"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Input is missing required columns: {missing}")

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    # --------------------------------------------------
    # Season day + anchor x-axis
    # --------------------------------------------------
    anchor = pd.Timestamp(2000, 9, 1)
    end_date = pd.Timestamp(2001, 1, 1)

    season_start = pd.to_datetime(df["season_year"].astype(str) + "-09-01")
    df["season_day"] = (df["Date"] - season_start).dt.days + 1
    df["x_date"] = anchor + pd.to_timedelta(df["season_day"] - 1, unit="D")
    df = df.loc[(df["x_date"] >= anchor) & (df["x_date"] <= end_date)].copy()

    # --------------------------------------------------
    # Full date spine — missing days become NaN, not absent
    # --------------------------------------------------
    all_days = pd.DataFrame({
        "x_date":     pd.date_range(anchor, end_date, freq="D"),
        "season_day": range(1, (end_date - anchor).days + 2),
    })

    # --------------------------------------------------
    # Climatology
    # --------------------------------------------------
    clim = (
        df.groupby("season_day")
        .agg(
            clim_min=("DailyMax_UVI", "min"),
            clim_max=("DailyMax_UVI", "max"),
            p10=("DailyMax_UVI", lambda s: np.nanpercentile(
                s.dropna(), 10) if s.notna().any() else np.nan),
            p90=("DailyMax_UVI", lambda s: np.nanpercentile(
                s.dropna(), 90) if s.notna().any() else np.nan),
        )
        .reset_index()
    )
    clim = all_days.merge(clim, on="season_day",
                          how="left").sort_values("x_date")

    # --------------------------------------------------
    # Figure
    # --------------------------------------------------
    x = clim["x_date"]
    fig = go.Figure()

    # Outer band ceiling (invisible)
    fig.add_trace(go.Scatter(
        x=x, y=clim["clim_max"], mode="lines",
        line=dict(color="rgba(0,0,0,0)"),
        showlegend=False, hoverinfo="skip",
    ))
    # Outer band floor fills up to ceiling
    fig.add_trace(go.Scatter(
        name="Range (min-max)",
        x=x, y=clim["clim_min"], mode="lines",
        line=dict(color="rgba(0,0,0,0)"),
        fill="tonexty", fillcolor="rgba(105,179,162,0.28)",
        customdata=np.c_[clim["clim_max"].to_numpy()],
        hovertemplate="Min-Max: %{y:.2f} – %{customdata[0]:.2f}<extra></extra>",
    ))

    if show_inner_band:
        # Inner band ceiling (invisible)
        fig.add_trace(go.Scatter(
            x=x, y=clim["p90"], mode="lines",
            line=dict(color="rgba(0,0,0,0)"),
            showlegend=False, hoverinfo="skip",
        ))
        # Inner band floor fills up to ceiling
        fig.add_trace(go.Scatter(
            name="Inner 10–90%",
            x=x, y=clim["p10"], mode="lines",
            line=dict(color="rgba(0,0,0,0)"),
            fill="tonexty", fillcolor="rgba(31,120,180,0.22)",
            customdata=np.c_[clim["p90"].to_numpy()],
            hovertemplate="P10–P90: %{y:.2f} – %{customdata[0]:.2f}<extra></extra>",
        ))

    # Optional overlay year
    if year_to_overlay is not None:
        one = (
            df.loc[df["season_year"] == int(year_to_overlay), [
                "season_day", "DailyMax_UVI"]]
            .set_index("season_day")
            .reindex(all_days["season_day"])
            .reset_index()
        )
        one = all_days.merge(one, on="season_day",
                             how="left").sort_values("x_date")
        if not one["DailyMax_UVI"].isna().all():
            fig.add_trace(go.Scatter(
                #name=str(year_to_overlay),
                name=f"UVI Max {str(year_to_overlay)}",
                x=one["x_date"], y=one["DailyMax_UVI"],
                mode="lines",
                line=dict(color="#e31a1c", width=1.6, dash="dash"),
                connectgaps=False,
                #hovertemplate=f"UVI Max {year_to_overlay}: %{{y:.2f}}<extra></extra>",
                #hovertemplate=f"UVI Max {year_to_overlay}: %{{x|%d-%b}}, %{{y:.2f}}<extra></extra>"
                hovertemplate=f"UVI Max (%{{x|%d-%b}}): %{{y:.2f}}<extra></extra>"

            ))

    # --------------------------------------------------
    # Layout
    # --------------------------------------------------
    fig.update_layout(
        title=title,
        template="plotly_white",
        hovermode="closest",
        xaxis=dict(
            type="date",
            tickformat="%d-%b",
            hoverformat="%d-%b",
            dtick=7 * 24 * 60 * 60 * 1000,
            range=[anchor, end_date],
            showgrid=False, 
            showline=True,
            linecolor="black",
            zeroline=False,

        ),
        yaxis=dict(title="UV Index",
                   showgrid=False,
                   showline=True,
                   linecolor="black",
                   zeroline=False),
        legend=dict(
            orientation="h",
            x=0.5, xanchor="center",
            y=-0.12, yanchor="top",
        ),
        margin=dict(l=60, r=20, t=70, b=100),
    )

    return fig


# def plot_daily_uv(
#     source: SourceLike,
#     *,
#     show_inner_band: bool = True,
#     year_to_overlay: int | None = None,
#     title: str = "UVA/UVB, Arrival Heights, Antarctica, 1990-2024",
# ) -> go.Figure:
#     """
#     Plot Sep 1 → Jan 31 climatology of Daily Maximum UVA (left axis) and
#     UVB (right axis) with shaded variability bands.

#     Expects pre-filtered, pre-aggregated input from compute_daily_max_uv()
#     with columns: Date, DailyMax_UVA, DailyMax_UVB, season_year.
#     Missing days should already be NaN in the input.
#     """

#     # --------------------------------------------------
#     # Load input
#     # --------------------------------------------------
#     if isinstance(source, pd.DataFrame):
#         df = source.copy()
#     else:
#         path = Path(source)
#         if not path.exists():
#             raise FileNotFoundError(f"Input file not found: {path}")
#         df = pd.read_csv(path)

#     # --------------------------------------------------
#     # Guard rails
#     # --------------------------------------------------
#     required_cols = {"Date", "DailyMax_UVA", "DailyMax_UVB", "season_year"}
#     missing = required_cols - set(df.columns)
#     if missing:
#         raise ValueError(f"Input is missing required columns: {missing}")

#     df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
#     df = df.dropna(subset=["Date"])

#     # --------------------------------------------------
#     # Season day + anchor x-axis
#     # --------------------------------------------------
#     anchor = pd.Timestamp(2000, 9, 1)
#     end_date = pd.Timestamp(2001, 1, 1)

#     season_start = pd.to_datetime(df["season_year"].astype(str) + "-09-01")
#     df["season_day"] = (df["Date"] - season_start).dt.days + 1
#     df["x_date"] = anchor + pd.to_timedelta(df["season_day"] - 1, unit="D")
#     df = df.loc[(df["x_date"] >= anchor) & (df["x_date"] <= end_date)].copy()

#     # --------------------------------------------------
#     # Full date spine — missing days become NaN rows, not absent rows
#     # --------------------------------------------------
#     all_days = pd.DataFrame({
#         "x_date":     pd.date_range(anchor, end_date, freq="D"),
#         "season_day": range(1, (end_date - anchor).days + 2),
#     })

#     # --------------------------------------------------
#     # Climatology helper
#     # --------------------------------------------------
#     def make_clim(col: str) -> pd.DataFrame:
#         clim = (
#             df.groupby("season_day")
#             .agg(
#                 clim_min=(col, "min"),
#                 clim_max=(col, "max"),
#                 p10=(col, lambda s: np.nanpercentile(
#                     s.dropna(), 10) if s.notna().any() else np.nan),
#                 p90=(col, lambda s: np.nanpercentile(
#                     s.dropna(), 90) if s.notna().any() else np.nan),
#             )
#             .reset_index()
#         )
#         return all_days.merge(clim, on="season_day", how="left").sort_values("x_date")

#     clim_uva = make_clim("DailyMax_UVA")
#     clim_uvb = make_clim("DailyMax_UVB")

#     # --------------------------------------------------
#     # Overlay year helper — daily max for a single season
#     # --------------------------------------------------
#     def make_overlay(col: str) -> pd.DataFrame | None:
#         if year_to_overlay is None:
#             return None
#         one = (
#             df.loc[df["season_year"] == int(year_to_overlay), [
#                 "season_day", col]]
#             .set_index("season_day")
#             .reindex(all_days["season_day"])
#             .reset_index()
#         )
#         return all_days.merge(one, on="season_day", how="left").sort_values("x_date")

#     # --------------------------------------------------
#     # Figure
#     # --------------------------------------------------
#     fig = go.Figure()

#     def add_band_traces(clim: pd.DataFrame, col: str, col_label: str, yaxis: str,
#                         outer_color: str, inner_color: str) -> None:
#         x = clim["x_date"]

#         # Outer band ceiling (invisible)
#         fig.add_trace(go.Scatter(
#             x=x, y=clim["clim_max"], mode="lines",
#             line=dict(color="rgba(0,0,0,0)"),
#             showlegend=False, hoverinfo="skip",
#             yaxis=yaxis,
#         ))
#         # Outer band floor fills up to ceiling
#         fig.add_trace(go.Scatter(
#             name=f"{col_label} Range (min–max)",
#             x=x, y=clim["clim_min"], mode="lines",
#             line=dict(color="rgba(0,0,0,0)"),
#             fill="tonexty", fillcolor=outer_color,
#             customdata=np.c_[clim["clim_max"].to_numpy()],
#             hovertemplate=f"{col_label} Min/Max: %{{y:.2f}} – %{{customdata[0]:.2f}}<extra></extra>",
#             yaxis=yaxis,
#         ))

#         if show_inner_band:
#             # Inner band ceiling (invisible)
#             fig.add_trace(go.Scatter(
#                 x=x, y=clim["p90"], mode="lines",
#                 line=dict(color="rgba(0,0,0,0)"),
#                 showlegend=False, hoverinfo="skip",
#                 yaxis=yaxis,
#             ))
#             # Inner band floor fills up to ceiling
#             fig.add_trace(go.Scatter(
#                 name=f"{col_label} Inner 10–90%",
#                 x=x, y=clim["p10"], mode="lines",
#                 line=dict(color="rgba(0,0,0,0)"),
#                 fill="tonexty", fillcolor=inner_color,
#                 customdata=np.c_[clim["p90"].to_numpy()],
#                 hovertemplate=f"{col_label} P10–P90: %{{y:.2f}} – %{{customdata[0]:.2f}}<extra></extra>",
#                 yaxis=yaxis,
#             ))



#     # UVB bands
#     add_band_traces(
#         clim_uvb, "DailyMax_UVB", "UVB", yaxis="y2",
#         outer_color="rgba(230,97,1,0.22)",
#         inner_color="rgba(230,97,1,0.40)",
#     )

#     # UVB overlay year
#     if year_to_overlay is not None:
#         one = make_overlay("DailyMax_UVB")
#         if one is not None and not one["DailyMax_UVB"].isna().all():
#             fig.add_trace(go.Scatter(
#                 name=f"UVB Max {year_to_overlay}",
#                 x=one["x_date"], y=one["DailyMax_UVB"],
#                 mode="lines",
#                 line=dict(color="#984ea3", width=1.6, dash="dash"),
#                 connectgaps=False,
#                 hovertemplate=f"UVB Max {year_to_overlay}: %{{y:.2f}}<extra></extra>",
#                 yaxis="y2",
#             ))

#     # UVA bands
#     add_band_traces(
#         clim_uva, "DailyMax_UVA", "UVA", yaxis="y",
#         outer_color="rgba(105,179,162,0.28)",
#         inner_color="rgba(31,120,180,0.22)",
#     )

#     # UVA overlay year
#     if year_to_overlay is not None:
#         one = make_overlay("DailyMax_UVA")
#         if one is not None and not one["DailyMax_UVA"].isna().all():
#             fig.add_trace(go.Scatter(
#                 name=f"UVA Max {year_to_overlay}",
#                 x=one["x_date"], y=one["DailyMax_UVA"],
#                 mode="lines",
#                 line=dict(color="#e31a1c", width=1.6, dash="dash"),
#                 connectgaps=False,
#                 hovertemplate=f"UVA Max {year_to_overlay}: %{{y:.2f}}<extra></extra>",
#                 yaxis="y",
#             ))

#     # --------------------------------------------------
#     # Layout
#     # --------------------------------------------------
#     fig.update_layout(
#         title=title,
#         template="plotly_white",
#         hovermode="x",
#         xaxis=dict(
#             type="date",
#             tickformat="%d-%b",
#             dtick=14 * 24 * 60 * 60 * 1000,
#             range=[anchor, end_date],
#             showgrid=False,
#             showline=True,
#             linecolor="black",
#             hoverformat="%d-%b",
#         ),
#         yaxis=dict(
#             title="UVA",
#             range=[0, 45],
#             side="left",
#             showgrid=False,            
#             showline=True,
#             linecolor="black",
#         ),
#         yaxis2=dict(
#             title="UVB",
#             range=[0, 5],
#             side="right",
#             overlaying="y",
#             showgrid=False,
#             showline=True,
#             linecolor="black",
#         ),
#         legend=dict(
#             orientation="h",
#             x=0.5, xanchor="center",
#             y=-0.15, yanchor="top",
#         ),
#         margin=dict(l=60, r=60, t=70, b=120),
#     )

#     return fig


def plot_daily_uv(
    source: SourceLike,
    *,
    show_inner_band: bool = True,
    year_to_overlay: int | None = None,
    title: str = "UVA/UVB, Arrival Heights, Antarctica, 1990-2024",
) -> go.Figure:
    """
    Plot Sep 1 → Jan 31 climatology of Daily Maximum UVA (left axis) and
    UVB (right axis) with shaded variability bands.

    Expects pre-filtered, pre-aggregated input from compute_daily_max_uv()
    with columns: Date, DailyMax_UVA, DailyMax_UVB, season_year.
    Missing days should already be NaN in the input.
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
    # Guard rails
    # --------------------------------------------------
    required_cols = {"Date", "DailyMax_UVA", "DailyMax_UVB", "season_year"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Input is missing required columns: {missing}")

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    # --------------------------------------------------
    # Season day + anchor x-axis
    # --------------------------------------------------
    anchor = pd.Timestamp(2000, 9, 1)
    end_date = pd.Timestamp(2001, 1, 1)

    season_start = pd.to_datetime(df["season_year"].astype(str) + "-09-01")
    df["season_day"] = (df["Date"] - season_start).dt.days + 1
    df["x_date"] = anchor + pd.to_timedelta(df["season_day"] - 1, unit="D")
    df = df.loc[(df["x_date"] >= anchor) & (df["x_date"] <= end_date)].copy()

    # --------------------------------------------------
    # Full date spine — missing days become NaN rows, not absent rows
    # --------------------------------------------------
    all_days = pd.DataFrame({
        "x_date":     pd.date_range(anchor, end_date, freq="D"),
        "season_day": range(1, (end_date - anchor).days + 2),
    })

    # --------------------------------------------------
    # Climatology helper
    # --------------------------------------------------
    def make_clim(col: str) -> pd.DataFrame:
        clim = (
            df.groupby("season_day")
            .agg(
                clim_min=(col, "min"),
                clim_max=(col, "max"),
                p10=(col, lambda s: np.nanpercentile(
                    s.dropna(), 10) if s.notna().any() else np.nan),
                p90=(col, lambda s: np.nanpercentile(
                    s.dropna(), 90) if s.notna().any() else np.nan),
            )
            .reset_index()
        )
        return all_days.merge(clim, on="season_day", how="left").sort_values("x_date")

    clim_uva = make_clim("DailyMax_UVA")
    clim_uvb = make_clim("DailyMax_UVB")

    # --------------------------------------------------
    # Overlay year helper — daily max for a single season
    # --------------------------------------------------
    def make_overlay(col: str) -> pd.DataFrame | None:
        if year_to_overlay is None:
            return None
        one = (
            df.loc[df["season_year"] == int(year_to_overlay), [
                "season_day", col]]
            .set_index("season_day")
            .reindex(all_days["season_day"])
            .reset_index()
        )
        return all_days.merge(one, on="season_day", how="left").sort_values("x_date")

    # --------------------------------------------------
    # Figure
    # --------------------------------------------------
    fig = go.Figure()

    def add_band_traces(clim: pd.DataFrame, col: str, col_label: str, yaxis: str,
                        outer_color: str, inner_color: str, legend_ref: str) -> None:
        x = clim["x_date"]

        # Outer band ceiling (invisible)
        fig.add_trace(go.Scatter(
            x=x, y=clim["clim_max"], mode="lines",
            line=dict(color="rgba(0,0,0,0)"),
            showlegend=False, hoverinfo="skip",
            yaxis=yaxis,
        ))
        # Outer band floor fills up to ceiling
        fig.add_trace(go.Scatter(
            name=f"{col_label} Range (min–max)",
            x=x, y=clim["clim_min"], mode="lines",
            line=dict(color="rgba(0,0,0,0)"),
            fill="tonexty", fillcolor=outer_color,
            customdata=np.c_[clim["clim_max"].to_numpy()],
            hovertemplate=f"{col_label} Min-Max: %{{y:.2f}} – %{{customdata[0]:.2f}}<extra></extra>",
            yaxis=yaxis,
            legend=legend_ref,
        ))

        if show_inner_band:
            # Inner band ceiling (invisible)
            fig.add_trace(go.Scatter(
                x=x, y=clim["p90"], mode="lines",
                line=dict(color="rgba(0,0,0,0)"),
                showlegend=False, hoverinfo="skip",
                yaxis=yaxis,
            ))
            # Inner band floor fills up to ceiling
            fig.add_trace(go.Scatter(
                name=f"{col_label} Inner 10–90%",
                x=x, y=clim["p10"], mode="lines",
                line=dict(color="rgba(0,0,0,0)"),
                fill="tonexty", fillcolor=inner_color,
                customdata=np.c_[clim["p90"].to_numpy()],
                hovertemplate=f"{col_label} P10–P90: %{{y:.2f}} – %{{customdata[0]:.2f}}<extra></extra>",
                yaxis=yaxis,
                legend=legend_ref,
            ))

    # UVB bands — bottom legend row
    add_band_traces(
        clim_uvb, "DailyMax_UVB", "UVB", yaxis="y2",
        outer_color="rgba(230,97,1,0.22)",
        inner_color="rgba(230,97,1,0.40)",
        legend_ref="legend2",
    )

    # UVB overlay year
    if year_to_overlay is not None:
        one = make_overlay("DailyMax_UVB")
        if one is not None and not one["DailyMax_UVB"].isna().all():
            fig.add_trace(go.Scatter(
                name=f"UVB Max {year_to_overlay}",
                x=one["x_date"], y=one["DailyMax_UVB"],
                mode="lines",
                line=dict(color="#984ea3", width=1.6, dash="dash"),
                connectgaps=False,
                hovertemplate=f"UVB Max {year_to_overlay}: %{{y:.2f}}<extra></extra>",
                yaxis="y2",
                legend="legend2",
            ))

    # UVA bands — top legend row
    add_band_traces(
        clim_uva, "DailyMax_UVA", "UVA", yaxis="y",
        outer_color="rgba(105,179,162,0.28)",
        inner_color="rgba(31,120,180,0.22)",
        legend_ref="legend",
    )

    # UVA overlay year
    if year_to_overlay is not None:
        one = make_overlay("DailyMax_UVA")
        if one is not None and not one["DailyMax_UVA"].isna().all():
            fig.add_trace(go.Scatter(
                name=f"UVA Max {year_to_overlay}",
                x=one["x_date"], y=one["DailyMax_UVA"],
                mode="lines",
                line=dict(color="#e31a1c", width=1.6, dash="dash"),
                connectgaps=False,
                hovertemplate=f"UVA Max {year_to_overlay}: %{{y:.2f}}<extra></extra>",
                yaxis="y",
                legend="legend",
            ))

    # --------------------------------------------------
    # Layout
    # --------------------------------------------------
    fig.update_layout(
        title=title,
        template="plotly_white",
        hovermode="x",
        xaxis=dict(
            type="date",
            tickformat="%d-%b",
            dtick=14 * 24 * 60 * 60 * 1000,
            range=[anchor, end_date],
            showgrid=False,
            showline=True,
            linecolor="black",
            hoverformat="%d-%b",
        ),
        yaxis=dict(
            title="UVA",
            range=[0, 60],
            side="left",
            showgrid=False,
            showline=True,
            linecolor="black",
        ),
        yaxis2=dict(
            title="UVB",
            range=[0, 5],
            side="right",
            overlaying="y",
            showgrid=False,
            showline=True,
            linecolor="black",
        ),
        legend=dict(
            orientation="h",
            x=0.5, xanchor="center",
            y=-0.15, yanchor="top",
            tracegroupgap=0,
        ),
        legend2=dict(
            orientation="h",
            x=0.5, xanchor="center",
            y=-0.25, yanchor="top",
            tracegroupgap=0,
        ),
        margin=dict(l=60, r=60, t=70, b=140),
    )

    return fig









def plot_raw_uvi(
    source: SourceLike,
    *,
    title: str = "UV Index, Arrival Heights, Antarctica, 1990-2024",
) -> go.Figure:
    """
    Plot raw (non-aggregated) UVI observations as a scatter/line.

    Expects input with columns: Date, UVI (or DailyMax_UVI).
    """

    if isinstance(source, pd.DataFrame):
        df = source.copy()
    else:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path}")
        df = pd.read_csv(path)

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).sort_values("Date")

    # Accept either column name
    uvi_col = "UVI" if "UVI" in df.columns else "DailyMax_UVI"
    if uvi_col not in df.columns:
        raise ValueError("Input must have a 'UVI' or 'DailyMax_UVI' column.")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        name="UVI",
        x=df["Date"],
        y=df[uvi_col],
        mode="lines",
        line=dict(color="#1f78b4", width=1),
        connectgaps=False,
        hovertemplate="UVI: %{y:.2f}<extra></extra>",
    ))

    fig.update_layout(
        title=title,
        template="plotly_white",
        hovermode="x",
        xaxis=dict(
            type="date",
            tickformat="%b-%Y",
            hoverformat="%d-%b-%Y",
            showgrid=False,
            showline=True,
            linecolor="black",
            zeroline=False,
        ),
        yaxis=dict(
            title="UV Index",
            showgrid=False,
            showline=True,
            linecolor="black",
            zeroline=False,
        ),
        legend=dict(
            orientation="h",
            x=0.5, xanchor="center",
            y=-0.12, yanchor="top",
        ),
        margin=dict(l=60, r=20, t=70, b=100),
    )

    return fig


def plot_raw_uv(
    source: SourceLike,
    *,
    title: str = "UVA/UVB, Arrival Heights, Antarctica, 1990-2024",
) -> go.Figure:
    """
    Plot raw (non-aggregated) UVA (left axis) and UVB (right axis) observations.

    Expects input with columns: Date, UVA, UVB (or DailyMax_UVA, DailyMax_UVB).
    """

    if isinstance(source, pd.DataFrame):
        df = source.copy()
    else:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path}")
        df = pd.read_csv(path)

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).sort_values("Date")

    # Accept either column naming convention
    uva_col = "UVA" if "UVA" in df.columns else "DailyMax_UVA"
    uvb_col = "UVB" if "UVB" in df.columns else "DailyMax_UVB"
    missing = [c for c in [uva_col, uvb_col] if c not in df.columns]
    if missing:
        raise ValueError(f"Input is missing required columns: {missing}")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        name="UVA",
        x=df["Date"],
        y=df[uva_col],
        mode="lines",
        line=dict(color="#1f78b4", width=1),
        connectgaps=False,
        hovertemplate="UVA: %{y:.2f}<extra></extra>",
        yaxis="y",
    ))

    fig.add_trace(go.Scatter(
        name="UVB",
        x=df["Date"],
        y=df[uvb_col],
        mode="lines",
        line=dict(color="#e6611a", width=1),
        connectgaps=False,
        hovertemplate="UVB: %{y:.2f}<extra></extra>",
        yaxis="y2",
    ))

    fig.update_layout(
        title=title,
        template="plotly_white",
        hovermode="x",
        xaxis=dict(
            type="date",
            tickformat="%b-%Y",
            hoverformat="%d-%b-%Y",
            showgrid=False,
            showline=True,
            linecolor="black",
            zeroline=False,
        ),
        yaxis=dict(
            title="UVA",
            side="left",
            showgrid=False,
            showline=True,
            linecolor="black",
            zeroline=False,
            range=[0, 50],

        ),
        yaxis2=dict(
            title="UVB",
            side="right",
            overlaying="y",
            showgrid=False,
            showline=True,
            linecolor="black",
            zeroline=False,
            range=[0, 5],

        ),
        legend=dict(
            orientation="h",
            x=0.5, xanchor="center",
            y=-0.12, yanchor="top",
        ),
        margin=dict(l=60, r=60, t=70, b=100),
    )

    return fig
