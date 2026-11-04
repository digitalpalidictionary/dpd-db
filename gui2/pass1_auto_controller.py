# -*- coding: utf-8 -*-
import asyncio
import threading
from json import JSONDecodeError, dump, dumps, loads

from gui2.books import (
    SuttaCentralSegment,
    SuttaCentralSource,
    sutta_central_books,
)
from gui2.pass1_context import (
    SYSTEM_PROMPT,
    AllowedValues,
    Sentence,
    book_name,
    build_new_prompt,
    choose_sentences,
    load_allowed_values,
    related_entry_dict,
    related_headwords,
)
from gui2.pass1_file_manager import Pass1FileManager
from gui2.spelling import SpellingMistakesFileManager
from gui2.toolkit import ToolKit
from gui2.variants import VariantReadingFileManager
from tools.ai_manager import AIResponse
from tools.clean_machine import clean_machine
from tools.cst_sc_text_sets import make_cst_text_list
from tools.epitaka_sentences import epitaka_word_dict, peu_entries
from tools.goldendict_tools import open_in_goldendict
from tools.pali_text_files import cst_texts
from tools.printer import printer as pr


class Pass1AutoController:
    def __init__(
        self,
        ui,  # Pass1AutoView
        toolkit: ToolKit,
    ) -> None:
        from gui2.pass1_auto_view import Pass1AutoView

        self.ui: Pass1AutoView = ui
        self.db = toolkit.db_manager
        self.ai_manager = toolkit.ai_manager
        self.file_manager = Pass1FileManager(toolkit.paths)
        self._lock = threading.Lock()

        self.gui2pth = toolkit.paths
        self.pass1_books: dict[str, SuttaCentralSource] = sutta_central_books
        self.pass1_books_list = [k for k in self.pass1_books]

        self.missing_words_dict: dict[str, list[SuttaCentralSegment]] = {}
        self.book: str
        self.cst_books: list[str]
        self.all_cst_words: list[str] = []
        self.word_in_text: str
        self.sentence_data: list[SuttaCentralSegment]
        self.chosen_sentences: list[Sentence] = []
        self.epitaka_dict: dict[str, list[Sentence]] = {}
        self.allowed: AllowedValues | None = None

        self.stop_flag = False
        # The loops are async, so their buttons stay clickable during a run.
        # A second run would share this controller's per-word state.
        self._run_in_progress = False

        self.prompt: str
        self.response: str | None = None  # Can be None if AI request fails
        self.ai_status_message: str = ""  # To store status from AIManager

        self.auto_processed_dict: dict[str, dict[str, str]] = {}
        self.auto_processed_keys: list[str] = []

        self.variant_readings = VariantReadingFileManager(
            toolkit.paths.variant_readings_path
        )
        self.spelling_mistakes = SpellingMistakesFileManager(
            toolkit.paths.spelling_mistakes_path
        )
        self.gd_toggle: bool = True
        self.current_book_processed: int = 0
        self.initial_auto_processed: int = 0
        self.total_missing: int = 0

    def get_auto_processed_dict(self, book: str) -> dict:
        with self._lock:
            current_book = getattr(self, "book", None)
            if not self.auto_processed_dict or current_book != book:
                self.auto_processed_dict = self.file_manager.read(book)
            return self.auto_processed_dict.copy()

    def remove_word(self, book: str, word: str):
        updated = self.file_manager.remove(book, word)
        if hasattr(self, "book") and self.book == book:
            self.auto_processed_dict = updated

    def add_word(self, book: str, word: str, data: dict):
        def update_func(current_data):
            current_data[word] = data
            return current_data

        updated = self.file_manager.update(book, update_func)
        if self.book == book:
            self.auto_processed_dict = updated

    def load_auto_processed(self):
        self.ui.update_message(f"Loading auto processed data for {self.book}")
        self.auto_processed_dict = self.get_auto_processed_dict(self.book)
        self.auto_processed_keys = list(self.auto_processed_dict.keys())
        self.ui.update_auto_processed_count("0 / 0")

    async def auto_process_book(self, book: str) -> None:
        if self._run_in_progress:
            self.ui.update_message("Already processing. Press Stop first.")
            return
        self._run_in_progress = True
        try:
            await self._auto_process_book(book)
        finally:
            self._run_in_progress = False

    async def _auto_process_book(self, book: str) -> None:
        self.ui.clear_all_fields()
        self.stop_flag = False
        self.missing_words_dict = {}  # Clear for new book

        # should run clean every time to update changes in db
        self.ui.update_message("Loading database...")
        await asyncio.to_thread(self.db.make_inflections_lists)

        self.book = book
        self.cst_books = sutta_central_books[book].cst_books
        self.load_auto_processed()
        self.current_book_processed = 0
        await asyncio.to_thread(self.find_missing_words_in_cst)
        await asyncio.to_thread(self.find_missing_words_in_sutta_central)
        await asyncio.to_thread(self.load_prompt_context)
        self.initial_auto_processed = len(self.auto_processed_dict)
        self.total_missing = len(self.missing_words_dict)
        self.unbroken_loop = True

        for self.word_in_text, self.sentence_data in self.missing_words_dict.items():
            # Stop can arrive during the setup or after a failed word.
            if self.stop_flag:
                self.ui.clear_all_fields()
                self.ui.update_message(f"Stopped processing {self.book}")
                self.unbroken_loop = False
                break
            self.ui.update_message(f"Processing {self.word_in_text}")

            self.compile_prompt()

            selected_model_str = self.ui.ai_model_dropdown.value
            provider_preference = None
            model_name = None
            if selected_model_str:
                parts = selected_model_str.split("|", 1)
                if len(parts) == 2:
                    provider_preference, model_name = parts

            # The AI call blocks for seconds. In a thread, the event loop can
            # redraw the screen and read the Stop click meanwhile.
            ai_resp = await asyncio.to_thread(
                self.send_prompt,
                provider_preference=provider_preference,
                model=model_name,
            )
            self.response = ai_resp.content
            self.ai_status_message = ai_resp.status_message
            self.ui.update_message(ai_resp.status_message)
            if self.response is None:
                self.unbroken_loop = False
                self.ui.update_message(f"Error processing {self.book}")
                break

            elif not self.update_auto_processed(provider_preference, model_name):
                self.ui.update_message(f"Error processing {self.book}")
                pass

            if self.stop_flag:
                self.ui.clear_all_fields()
                self.ui.update_message(f"Stopped processing {self.book}")
                self.unbroken_loop = False
                break

        if self.unbroken_loop:
            self.ui.update_message(f"Finished processing {self.book}")

    async def auto_process_text(self, text: str) -> None:
        if self._run_in_progress:
            self.ui.update_message("Already processing. Press Stop first.")
            return
        self._run_in_progress = True
        try:
            await self._auto_process_text(text)
        finally:
            self._run_in_progress = False

    async def _auto_process_text(self, text: str) -> None:
        self.ui.clear_all_fields()
        self.stop_flag = False
        self.missing_words_dict = {}

        self.ui.update_message("Loading database...")
        await asyncio.to_thread(self.db.make_inflections_lists)

        self.book = "text"
        self.load_auto_processed()
        self.current_book_processed = 0

        cleaned = clean_machine(text)
        words = cleaned.split()
        seen: set[str] = set()
        for word in words:
            if word and word not in seen:
                seen.add(word)
                if self.is_missing(word):
                    self.missing_words_dict[word] = []

        await asyncio.to_thread(self.load_prompt_context)
        self.initial_auto_processed = len(self.auto_processed_dict)
        self.total_missing = len(self.missing_words_dict)
        self.unbroken_loop = True

        self.ui.update_message(f"Found {self.total_missing} missing words in text")

        for self.word_in_text, self.sentence_data in self.missing_words_dict.items():
            # Stop can arrive during the setup or after a failed word.
            if self.stop_flag:
                self.ui.clear_all_fields()
                self.ui.update_message(f"Stopped processing {self.book}")
                self.unbroken_loop = False
                break
            self.ui.update_message(f"Processing {self.word_in_text}")

            self.compile_prompt()

            selected_model_str = self.ui.ai_model_dropdown.value
            provider_preference = None
            model_name = None
            if selected_model_str:
                parts = selected_model_str.split("|", 1)
                if len(parts) == 2:
                    provider_preference, model_name = parts

            # The AI call blocks for seconds. In a thread, the event loop can
            # redraw the screen and read the Stop click meanwhile.
            ai_resp = await asyncio.to_thread(
                self.send_prompt,
                provider_preference=provider_preference,
                model=model_name,
            )
            self.response = ai_resp.content
            self.ai_status_message = ai_resp.status_message
            self.ui.update_message(ai_resp.status_message)
            if self.response is None:
                self.ui.update_message(
                    f"Error processing {self.word_in_text}, skipping"
                )
                continue

            elif not self.update_auto_processed(provider_preference, model_name):
                self.ui.update_message(
                    f"Error processing {self.word_in_text}, skipping"
                )

            if self.stop_flag:
                self.ui.clear_all_fields()
                self.ui.update_message("Stopped processing text")
                self.unbroken_loop = False
                break

        if self.unbroken_loop:
            self.ui.update_message("Finished processing text")

    def is_missing(self, word: str):
        if (
            word not in self.db.all_inflections
            and word not in self.db.sandhi_ok_list
            and word not in self.auto_processed_keys
            and word not in self.variant_readings.variants_dict
            and word not in self.spelling_mistakes.spelling_mistakes_dict
        ):
            return True
        else:
            return False

    def find_missing_words_in_cst(self) -> None:
        """Find all the missing words in CST."""

        self.ui.update_message("Finding missing words in CST")

        # just run once, it doesn't change
        # if not self.all_cst_words: actually needs to change for every book
        self.all_cst_words = make_cst_text_list(self.cst_books, dedupe=True)

        for word in self.all_cst_words:
            if self.is_missing(word):
                self.missing_words_dict[word] = []

    def find_missing_words_in_sutta_central(self) -> None:
        """Find all the missing words in SC and add their sentences."""

        self.ui.update_message("Finding missing words in Sutta Central")

        for word, segments in self.pass1_books[self.book].word_dict.items():
            if self.is_missing(word):
                self.missing_words_dict[word] = segments

    def load_prompt_context(self) -> None:
        """Load what every prompt of this run shares: the real dictionary
        values and the ePitaka sentences of the book. Pasted text has no book."""

        self.ui.update_message("Loading prompt context")
        self.allowed = load_allowed_values(self.db.db_session)
        if self.book == "text":
            self.epitaka_dict = {}
            return
        cst_files = [
            name.removesuffix(".txt")
            for cst_book in self.cst_books
            for name in cst_texts.get(cst_book, [])
        ]
        self.epitaka_dict = epitaka_word_dict(cst_files)

    def compile_prompt(self):
        """Compile the prompt for the word and save it to the temp folder."""

        self.ui.update_message(f"compiling prompt for {self.word_in_text}")

        if self.allowed is None:
            self.allowed = load_allowed_values(self.db.db_session)

        self.chosen_sentences = choose_sentences(
            [(s.pali, s.english) for s in self.sentence_data],
            self.epitaka_dict.get(self.word_in_text, []),
        )
        # a fresh session, so the related entries see the latest edits
        self.db.new_db_session()
        related = [
            related_entry_dict(headword)
            for headword in related_headwords(self.db.db_session, self.word_in_text)
        ]
        self.prompt = build_new_prompt(
            self.word_in_text,
            book_name(self.book),
            self.chosen_sentences,
            related,
            peu_entries(self.word_in_text),
            self.allowed,
        )

        temp_dir = self.db.pth.temp_dir / "prompts" / "pass1"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file = temp_dir / f"{self.word_in_text}_prompt"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(self.prompt)

    def send_prompt(
        self, provider_preference: str | None = None, model: str | None = None
    ) -> AIResponse:  # Changed return type
        import time  # Add at top if not present

        max_retries: int = 3
        retry_delay: float = 1.0  # Seconds between retries
        last_error = "Unknown"

        for attempt in range(max_retries):
            self.ui.update_message(
                f"Sending prompt for {self.word_in_text} using {model or 'default model'}... (Attempt {attempt + 1}/{max_retries})"
            )

            try:
                ai_response = self.ai_manager.request(
                    prompt=self.prompt,
                    prompt_sys=SYSTEM_PROMPT,
                    provider_preference=provider_preference,
                    model=model,
                )

                if ai_response.content is not None:
                    return ai_response  # Success, no need for more retries

                last_error = ai_response.status_message
                # Log failure for this attempt
                pr.amber(
                    f"AI request failed for {self.word_in_text} on attempt {attempt + 1}: {ai_response.status_message}"
                )

                if attempt < max_retries - 1:  # Not the last attempt
                    time.sleep(retry_delay)

            except Exception as e:
                pr.red(
                    f"Exception during AI request for {self.word_in_text} on attempt {attempt + 1}: {e}"
                )
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)

        # All retries failed
        return AIResponse(
            content=None,
            status_message=f"Failed after {max_retries} attempts for {self.word_in_text}. Last error: {last_error}",
        )

    def update_auto_processed(self, provider: str | None, model: str | None) -> bool:
        if not isinstance(self.response, str):
            self.ui.update_message(
                f"Error for {self.word_in_text}: AI response content is not a string ({type(self.response)}). Original AI Status: {self.ai_status_message}"
            )
            return False

        # Attempt to clean and parse the JSON response
        try:
            cleaned_response = self.response.replace("```json\n", "").replace("```", "")

            # Try parsing the cleaned response
            parsed_json = loads(cleaned_response)

            # add ai details
            if provider:
                try:
                    comment = parsed_json["comment"]
                    parsed_json["comment"] = f"[{provider}: {model}] {comment}"
                except KeyError:
                    pr.red("ERROR adding ai model to comment")

            # save json to temp file
            temp_dir = self.db.pth.temp_dir / "prompts" / "pass1"
            temp_dir.mkdir(parents=True, exist_ok=True)
            tempfile = temp_dir / f"{self.word_in_text}_response"
            with open(tempfile, "w", encoding="utf-8") as f:
                dump(parsed_json, f, ensure_ascii=False, indent=4)

            # add examples and translations
            if len(self.chosen_sentences) > 0:
                first_pali, first_english = self.chosen_sentences[0]
                parsed_json["example_1"] = first_pali
                parsed_json["translation_1"] = first_english

            if len(self.chosen_sentences) > 1:
                second_pali, second_english = self.chosen_sentences[1]
                parsed_json["example_2"] = second_pali
                parsed_json["translation_2"] = second_english

            self.add_word(self.book, self.word_in_text, parsed_json)

            # update gui
            if self.gd_toggle:
                open_in_goldendict(self.word_in_text)
            self.ui.update_word_in_text(self.word_in_text)
            self.current_book_processed += 1
            self.ui.update_auto_processed_count(
                f"{self.initial_auto_processed + self.current_book_processed} / {self.initial_auto_processed + self.total_missing}"
            )
            self.ui.update_ai_results(
                dumps(
                    self.auto_processed_dict[self.word_in_text],
                    indent=4,
                    ensure_ascii=False,
                    separators=("", ":"),
                )
            )

        except JSONDecodeError as e:
            # Handle the case where the response is not valid JSON
            error_message = f"Error processing '{self.word_in_text}': Failed to decode API response. Details: {e}. Original AI Status: {self.ai_status_message}"
            self.ui.update_message(error_message)
            return False

        except Exception as e:
            # Catch any other unexpected errors during processing
            error_message = f"Unexpected error processing '{self.word_in_text}': {e}. Original AI Status: {self.ai_status_message}"
            self.ui.update_message(error_message)
            return False

        return True
