import sys
from tools.printer import printer as pr

# Shared state for progress tracking
state = {
    "total_words": 0,
    "processed_count": 0,
    "remaining_words": [],
}

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    pr.red("\n\nInterrupted!")
    pr.info(f"Done: {state['processed_count']}")
    pr.info(f"Left: {len(state['remaining_words'])}")
    sys.exit(0)
