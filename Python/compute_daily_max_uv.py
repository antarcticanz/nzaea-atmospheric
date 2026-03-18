# """
# Compute daily maximum UV Index (UVI) from NDACC-style input data.

# The input may be:
#   - a path to a CSV file, or
#   - a pandas DataFrame already in memory

# Required columns:
#   - Year, Month, Day
#   - Either UVI or UVEry
# """

# from __future__ import annotations

# from pathlib import Path
# from typing import Union

# import numpy as np
# import pandas as pd


# SourceLike = Union[str, Path, pd.DataFrame]


# def compute_daily_max_uvi(
#     source: SourceLike,
#     *,
#     uvi_col: str | None = "UVI",
#     uvery_col: str = "UVEry",
#     sentinel: float = 9.999e9,
#     convert_from_uvery_if_needed: bool = True,
#     attach_season_year: bool = True,
# ) -> pd.DataFrame:
#     """
#     Returns a tidy dataframe with one row per calendar day containing
#     the daily maximum UVI, keeping ONLY dates from Sep 1 through Jan 1
#     (inclusive) for each Sep→Jan season.

#     Assumes input timestamps are in UT (NDACC SUV convention).

#     Parameters
#     ----------
#     source : str | pathlib.Path | pandas.DataFrame
#         Input data source (CSV file path or DataFrame)
#     uvi_col : str or None
#         Name of column containing UVI values (set None to compute from UVEry)
#     uvery_col : str
#         Name of erythemal dose-rate column if UVI must be computed
#     sentinel : float
#         NDACC missing-value sentinel
#     convert_from_uvery_if_needed : bool
#         Whether to compute UVI from UVEry if UVI is not provided
#     attach_season_year : bool
#         Whether to include season_year column

#     Returns
#     -------
#     pandas.DataFrame
#         Daily maximum UVI for Sep–Jan seasons
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
#     # Build Date from Year / Month / Day
#     # --------------------------------------------------
#     df["Date"] = pd.to_datetime(
#         dict(year=df["Year"], month=df["Month"], day=df["Day"]),
#         errors="coerce",
#     )
#     df = df.dropna(subset=["Date"])

#     # --------------------------------------------------
#     # Ensure UVI exists and clean sentinel values
#     # --------------------------------------------------
#     if uvi_col is None:
#         if not convert_from_uvery_if_needed:
#             raise ValueError(
#                 "uvi_col is None. Enable conversion or provide a UVI column."
#             )
#         if uvery_col not in df.columns:
#             raise ValueError(f"{uvery_col} column not found.")

#         u = pd.to_numeric(df[uvery_col], errors="coerce")
#         u[(u >= sentinel) | (~np.isfinite(u))] = np.nan
#         df["UVI"] = u * 40.0
#         uvi_col = "UVI"

#     else:
#         if uvi_col not in df.columns:
#             raise ValueError(f"{uvi_col} column not found.")
#         u = pd.to_numeric(df[uvi_col], errors="coerce")
#         u[(u >= sentinel) | (~np.isfinite(u))] = np.nan
#         df[uvi_col] = u

#     # --------------------------------------------------
#     # Aggregate to daily maximum
#     # --------------------------------------------------
#     daily_max = (
#         df.groupby(["Year", "Month", "Day", "Date"], as_index=False)[uvi_col]
#           .max(min_count=1)
#           .rename(columns={uvi_col: "DailyMaxUVI"})
#     )

#     # --------------------------------------------------
#     # Season year (Sep–Dec → same year; Jan → previous year)
#     # --------------------------------------------------
#     m = daily_max["Date"].dt.month
#     y = daily_max["Date"].dt.year
#     daily_max["season_year"] = np.where(m == 1, y - 1, y)

#     # --------------------------------------------------
#     # Keep only Sep 1 → Jan 1 (inclusive)
#     # --------------------------------------------------
#     season_start = pd.to_datetime(
#         daily_max["season_year"].astype(str) + "-09-01")
#     season_end = pd.to_datetime(
#         (daily_max["season_year"] + 1).astype(str) + "-01-01")

#     mask = (daily_max["Date"] >= season_start) & (
#         daily_max["Date"] <= season_end)
#     daily_max = daily_max.loc[mask].copy()

#     if not attach_season_year:
#         daily_max = daily_max.drop(columns=["season_year"])

#     return daily_max


# # --------------------------------------------------
# # Optional CLI
# # --------------------------------------------------
# if __name__ == "__main__":
#     import sys

#     if len(sys.argv) < 3:
#         print("Usage: python compute_daily_max_uvi.py input.csv output.csv")
#         sys.exit(1)

#     inp, out = sys.argv[1], sys.argv[2]
#     result = compute_daily_max_uvi(inp)
#     result.to_csv(out, index=False)
#     print(f"Wrote daily max UVI to {out}")


"""
Compute daily maximum UV Index (UVI), UVA, and UVB from NDACC-style input data.

The input may be:
  - a path to a CSV file, or
  - a pandas DataFrame already in memory

Required columns:
  - Year, Month, Day
  - Any of: UVI, UVA, UVB, UVEry (configurable)
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd


SourceLike = Union[str, Path, pd.DataFrame]


def compute_daily_max_uv(
    source: SourceLike,
    *,
    columns: list[str] | None = None,
    uvery_col: str = "UVEry",
    sentinel: float = 9.999e9,
    convert_from_uvery_if_needed: bool = True,
    attach_season_year: bool = True,
) -> pd.DataFrame:
    """
    Returns a tidy dataframe with one row per calendar day containing
    the daily maximum for each requested UV column, keeping ONLY dates
    from Sep 1 through Jan 1 (inclusive) for each Sep→Jan season.

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

    Returns
    -------
    pandas.DataFrame
        Daily maximum UV values for Sep–Jan seasons, with columns:
        Year, Month, Day, Date, DailyMax_UVI, DailyMax_UVA, DailyMax_UVB
        (plus season_year if attach_season_year=True)
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
    # Aggregate to daily maximum
    # --------------------------------------------------
    daily_max = (
        df.groupby(["Year", "Month", "Day", "Date"], as_index=False)[columns]
          .max(min_count=1)
          .rename(columns={c: f"DailyMax_{c}" for c in columns})
    )

    # --------------------------------------------------
    # Season year (Sep–Dec → same year; Jan → previous year)
    # --------------------------------------------------
    m = daily_max["Date"].dt.month
    y = daily_max["Date"].dt.year
    daily_max["season_year"] = np.where(m == 1, y - 1, y)

    # --------------------------------------------------
    # Keep only Sep 1 → Jan 1 (inclusive)
    # --------------------------------------------------
    season_start = pd.to_datetime(
        daily_max["season_year"].astype(str) + "-09-01")
    season_end = pd.to_datetime(
        (daily_max["season_year"] + 1).astype(str) + "-01-01")

    mask = (daily_max["Date"] >= season_start) & (
        daily_max["Date"] <= season_end)
    daily_max = daily_max.loc[mask].copy()

    if not attach_season_year:
        daily_max = daily_max.drop(columns=["season_year"])

    return daily_max


# --------------------------------------------------
# Optional CLI
# --------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python compute_daily_max_uvi.py input.csv output.csv")
        sys.exit(1)

    inp, out = sys.argv[1], sys.argv[2]
    result = compute_daily_max_uvi(inp)
    result.to_csv(out, index=False)
    print(f"Wrote daily max UV to {out}")
