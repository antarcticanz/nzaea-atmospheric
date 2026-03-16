"""
update_daily_ozone_deficit.py

Incrementally downloads NASA Ozone Mass Deficit (OMD) daily files.

Behaviour:
----------
• Downloads missing yearly files from NASA OzoneWatch
• Detects latest year already stored locally
• Always checks up to (current system year + 1)
• Skips future unpublished files gracefully
• Refreshes the current year's file automatically (NASA updates daily values)
• Safe to run on a scheduler (Task Scheduler / cron / Airflow etc.)

NOTE:
-----
The output directory MUST be passed to the function.
"""

import requests
from datetime import datetime
from pathlib import Path
import re


BASE_URL = (
    "https://ozonewatch.gsfc.nasa.gov/meteorology/figures/ozone/"
    "omds_{year}_toms+omi+omps.txt"
)

START_YEAR = 1979


# ---------------- HELPERS ---------------- #

def _get_latest_downloaded_year(write_dir: Path) -> int:
    """
    Scan the local directory for existing yearly files
    and return the most recent year found.
    """

    pattern = re.compile(r"omds_(\d{4})\.txt")
    years = []

    for f in write_dir.glob("omds_*.txt"):
        match = pattern.search(f.name)
        if match:
            years.append(int(match.group(1)))

    if not years:
        return START_YEAR - 1

    return max(years)


def _download_year(year: int, write_dir: Path) -> bool:
    """
    Attempt to download a specific year from NASA.
    Returns True if successful, False if not yet available.
    """

    url = BASE_URL.format(year=year)
    out_file = write_dir / f"omds_{year}.txt"

    try:
        resp = requests.get(url, timeout=30)

        if resp.status_code == 404:
            print(f"— {year} not yet available from NASA")
            return False

        resp.raise_for_status()

        out_file.write_text(resp.text)
        print(f"↓ Downloaded {year}")

        return True

    except Exception as e:
        print(f"⚠ Failed to download {year}: {e}")
        return False


# ---------------- MAIN UPDATE ---------------- #

def update_ozone_deficit_archive(write_dir: Path | str):

    write_dir = Path(write_dir)
    write_dir.mkdir(parents=True, exist_ok=True)

    current_year = datetime.now().year
    check_until = current_year + 1

    # --- Refresh current year (NASA updates daily) --- #
    current_file = write_dir / f"omds_{current_year}.txt"
    if current_file.exists():
        current_file.unlink()
        print(f"↻ Refreshing {current_year}")

    latest_local = _get_latest_downloaded_year(write_dir)

    start_year = latest_local + 1
    if start_year < START_YEAR:
        start_year = START_YEAR

    print("\n-----------------------------")
    print(f"Latest local year: {latest_local}")
    print(f"Checking {start_year} → {check_until}")
    print("-----------------------------\n")

    for yr in range(start_year, check_until + 1):

        out_file = write_dir / f"omds_{yr}.txt"

        # Skip if already exists (except current year handled above)
        if out_file.exists():
            print(f"✓ Already have {yr}")
            continue

        success = _download_year(yr, write_dir)

        # Stop early if future year isn't published yet
        if not success:
            break

    print("\n✅ Archive update complete.\n")


# ---------------- ENTRY POINT (OPTIONAL) ---------------- #

if __name__ == "__main__":

    DEFAULT_DIR = Path(
        r"C:\Users\ANTNZDEV\michaelmeredythyoung\github\nzaea-atmospheric\data\ozone\daily_ozone_deficit"
    )

    update_ozone_deficit_archive(DEFAULT_DIR)
