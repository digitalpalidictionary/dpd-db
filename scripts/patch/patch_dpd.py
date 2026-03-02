# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "python-idzip",
# ]
# ///

"""
===============================================================================
OFFLINE SUTTA LINK PATCHER (FOR DIGITAL PALI DICTIONARY)
===============================================================================

This tool updates your DPD dictionary files to point to your offline copy
of the Buddha's Words website.

INSTRUCTIONS:
1. Install the 'uv' runner:
   Windows:   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   Mac/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh

2. Save this script as 'patch_dpd.py' in your dictionary folder.

3. Run the script:
   uv run patch_dpd.py
"""

import os
import shutil
import idzip


def main():
    old_url = "https://thebuddhaswords.net/"
    new_url = "file:///buddhaswordsoffline/"

    target_dz = "dpd.dict.dz"
    target_dict = "dpd.dict"

    print("\n--- Patching DPD Sutta Links ---")

    if not os.path.exists(target_dz):
        print(f"Error: Could not find {target_dz} in this folder.")
        return

    # 1. Unzip using idzip (supports dictzip format)
    print(f"Unzipping {target_dz}... (please wait)")
    try:
        with idzip.open(target_dz, "rb") as f_in:
            with open(target_dict, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
    except Exception as e:
        print(f"Error unzipping: {e}")
        return

    # 2. Replace URL and remove target="_blank"
    print("Replacing links and removing security restrictions...")
    try:
        with open(target_dict, "r", encoding="utf-8", errors="ignore") as f:
            data = f.read()

        if old_url in data:
            new_data = data.replace(old_url, new_url)
            # Remove target="_blank" so GoldenDict allows local file:// links
            new_data = new_data.replace('target="_blank"', "")

            with open(target_dict, "w", encoding="utf-8") as f:
                f.write(new_data)
            print("Successfully patched links.")
        else:
            print("No links found (perhaps already patched?).")
    except Exception as e:
        print(f"Error replacing links: {e}")
        return

    # 3. Zip back into proper DICTZIP format
    print(f"Re-zipping into {target_dz} (proper DictZip format)...")
    try:
        # Use idzip to create a true dictzip-compatible file
        with open(target_dict, "rb") as f_in:
            with open(target_dz, "wb") as f_out:
                # Get the size of the uncompressed file
                f_in_info = os.fstat(f_in.fileno())
                # Compress into proper dictzip format
                # Note: argument is 'basename', not 'filename'
                idzip.compressor.compress(  # type: ignore
                    f_in,
                    f_in_info.st_size,
                    f_out,
                    basename=target_dz,
                    mtime=int(f_in_info.st_mtime),
                )
        print("Dictionary file updated and compressed.")
    except Exception as e:
        print(f"Error zipping: {e}")
        return

    # Cleanup temporary unzipped file
    if os.path.exists(target_dict):
        os.remove(target_dict)

    print("\n" + "=" * 40)
    print("DONE! Your links are updated and clickable.")
    print(f"{old_url} >> {new_url}")
    print("Please restart GoldenDict.")
    print("=" * 40 + "\n")


if __name__ == "__main__":
    main()
