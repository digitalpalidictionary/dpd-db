"""3.2: time each ToolKit manager's construction individually, replicating
gui2/toolkit.py's __init__ body with per-step timing. A real flet.Page can't
be constructed standalone (needs a live Connection+session_id+event loop),
so this uses `page=None` — none of the manager __init__ methods below call
methods on `page`, they only store the reference, so this is safe.
"""

import time

from bench_common import force_throwaway_db_globally, write_result
from gui2.toolkit import ToolKit

# Must run before any manager __init__ actually opens a db session (not
# before import — Python resolves module-global names lazily at call time).
force_throwaway_db_globally()


def main() -> None:
    from db_tests.db_tests_manager import DbTestManager
    from gui2.additions_manager import AdditionsManager
    from gui2.ai_search import AiSearchPopup
    from gui2.appbar_updater import AppBarUpdater
    from gui2.corrections_manager import CorrectionsManager
    from gui2.daily_log import DailyLog
    from gui2.database_manager import DatabaseManager
    from gui2.filter_presets_manager import FilterPresetsManager
    from gui2.history import HistoryManager
    from gui2.pass2_exceptions import Pass2ExceptionsFileManager
    from gui2.pass2_pre_new_word_manager import Pass2NewWordManager
    from gui2.paths import Gui2Paths
    from gui2.sandhi_files_manager import SandhiFileManager
    from gui2.see import SeeFileManager
    from gui2.spelling import SpellingMistakesFileManager
    from gui2.test_manager import GuiTestManager
    from gui2.user import UsernameManager
    from gui2.variants import VariantReadingFileManager
    from gui2.wordfinder_popup import WordFinderPopup
    from tools.ai_manager import AIManager
    from tools.bold_definitions_search import BoldDefinitionsSearchManager
    from tools.configger import config_read
    from tools.paths import ProjectPaths
    from tools.proofreader import ProofreaderManager
    from tools.speech_marks import SpeechMarkManager
    from tools.wordfinder_manager import WordFinderManager

    timings: dict[str, float] = {}

    def step(label, fn):
        start = time.perf_counter()
        result = fn()
        timings[label] = round((time.perf_counter() - start) * 1000, 2)
        return result

    tk = object.__new__(ToolKit)
    tk.page = None  # type: ignore[assignment]

    tk.project_paths = step("project_paths (ProjectPaths)", lambda: ProjectPaths())
    username = config_read("gui2", "username") or "1"
    tk.paths = step("paths (Gui2Paths.for_user)", lambda: Gui2Paths.for_user(username))
    tk.db_test_manager = step(
        "db_test_manager (DbTestManager)", lambda: DbTestManager()
    )
    tk.test_manager = step("test_manager (GuiTestManager)", lambda: GuiTestManager(tk))
    tk.speech_marks_manager = step(
        "speech_marks_manager (SpeechMarkManager)", lambda: SpeechMarkManager()
    )
    tk.history_manager = step(
        "history_manager (HistoryManager)", lambda: HistoryManager(tk)
    )
    tk.ai_manager = step("ai_manager (AIManager, 6 provider SDKs)", lambda: AIManager())
    tk.db_manager = step("db_manager (DatabaseManager)", lambda: DatabaseManager())
    tk.pass2_exceptions_manager = step(
        "pass2_exceptions_manager", lambda: Pass2ExceptionsFileManager(tk)
    )
    tk.pass2_new_word_manager = step(
        "pass2_new_word_manager", lambda: Pass2NewWordManager(tk)
    )
    tk.username_manager = step(
        "username_manager (UsernameManager)", lambda: UsernameManager(tk.page)
    )
    tk.corrections_manager = step(
        "corrections_manager (CorrectionsManager)", lambda: CorrectionsManager(tk)
    )
    tk.filter_presets_manager = step(
        "filter_presets_manager (FilterPresetsManager)",
        lambda: FilterPresetsManager(tk),
    )
    tk.additions_manager = step(
        "additions_manager (AdditionsManager)", lambda: AdditionsManager(tk)
    )
    tk.proofreader_manager = step(
        "proofreader_manager (ProofreaderManager)",
        lambda: ProofreaderManager(tk.project_paths.proofreader_tsv_path),
    )
    tk.appbar_updater = step(
        "appbar_updater (AppBarUpdater)", lambda: AppBarUpdater(tk.page)
    )
    tk.daily_log = step("daily_log (DailyLog)", lambda: DailyLog(tk))
    tk.ai_search_popup = step(
        "ai_search_popup (AiSearchPopup)", lambda: AiSearchPopup(tk)
    )
    tk.wordfinder_manager = step(
        "wordfinder_manager (WordFinderManager, 74MB JSON load)",
        lambda: WordFinderManager(),
    )
    tk.wordfinder_popup = step(
        "wordfinder_popup (WordFinderPopup)", lambda: WordFinderPopup(tk)
    )
    tk.bold_definitions_search_manager = step(
        "bold_definitions_search_manager (BoldDefinitionsSearchManager, own DB session)",
        lambda: BoldDefinitionsSearchManager(),
    )
    tk.see_manager = step("see_manager (SeeFileManager)", lambda: SeeFileManager())
    tk.variants = step(
        "variants (VariantReadingFileManager)", lambda: VariantReadingFileManager()
    )
    tk.spelling_mistakes = step(
        "spelling_mistakes (SpellingMistakesFileManager)",
        lambda: SpellingMistakesFileManager(),
    )
    tk.sandhi_files_manager = step(
        "sandhi_files_manager (SandhiFileManager)", lambda: SandhiFileManager(tk)
    )
    step(
        "pre_initialize_gui_data (5 aggregate queries)",
        tk.db_manager.pre_initialize_gui_data,
    )

    total_ms = round(sum(timings.values()), 2)
    ordered = dict(sorted(timings.items(), key=lambda kv: -kv[1]))

    print(f"\nTotal ToolKit-equivalent construction: {total_ms:.1f} ms\n")
    print(f"{'step':<65} {'ms':>10}")
    for label, ms in ordered.items():
        print(f"{label:<65} {ms:>10.2f}")

    write_result(
        "3.2_startup",
        {"total_ms": total_ms, "steps_ms_desc": ordered},
    )


if __name__ == "__main__":
    main()
