#!/usr/bin/env python3

"""making ai generated translation into Russian and saving to db or saving promts in json format"""

import os
import json
import glob

from typing import List, Dict

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Russian

from tools.paths import ProjectPaths
from tools.meaning_construction import make_meaning_combo
from tools.date_and_time import year_month_day_hour_minute_dash

from dps.tools.ai_related import load_translaton_examples
from dps.tools.ai_related import handle_openai_response
from dps.tools.ai_related import replace_abbreviations
from dps.tools.ai_related import get_openai_client
from dps.tools.ai_related import generate_messages_for_meaning
from dps.tools.ai_related import generate_messages_for_notes

from dps.tools.paths_dps import DPSPaths    

from sqlalchemy import and_, or_, null
from sqlalchemy import func
from sqlalchemy.orm import joinedload


pth = ProjectPaths()
dpspth = DPSPaths()
db_session = get_db_session(pth.dpd_db_path)
date = year_month_day_hour_minute_dash()

# model="gpt-4o"
# model="gpt-4o-mini"
model="gpt-4o-2024-08-06"
hight_model="gpt-4o-2024-08-06"


def remove_irrelevant(limit: int):

    # Query the database to fetch words that meet the conditions
    db = db_session.query(DpdHeadword).join(Russian).filter(
        and_(
            Russian.ru_meaning_raw != '',
            Russian.ru_meaning == '',
            DpdHeadword.meaning_1 == ''
        )
    ).all()

    total_row_count = len(db)

    db = db[:limit]

    print(f"Rows filtered for the proccess: {len(db)} / {total_row_count}")

    # Remove the filtered rows from the Russian table
    for word in db:
        db_session.delete(word.ru)

    # Commit the changes
    db_session.commit()



def filter_words_for_translation(mode, limit: int) -> List[DpdHeadword]:
    """Filter words that need translation."""

    # commentary_list = [
    #         "VINa", "VINt", "DNa", "MNa", "SNa", "SNt", "ANa", 
    #         "KHPa", "KPa", "DHPa", "UDa", "ITIa", "SNPa", "VVa", "VVt",
    #         "PVa", "THa", "THIa", "APAa", "APIa", "BVa", "CPa", "JAa",
    #         "NIDD1", "NIDD2", "PMa", "NPa", "NPt", "PTP",
    #         "DSa", "PPa", "VIBHa", "VIBHt", "ADHa", "ADHt",
    #         "KVa", "VMVt", "VSa", "PYt", "SDt", "SPV", "VAt", "VBt",
    #         "VISM", "VISMa",
    #         "PRS", "SDM", "SPM",
    #         "bālāvatāra", "kaccāyana", "saddanīti", "padarūpasiddhi",
    #         "buddhavandana", "Thai", "Sri Lanka", "Trad", "PAT PK", "MJG"
    #         ]

    # conditions = [DpdHeadword.source_1.like(f"%{comment}%") for comment in commentary_list]
    # combined_condition = or_(*conditions)

    if mode == "meaning":
        #! for filling those which does not have Russian table and fill the conditions

        db = db_session.query(DpdHeadword).outerjoin(
        Russian, DpdHeadword.id == Russian.id
            ).filter(
                and_(
                    DpdHeadword.meaning_1 != '',
                    # DpdHeadword.example_1 != '',
                    # ~combined_condition,
                    or_(
                        Russian.ru_meaning.is_(None),
                        Russian.ru_meaning_raw.is_(None),
                        Russian.id.is_(null())
                    )

                )
            ).order_by(DpdHeadword.ebt_count.desc()).all()

        #! for filling empty rows in Russian table

        # db = db_session.query(DpdHeadword).outerjoin(
        #     Russian, DpdHeadword.id == Russian.id
        #         ).filter(
        #                 Russian.id != '',
        #                 Russian.ru_meaning == '',
        #                 Russian.ru_meaning_raw == '',
        #                 ).order_by(DpdHeadword.ebt_count.desc()).all()

        #! for filling those which have lower model of gpt:

        # # Call the functions to read IDs from the TSV and json files to exclude
        # exclude_ids_tsv: set[str] = read_exclude_ids_from_tsv(f"{dpspth.ai_translated_dir}/{hight_model}.tsv")
        # exclude_ids_json: set[str] = read_exclude_ids_from_json(dpspth.ai_from_batch_api_dir)
        # exclude_ids = exclude_ids_tsv | exclude_ids_json
        # print(f"excluded words {len(exclude_ids)}")


        # # Add the conditions to the query
        # db = db_session.query(DpdHeadword).outerjoin(
        #     Russian, DpdHeadword.id == Russian.id
        #     ).filter(
        #         and_(
        #             DpdHeadword.meaning_1 != '',
        #             # DpdHeadword.example_1 != '',
        #             Russian.ru_meaning_raw != '',
        #             # func.length(Russian.ru_meaning_raw) > 20,
        #             Russian.ru_meaning == '',
        #             ~DpdHeadword.id.in_(exclude_ids)
        #         )
        #     ).order_by(DpdHeadword.ebt_count.desc()).all()

        total_row_count = len(db)
        db = db[:limit]

    if mode == "note":

        #! for filling notes those which has Russian table and does not have ru_notes
        db = db_session.query(DpdHeadword).outerjoin(
        Russian, DpdHeadword.id == Russian.id
            ).options(
                joinedload(DpdHeadword.ru)
            ).filter(
                and_(
                    # DpdHeadword.meaning_1 != '',
                    # DpdHeadword.example_1 != '',
                    DpdHeadword.notes != '',
                    Russian.ru_notes == ''
                ),
                or_(
                        Russian.ru_meaning != '',
                        Russian.ru_meaning_raw != '',
                    )
            ).order_by(DpdHeadword.ebt_count.desc()).all()

        total_row_count = len(db)
        db = db[:limit]


    print(f"Rows filtered for the proccess: {len(db)} / {total_row_count}")

    return db


def create_translation_prompt(word: DpdHeadword, mode) -> Dict:
    """Create a translation prompt for a given word."""
    pos_example_map = load_translaton_examples(dpspth)
    meaning = make_meaning_combo(word)
    example = word.example_1 if word.example_1 else ""
    translation_example = pos_example_map.get(word.pos, "")
    grammar = replace_abbreviations(word.grammar)

    if mode == "meaning":
        messages = generate_messages_for_meaning(word.lemma_1, grammar, meaning, example, translation_example)
    if mode == "note":
        messages = generate_messages_for_notes(word.lemma_1, grammar, word.notes)

    return {
        "custom_id": f"request-{word.id}",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": model,
            "messages": messages
        }
    }


def translate(lemma_1, grammar, pos, meaning, sentence, notes, mode):
    pos_example_map = load_translaton_examples(dpspth)
    translation_example = pos_example_map.get(pos, "")
    grammar = replace_abbreviations(grammar)

    if mode == "meaning":
        messages = generate_messages_for_meaning(lemma_1, grammar, meaning, sentence, translation_example)

    elif mode == "note":
        messages = generate_messages_for_notes(lemma_1, grammar, notes)
    else:
        raise ValueError(f"Invalid mode: {mode}")

    # Lazy initialization of OpenAI client
    client = get_openai_client()
    suggestion, error_string = handle_openai_response(client, messages, model)
    if error_string:
        print(error_string)
    elif suggestion:
        # Ensure suggestion is treated as a string
        suggestion_str = suggestion.content if suggestion is not None else ""

        if mode == "meaning":
            return suggestion_str

        elif mode == "note":
            return f"[пер. ИИ] {suggestion_str}"
        else:
            raise ValueError(f"Invalid mode: {mode}")


def save_prompts_to_json(prompts: List[Dict], filename):
    """Save prompts to a JSON file for Batch API use."""
    with open(filename, 'w', encoding='utf-8') as f:
        for prompt in prompts:
            json.dump(prompt, f, ensure_ascii=False)
            f.write('\n')  # Add newline between JSON objects
    print(f"prompts saved to {filename}")


def make_json(mode, limit: int):
    words = filter_words_for_translation(mode, limit)
    prompts = [create_translation_prompt(word, mode) for word in words]

    file_name = os.path.join(dpspth.ai_for_batch_api_dir, f"{mode}-{date}.jsonl")
    save_prompts_to_json(prompts, file_name)


def translation_generate(mode, limit: int):
    words = filter_words_for_translation(mode, limit)
    for word in words:
        
        ru_meaning_raw = translate(
            word.lemma_1, 
            word.grammar, 
            word.pos, 
            make_meaning_combo(word), 
            word.example_1 or "",
            word.notes or "",
            mode
        )
        if ru_meaning_raw:
            if mode == "meaning":
                existing_russian = db_session.query(Russian).filter(Russian.id == word.id).first()
                if not existing_russian:
                    new_russian = Russian(id=word.id, ru_meaning_raw=ru_meaning_raw)
                    db_session.add(new_russian)
                else:
                    existing_russian.ru_meaning_raw = ru_meaning_raw

                db_session.commit()

                print(f"{word.id}, {word.ebt_count} {word.lemma_1} {ru_meaning_raw}")

                with open(f'{dpspth.ai_translated_dir}/{model}.tsv', 'a', encoding='utf-8') as file:
                    file.write(f"{word.id}\t{word.lemma_1}\t{ru_meaning_raw}\n")
            
            if mode == "note":
                word.ru.ru_notes = ru_meaning_raw

                db_session.commit()

                print(f"{word.id}, {word.ebt_count} {word.lemma_1} {ru_meaning_raw}")


def read_exclude_ids_from_tsv(file_path) -> set[str]:
    exclude_ids = set()
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            id = line.split('\t')[0]
            exclude_ids.add(id)
    return exclude_ids


def read_exclude_ids_from_json(dir_path, mode: str = "meaning") -> set[str]:
    exclude_ids = set()
    # Find all JSON files in the directory
    json_files = glob.glob(f"{dir_path}/*.jsonl")

    # Read each JSON file and extract the IDs
    for file_path in json_files:
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                try:
                    # Decode each JSON object
                    data = json.loads(line)
                    # Extract the ID
                    id = data.get('id', '')
                    exclude_ids.add(id)
                except json.JSONDecodeError as e:
                    print(f"Error decoding line: {e}, Line: {line}")
    
    return exclude_ids


if __name__ == "__main__":

    print("Translationg with the help of AI")

    limit: int = 1

    # remove_irrelevant(limit)

    translation_generate("meaning", limit)

    # translation_generate("note", limit)

    # make_json("meaning", limit)

    # make_json("note", limit)

