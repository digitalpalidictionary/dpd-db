import os
import zipfile
from pathlib import Path
from tools.printer import printer as pr


def zip_up_file(
    input_file: Path,
    output_file: Path,
    compression_level: int = 9,
    delete_original: bool = False,
):
    """
    Zip up an output file with compression and optionally delete the original file.

    Parameters:
    input_file (pathlib.Path): Path to the input file
    output_file (pathlib.Path): Path to the output file
    compression_level (int, optional): Compression level for the zip file, from 0 (no compression) to 9 (best compression). Defaults to 9.
    delete_original (bool, optional): Whether to delete the original file after zipping. Defaults to False.

    Raises:
    FileNotFoundError: If the input file does not exist
    PermissionError: If the user does not have permission to delete the file
    """
    # Check if the input file exists
    if not input_file.exists():
        raise FileNotFoundError(f"Input file {input_file} does not exist.")

    # Create the output directory if it doesn't exist
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Zip the output file with compression
    with zipfile.ZipFile(
        str(output_file),
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=compression_level,
    ) as zip_file:
        zip_file.write(str(input_file), os.path.basename(str(input_file)))

    # Optionally delete the original file
    if delete_original:
        try:
            input_file.unlink()
        except PermissionError:
            print(f"Unable to delete {input_file} due to permission error.")


def zip_up_directory(
    input_dir: Path, compression_level: int = 9, delete_original: bool = False
):
    """
    Zip up an entire directory with compression and place the zip file in the parent directory.

    Parameters:
    input_dir (pathlib.Path): Path to the input directory
    compression_level (int, optional): Compression level for the zip file, from 0 (no compression) to 9 (best compression). Defaults to 9.
    delete_original (bool, optional): Whether to delete the original directory after zipping. Defaults to False.

    Raises:
    FileNotFoundError: If the input directory does not exist
    PermissionError: If the user does not have permission to delete the directory
    """
    # Check if the input directory exists
    if not input_dir.exists() or not input_dir.is_dir():
        raise FileNotFoundError(
            f"Input directory {input_dir} does not exist or is not a directory."
        )

    # Define the output zip file path
    output_file = input_dir.parent / f"{input_dir.name}.zip"

    # Zip the entire directory with compression
    with zipfile.ZipFile(
        str(output_file),
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=compression_level,
    ) as zip_file:
        for root, _, files in os.walk(input_dir):
            for file in files:
                file_path = Path(root) / file
                zip_file.write(
                    str(file_path), str(file_path.relative_to(input_dir.parent))
                )

    # Optionally delete the original directory
    if delete_original:
        try:
            for root, _, files in os.walk(input_dir, topdown=False):
                for file in files:
                    (Path(root) / file).unlink()
                for dir in Path(root).iterdir():
                    if dir.is_dir():
                        dir.rmdir()
            input_dir.rmdir()
        except PermissionError:
            print(f"Unable to delete {input_dir} due to permission error.")


def unzip_file(zip_path: Path, destination_dir: Path):
    """
    Unzip a file to the destination directory.
    """
    pr.green(f"unzipping {zip_path.name}")

    if not zip_path.exists():
        raise FileNotFoundError(f"Zip file not found: {zip_path}")

    destination_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(destination_dir)

    pr.yes("ok")
