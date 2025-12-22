import multiprocessing
import subprocess
import re
from pathlib import Path
from rich.progress import Progress
from rich.console import Console
from tools.printer import printer as pr
from tools.paths import ProjectPaths

# CONFIGURATION
pth = ProjectPaths()
SILENCE_THRESHOLD_DB = -50.0  # dB for silencedetect
PADDING_MS = 100  # Padding in milliseconds
TRIM_THRESHOLD_MS = (
    250  # Only trim if we save more than this amount (including padding consideration)
)
console = Console()


def gather_mp3_files() -> list[Path]:
    """
    Gather all MP3 files from folders with '_0.85' in their names.
    Reused from delete_silent_files.py
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

    # No longer filtering out _trimmed.mp3 since we overwrite
    pr.info(f"found {len(files)} files. processing...")
    return files


def get_audio_info(filepath: Path) -> tuple[float, float, float] | None:
    """
    Detects audio start and end times using ffmpeg silencedetect.
    Returns (start, end, duration) or None if error.
    """
    try:
        # 1. Get total duration
        cmd_duration = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(filepath),
        ]
        duration_out = subprocess.check_output(cmd_duration).strip()
        if not duration_out:
            return None
        duration = float(duration_out)

        # 2. Detect silence
        # Use a small duration 'd' to detect even short silences
        cmd_silence = [
            "ffmpeg",
            "-i",
            str(filepath),
            "-af",
            f"silencedetect=noise={SILENCE_THRESHOLD_DB}dB:d=0.05",
            "-f",
            "null",
            "-",
        ]
        # ffmpeg outputs silencedetect info to stderr
        output = subprocess.run(cmd_silence, capture_output=True, text=True).stderr

        # Parse silence_start and silence_end
        starts = [float(x) for x in re.findall(r"silence_start: ([\d\.]+)", output)]
        ends = [float(x) for x in re.findall(r"silence_end: ([\d\.]+)", output)]

        audio_start = 0.0
        audio_end = duration

        # Check for silence at the beginning
        if starts and starts[0] < 0.1:
            if ends:
                audio_start = ends[0]
            else:
                return None  # Entire file is silent

        # Check for silence at the end
        if starts:
            last_start = starts[-1]
            if len(starts) > len(ends) or (ends and ends[-1] < last_start):
                audio_end = last_start
            elif ends and ends[-1] >= duration - 0.1:
                audio_end = last_start

        # Adjust for padding
        audio_start = max(0, audio_start - PADDING_MS / 1000)
        audio_end = min(duration, audio_end + PADDING_MS / 1000)

        if audio_end <= audio_start:
            return None

        return audio_start, audio_end, duration

    except Exception as e:
        pr.error(f"error analyzing {filepath.name}: {e}")
        return None


def trim_file(filepath: Path, start: float, end: float) -> bool:
    """
    Trims the file using ffmpeg and OVERWRITES the original.
    Uses stream copy for speed and lossless quality.
    """
    try:
        # Save to a temporary file first
        temp_path = filepath.with_name(f"{filepath.stem}_temp.mp3")

        cmd_trim = [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-ss",
            f"{start:.3f}",
            "-i",
            str(filepath),
            "-to",
            f"{end - start:.3f}",
            "-c",
            "copy",
            str(temp_path),
        ]

        subprocess.run(cmd_trim, check=True)

        # Move temp file to original file (overwrite)
        temp_path.replace(filepath)
        return True
    except Exception as e:
        pr.error(f"error trimming {filepath.name}: {e}")
        # Clean up temp file if it exists
        if "temp_path" in locals() and temp_path.exists():
            temp_path.unlink()
        return False


def process_one_file(filepath: Path) -> tuple[str, Path]:
    """
    Worker function for multiprocessing.
    """
    info = get_audio_info(filepath)
    if info:
        start, end, original_duration = info
        
        new_duration = end - start
        reduction = original_duration - new_duration
        
        # Check if reduction is significant enough
        if reduction < TRIM_THRESHOLD_MS / 1000:
            return "skipped_threshold", filepath
        
        if trim_file(filepath, start, end):
            return "trimmed", filepath
        return "error_trimming", filepath
            
    return "skipped_analysis", filepath

def save_results(file_list: list[Path], filename: str) -> None:
    """
    Save a list of files to a text file.
    """
    output_path = Path(__file__).parent / filename
    with open(output_path, "w") as f:
        for path in file_list:
            f.write(f"{path}\n")
    pr.info(f"results saved to: {output_path}")

def main():
    files = gather_mp3_files()
    if not files:
        pr.error("no files found.")
        return
    
    num_processes = multiprocessing.cpu_count()
    results = {"trimmed": 0, "skipped_threshold": 0, "skipped_analysis": 0, "error_trimming": 0}
    trimmed_list: list[Path] = []
    skipped_threshold_list: list[Path] = []

    with Progress() as progress:
        task = progress.add_task("[cyan]Trimming Audio...", total=len(files))
        
        with multiprocessing.Pool(processes=num_processes) as pool:
            for result, filepath in pool.imap_unordered(process_one_file, files):
                results[result] += 1
                if result == "trimmed":
                    trimmed_list.append(filepath)
                elif result == "skipped_threshold":
                    skipped_threshold_list.append(filepath)
                progress.update(task, advance=1)

    pr.info(f"Done. Summary:")
    pr.info(f"  Trimmed: {results['trimmed']}")
    pr.info(f"  Skipped (threshold < {TRIM_THRESHOLD_MS}ms): {results['skipped_threshold']}")
    pr.info(f"  Skipped (analysis/silent): {results['skipped_analysis']}")
    pr.info(f"  Errors: {results['error_trimming']}")

    if trimmed_list:
        save_results(trimmed_list, "trimmed_files.txt")
    
    if skipped_threshold_list:
        save_results(skipped_threshold_list, "skipped_threshold.txt")


if __name__ == "__main__":
    main()
