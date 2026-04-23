# """
# Compute daily maximum UV Index (UVI) from NDACC-style input data.

# The input may be:
#   - a path to a CSV file, or
#   - a pandas DataFrame already in memory

# Required columns:
#   - Year, Month, Day
#   - Either UVI or UVEry
# """

from __future__ import annotations

from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd


SourceLike = Union[str, Path, pd.DataFrame]




def compute_daily_uv(
    source: SourceLike,
    *,
    columns: list[str] | None = None,
    uvery_col: str = "UVEry",
    sentinel: float = 9.999e9,
    convert_from_uvery_if_needed: bool = True,
    attach_season_year: bool = True,
    sky_filter: int = 0,
    flag_filter: int = 0,
) -> pd.DataFrame:
    """
    Returns a tidy dataframe with one row per calendar day containing
    the daily maximum for each requested UV column, keeping ONLY dates
    from Sep 1 through Jan 1 (inclusive) for each Sep→Jan season.

    Filters to Sky == sky_filter and Flag == flag_filter before aggregating.

    Assumes input timestamps are in UT (NDACC SUV convention).

    Parameters
    ----------
    source : str | pathlib.Path | pandas.DataFrame
        Input data source (CSV file path or DataFrame)
    columns : list[str] or None
        UV columns to compute daily maxima for.
        Defaults to ["UVI", "UVA", "UVB"].
    uvery_col : str
        Name of erythemal dose-rate column if UVI must be computed from UVEry.
    sentinel : float
        NDACC missing-value sentinel.
    convert_from_uvery_if_needed : bool
        Whether to compute UVI from UVEry if UVI is not present in the data.
    attach_season_year : bool
        Whether to include season_year column in output.
    sky_filter : int
        Keep only rows where Sky == this value (default 1 = clear sky).
    flag_filter : int
        Keep only rows where Flag == this value (default 0 = unflagged).

    Returns
    -------
    pandas.DataFrame
        Daily maximum UV values for Sep–Mar seasons, with columns:
        Year, Month, Day, Date, DailyMax_UVI, DailyMax_UVA, DailyMax_UVB
        (plus season_year if attach_season_year=True).
        Days with no valid observations after filtering are NaN (not zero).
    """

    if columns is None:
        columns = ["UVI", "UVA", "UVB"]

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
    # Build Date from Year / Month / Day
    # --------------------------------------------------
    df["Date"] = pd.to_datetime(
        dict(year=df["Year"], month=df["Month"], day=df["Day"]),
        errors="coerce",
    )
    df = df.dropna(subset=["Date"])

    # --------------------------------------------------
    # Filter Sky and Flag
    # --------------------------------------------------
    missing_filter_cols = [c for c in ("Sky", "Flag") if c not in df.columns]
    if missing_filter_cols:
        raise ValueError(
            f"Input is missing filter columns: {missing_filter_cols}")

    df = df.loc[(df["Sky"] == sky_filter) & (df["Flag"] == flag_filter)].copy()


    # --------------------------------------------------
    # Keep Sep–Dec + January only (before expensive aggregation)
    # --------------------------------------------------
    # df = df.loc[df["Date"].dt.month.isin([9, 10, 11, 12, 1])].copy()
    df = df.loc[df["Date"].dt.month.isin([9, 10, 11, 12, 1, 2, 3])].copy()

    # --------------------------------------------------
    # Clean each requested column
    # --------------------------------------------------
    for col in columns:
        if col == "UVI" and col not in df.columns:
            if not convert_from_uvery_if_needed:
                raise ValueError(
                    "UVI column not found. Enable convert_from_uvery_if_needed "
                    "or provide a UVI column."
                )
            if uvery_col not in df.columns:
                raise ValueError(f"'{uvery_col}' column not found.")
            u = pd.to_numeric(df[uvery_col], errors="coerce")
            u[(u >= sentinel) | (~np.isfinite(u))] = np.nan
            df["UVI"] = u * 40.0
        else:
            if col not in df.columns:
                raise ValueError(f"'{col}' column not found in input data.")
            u = pd.to_numeric(df[col], errors="coerce")
            u[(u >= sentinel) | (~np.isfinite(u))] = np.nan
            df[col] = u

    # --------------------------------------------------
    # Season year (Sep–Dec → same year; Jan → previous year)
    # --------------------------------------------------
    m = df["Date"].dt.month
    y = df["Date"].dt.year
    #df["season_year"] = np.where(m == 1, y - 1, y)
    df["season_year"] = np.where(m.isin([1, 2, 3]), y - 1, y)

    # --------------------------------------------------
    # Aggregate to daily maximum
    # min_count=1 ensures days with all-NaN observations stay NaN, not zero
    # --------------------------------------------------
    group_cols = ["Year", "Month", "Day", "Date", "season_year"]
    daily_max = (
        df.groupby(group_cols, as_index=False)[columns]
          .max(min_count=1)
          .rename(columns={c: f"DailyMax_{c}" for c in columns})
    )

    # --------------------------------------------------
    # Keep only Sep 1 → Jan 1 (inclusive)
    # --------------------------------------------------
    season_start = pd.to_datetime(
        daily_max["season_year"].astype(str) + "-09-01")
    # season_end = pd.to_datetime(
    #     (daily_max["season_year"] + 1).astype(str) + "-01-01")
    season_end = pd.to_datetime(
        (daily_max["season_year"] + 1).astype(str) + "-03-31")
    mask = (daily_max["Date"] >= season_start) & (
        daily_max["Date"] <= season_end)
    daily_max = daily_max.loc[mask].copy()

    if not attach_season_year:
        daily_max = daily_max.drop(columns=["season_year"])

    return daily_max
