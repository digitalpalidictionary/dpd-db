from pathlib import Path

import pandas as pd
from rich import print


def read_dv_catalogue_excel() -> dict[str, dict[str, str]]:
    """Read DV Catalogue Excel file and convert to dict with SUTTACODE as key.

    First row contains general headings (skipped), second row contains actual column names.
    All column names are converted to lowercase.
    """
    excel_path = Path("db/suttas/DV Catalogue 5.1.xlsx")

    # Read Excel file, skipping the first row and using second row as headers
    df = pd.read_excel(excel_path, skiprows=1)

    # Convert column names to lowercase
    df.columns = [str(col).lower() for col in df.columns]

    # Remove duplicates by keeping first occurrence of each SUTTACODE
    df = df.drop_duplicates(subset=["suttacode"], keep="first")

    # Set SUTTACODE as index and convert to dict
    df.set_index("suttacode", inplace=True)
    catalogue_dict = df.to_dict("index")

    return catalogue_dict  # type: ignore[return-value]


def main():
    catalogue_dict = read_dv_catalogue_excel()
    print(catalogue_dict)


if __name__ == "__main__":
    main()
