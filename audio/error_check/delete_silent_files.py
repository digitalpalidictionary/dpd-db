import multiprocessing
import math
import time
from pathlib import Path

# High-performance audio decoding
import miniaudio
import numpy as np
from rich.progress import Progress
from rich.console import Console
from tools.printer import printer as pr
from tools.paths import ProjectPaths

# CONFIGURATION
pth = ProjectPaths()
SILENCE_THRESHOLD_DB = -60.0  # dB
MIN_FILE_SIZE_BYTES = 1024  # Skip files smaller than 1KB

console = Console()


def check_file(filepath: Path) -> Path | None:
    """
    Decodes MP3 to float32 and checks RMS dB.
    Returns filepath if silent/corrupt, otherwise None.
    """
    try:
        # 1. FAST CHECK: File Size
        if filepath.stat().st_size < MIN_FILE_SIZE_BYTES:
            return filepath

        # 2. DECODE: miniaudio (Native C binding, extremely fast)
        # Decodes directly to a memory object of float32 samples
        decoded = miniaudio.mp3_read_file_f32(str(filepath))

        # 3. COMPUTE RMS: Numpy
        # Wrap the memoryview in a numpy array without copying data
        samples = np.array(decoded.samples, copy=False)

        if samples.size == 0:
            return filepath

        # Calculate RMS (Root Mean Square)
        # mean(samples^2) -> sqrt -> log10
        rms_amplitude = np.sqrt(np.mean(samples**2))

        # Avoid log(0)
        if rms_amplitude <= 1e-9:
            db = -float("inf")
        else:
            db = 20 * math.log10(rms_amplitude)

        if db < SILENCE_THRESHOLD_DB:
            return filepath

    except miniaudio.DecodeError:
        # File is corrupt or not an mp3
        return filepath
    except Exception as e:
        # Catch unexpected IO errors
        pr.error(f"error {filepath}: {e}")
        return filepath

    return None


def gather_mp3_files() -> list[Path]:
    """
    Gather all MP3 files from folders with '_0.85' in their names.
    """
    files: list[Path] = []
    pr.info("scanning folders with '_0.85' for mp3s")

    # Find all folders with "_0.85" in their names
    folders_with_085: list[Path] = [
        folder
        for folder in pth.dpd_audio_mp3_dir.iterdir()
        if folder.is_dir() and "_0.85" in folder.name
    ]

    for folder in folders_with_085:
        files.extend(list(folder.glob("*.mp3")))

    pr.info(f"found {len(files)} files. processing...")
    return files


def process_files(files: list[Path]) -> list[Path]:
    """
    Process files in parallel to check for silence.
    """
    # Use all available cores
    num_processes = multiprocessing.cpu_count()

    silent_files: list[Path] = []

    with Progress() as progress:
        task = progress.add_task("[cyan]Scanning Audio...", total=len(files))

        # Chunksize: crucial for speed with small tasks.
        # Sends batches of 100 filenames to each worker at a time
        # to reduce inter-process communication overhead.
        chunk_size = 100

        with multiprocessing.Pool(processes=num_processes) as pool:
            for result in pool.imap_unordered(check_file, files, chunksize=chunk_size):
                if result:
                    silent_files.append(result)
                progress.update(task, advance=1)

    return silent_files


def save_results(silent_files: list[Path]) -> None:
    """
    Save the list of silent files to a file.
    """
    # Save list to a file in the same directory as the script
    output_path = Path(__file__).parent / "deleted_silent_files.txt"
    with open(output_path, "w") as f:
        for path in silent_files:
            f.write(f"{path}\n")

    pr.info(f"results saved to: {output_path}")


def play_audio(filepath: Path) -> None:
    """Plays the audio file using miniaudio and waits for it to finish."""
    try:
        # Decode to get duration and sample rate for waiting
        decoded = miniaudio.mp3_read_file_f32(str(filepath))
        # duration = total_samples / (sample_rate * channels)
        duration = len(decoded.samples) / (decoded.sample_rate * decoded.nchannels)

        # Use stream_file for playback
        stream = miniaudio.stream_file(str(filepath))
        with miniaudio.PlaybackDevice() as device:
            device.start(stream)
            time.sleep(duration + 0.2)  # Add a small buffer for safety
    except Exception as e:
        pr.error(f"error playing {filepath}: {e}")


def delete_silent_files(silent_files: list[Path]) -> None:
    """
    Delete the list of silent or corrupt files.
    """
    for filepath in silent_files:
        try:
            filepath.unlink()
        except Exception as e:
            pr.error(f"failed to delete {filepath}: {e}")

    pr.info(f"deleted {len(silent_files)} silent/corrupt files.")


def find_and_delete_silent_files() -> None:
    """
    Find and delete silent or corrupt MP3 files.
    Non-interactive version for use in other scripts.
    """
    files = gather_mp3_files()

    if not files:
        pr.error("no files found.")
        return

    silent_files = process_files(files)
    if silent_files:
        pr.info(f"found {len(silent_files)} blank/corrupt files. deleting...")
        save_results(silent_files)
        delete_silent_files(silent_files)
    else:
        pr.info("no blank or corrupt files found.")


def interactive_delete() -> None:
    """
    Find and delete silent or corrupt MP3 files interactively.
    """
    pr.info("identifying silent/corrupt files...")
    files = gather_mp3_files()
    if not files:
        pr.error("no files found.")
        return

    silent_files = process_files(files)
    if not silent_files:
        pr.info("no silent or corrupt files found.")
        return

    pr.info(f"found {len(silent_files)} blank/corrupt files.")

    for i, filepath in enumerate(silent_files):
        while True:
            console.print(
                f"\n[{i + 1}/{len(silent_files)}] [cyan]{filepath.name}[/cyan]"
            )
            play_audio(filepath)

            choice = (
                console.input(
                    "[bold yellow]Options: (d) delete, (r) replay, (any other key) pass: "
                )
                .lower()
                .strip()
            )

            if choice == "d":
                try:
                    filepath.unlink()
                    pr.info(f"deleted: {filepath.name}")
                    break
                except Exception as e:
                    pr.error(f"failed to delete {filepath.name}: {e}")
                    break
            elif choice == "r":
                continue
            else:
                pr.info("passed.")
                break


if __name__ == "__main__":
    # interactive_delete()
    find_and_delete_silent_files()
