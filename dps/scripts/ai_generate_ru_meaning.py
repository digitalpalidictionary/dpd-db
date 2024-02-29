#!/usr/bin/env python3

"""making ai generated translation into Russian and saving to db"""

import openai
import csv
import re
from rich.prompt import Prompt

from db.get_db_session import get_db_session
from db.models import DpdHeadwords, DpdRoots, Russian
from tools.paths import ProjectPaths
from tools.meaning_construction import make_meaning

from sqlalchemy import and_, or_, null
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from timeout_decorator import timeout, TimeoutError as TimeoutDecoratorError

from tools.configger import config_test_option, config_read, config_update

pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)


def ru_meaning_generating():

    commentary_list = [
            "VINa", "VINt", "DNa", "MNa", "SNa", "SNt", "ANa", 
            "KHPa", "KPa", "DHPa", "UDa", "ITIa", "SNPa", "VVa", "VVt",
            "PVa", "THa", "THIa", "APAa", "APIa", "BVa", "CPa", "JAa",
            "NIDD1", "NIDD2", "PMa", "NPa", "NPt", "PTP",
            "DSa", "PPa", "VIBHa", "VIBHt", "ADHa", "ADHt",
            "KVa", "VMVt", "VSa", "PYt", "SDt", "SPV", "VAt", "VBt",
            "VISM", "VISMa",
            "PRS", "SDM", "SPM",
            "bālāvatāra", "kaccāyana", "saddanīti", "padarūpasiddhi",
            "buddhavandana", "Thai", "Sri Lanka", "Trad", "PAT PK", "MJG"
            ]

    conditions = [DpdHeadwords.source_1.like(f"%{comment}%") for comment in commentary_list]
    combined_condition = or_(*conditions)

    #! for filling those which does not have Russian table and fill the conditions

    # db = db_session.query(DpdHeadwords).outerjoin(
    # Russian, DpdHeadwords.id == Russian.id
    #     ).filter(
    #         and_(
    #             DpdHeadwords.meaning_1 != '',
    #             # DpdHeadwords.example_1 != '',
    #             # ~combined_condition,
    #             or_(
    #                 Russian.ru_meaning.is_(None),
    #                 Russian.ru_meaning_raw.is_(None),
    #                 Russian.id.is_(null())
    #             )

    #         )
    #     ).order_by(DpdHeadwords.ebt_count.desc()).limit(10000).all()

    #! for filling empty rows in Russian table

    db = db_session.query(DpdHeadwords).outerjoin(
        Russian, DpdHeadwords.id == Russian.id
            ).filter(
                    Russian.id != '',
                    Russian.ru_meaning == '',
                    Russian.ru_meaning_raw == '',
                    ).order_by(DpdHeadwords.ebt_count.desc()).limit(3000).all()

    row_count =  0

    # Print the db
    print("Details of filtered words")
    for word in db:
        print(f"{word.id}, {word.lemma_1}, {word.ebt_count}")
        row_count +=  1

    print(f"Total rows that fit the filter criteria: {row_count}")


    for counter, i in enumerate(db):
        meaning = make_meaning(i)

        if i.example_1:
            example = i.example_1
        else:
            example = ""

        ru_meaning_raw = translate_meaning(pth, i.lemma_1, i.grammar, meaning, example)

        if ru_meaning_raw:

            # Check if a Russian row with the same id exists
            existing_russian = db_session.query(Russian).filter(Russian.id == i.id).first()
            if not existing_russian:
                # If not, create a new Russian row
                new_russian = Russian(id=i.id, ru_meaning_raw=ru_meaning_raw)
                db_session.add(new_russian)
            else:
                # If it exists, use the existing row
                existing_russian.ru_meaning_raw = ru_meaning_raw

            # Commit changes after all updates/additions
            db_session.commit()

            print(f"{counter +  1}. {i.id} {i.lemma_1} {ru_meaning_raw}")


def roots_meaning_generating(lang):

    #! for filling those which does not have Russian root meaing

    # Define a subquery that counts the related DpdHeadwords entries
    subquery = db_session.query(
            DpdHeadwords.root_key,
            func.count(DpdHeadwords.id).label('headword_count')
        ).group_by(
            DpdHeadwords.root_key
        ).subquery()

    if lang == "pali":

        roots = db_session.query(DpdRoots).join(
                subquery, DpdRoots.root == subquery.c.root_key
            ).filter(
                and_(
                    DpdRoots.root_ru_meaning == '',
                )
            ).order_by(
                subquery.c.headword_count.desc()
            ).limit(1000).all()

    elif lang == "sk":

        roots = db_session.query(DpdRoots).join(
                subquery, DpdRoots.root == subquery.c.root_key
            ).filter(
                and_(
                    DpdRoots.sanskrit_root_ru_meaning == '',
                    DpdRoots.sanskrit_root_ru_meaning != '-',
                )
            ).order_by(
                subquery.c.headword_count.desc()
            ).limit(1000).all()

    else:
        print("wrong language")

    # row_count =  0

    # # Print the db
    # print("Details of filtered roots")
    # for root in roots:
    #     print(f"{root.root_clean}, {root.root_count}")
    #     row_count +=  1

    # print(f"Total rows that fit the filter criteria: {row_count}")


    for counter, root in enumerate(roots):

        if lang == "pali":

            ru_root_meaning = translate_pali_roots(root.root_clean, root.root_meaning, root.root_example)

            if ru_root_meaning:

                root.root_ru_meaning = ru_root_meaning

                # Commit changes after all updates/additions
                db_session.commit()

                print(f"{counter +  1}. {root.root_clean}, {root.root_count} {ru_root_meaning}")

        if lang == "sk":

            ru_root_meaning = translate_sk_roots(root.root_clean, root.sanskrit_root_meaning)

            if ru_root_meaning:

                root.sanskrit_root_ru_meaning = ru_root_meaning

                # Commit changes after all updates/additions
                db_session.commit()

                if lang == "pali":
                    print(f"{counter +  1}. {root.root_clean}, {root.root_meaning} {ru_root_meaning}")
                if lang == "sk":
                    print(f"{counter +  1}. {root.sanskrit_root}, {root.sanskrit_root_meaning} {ru_root_meaning}")


def ru_notes_generating():

    #! for filling those which has Russian table and does not have ru_notes

    db = db_session.query(DpdHeadwords).outerjoin(
    Russian, DpdHeadwords.id == Russian.id
        ).options(
            joinedload(DpdHeadwords.ru)
        ).filter(
            and_(
                DpdHeadwords.meaning_1 != '',
                # DpdHeadwords.example_1 != '',
                DpdHeadwords.notes != '',
                Russian.ru_notes == ''
            ),
            or_(
                    Russian.ru_meaning != '',
                    Russian.ru_meaning_raw != '',
                )
        ).order_by(DpdHeadwords.ebt_count.desc()).limit(1000).all()

    row_count =  0

    # Print the db
    print("Details of filtered words")
    for word in db:
        print(f"{word.id}, {word.lemma_1}, {word.ebt_count}")
        row_count +=  1

    print(f"Total rows that fit the filter criteria: {row_count}")


    for counter, i in enumerate(db):

        ru_meaning_raw = translate_notes(pth, i.lemma_1, i.grammar, i.notes)

        if ru_meaning_raw:
            # Update the ru_notes attribute of the existing Russian instance
            i.ru.ru_notes = ru_meaning_raw

            # Commit changes after all updates/additions
            db_session.commit()

            print(f"{counter +  1}. {i.id} {i.lemma_1} {ru_meaning_raw}")



def load_openia_config():
    """Add a OpenAI key if one doesn't exist, or return the key if it does."""

    if not config_test_option("openia", "key"):
        openia_config = Prompt.ask("[yellow]Enter your openai key (or ENTER for None)")
        config_update("openia", "key", openia_config)
    else:
        openia_config = config_read("openia", "key")
    return openia_config


# Setup OpenAI API key
openai.api_key = load_openia_config()

@timeout(10, timeout_exception=TimeoutDecoratorError)  # Setting a 10-second timeout
def call_openai(messages):
    return openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0125",
        messages=messages
    )


def handle_openai_response(messages):
    error_string = ""

    try:
        # Request translation from OpenAI's GPT chat model
        response = call_openai(messages)
        suggestion = response.choices[0].message['content'].strip() # type: ignore

        return suggestion

    # Handle any exceptions that occur
    except TimeoutDecoratorError:
        error_string = "Timed out"
        print(error_string)

    except Exception as e:
        error_string = f"Error: {e} "
        print(error_string)


def replace_abbreviations(pth, grammar_string):
    # Clean the grammar string: Take portion before the first ','
    # cleaned_grammar_string = grammar_string.split(',')[0].strip()

    replacements = {}

    # Read abbreviations and their full forms into a dictionary
    with open(pth.abbreviations_tsv_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter='\t')
        next(reader)  # skip header
        for row in reader:
            abbrev, full_form = row[0], row[1]  # select only the first two columns
            replacements[abbrev] = full_form

    # Remove content within brackets
    grammar_string = re.sub(r'\(.*?\)', '', grammar_string)

    # Use regex to split the string in a way that separates punctuations
    abbreviations = re.findall(r"[\w']+|[.,!?;]", grammar_string)

    # Replace abbreviations in the list
    for idx, abbrev in enumerate(abbreviations):
        if abbrev in replacements:
            abbreviations[idx] = replacements[abbrev]

    # Join the list back into a string
    replaced_string = ' '.join(abbreviations)

    return replaced_string


def translate_meaning(pth, lemma_1, grammar, meaning, example):

    # Replace abbreviations in grammar
    grammar = replace_abbreviations(pth, grammar)
    
    # Generate the chat messages based on provided values
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that translates English text to Russian considering the context."
        },
        {
            "role": "user",
            "content": f"""
                **Pali Term**: {lemma_1}
                **Grammar Details**: {grammar}
                **Pali sentence**: {example}
                **English Definition**: {meaning}
                Please provide distinct Russian translation for the English definition, considering the Pali term and its grammatical context and Pali sentence. In the answer give only Russian translation in Cyrillic script in one line and nothing else. 
            """
        }
    ]

    suggestion = handle_openai_response(messages)

    return suggestion


def translate_notes(pth, lemma_1, grammar, notes):

    # Replace abbreviations in grammar
    grammar = replace_abbreviations(pth, grammar)
    
    # Generate the chat messages based on provided values
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that translates English text to Russian considering the context."        
        },
        {
            "role": "user",
            "content": f"""
                **Pali Term**: {lemma_1}
                **Grammar Details**: {grammar}
                **English Notes**: {notes}
                Please provide Russian translation for the English notes, considering the Pali term and its grammatical context. In the answer give only Russian translation in one line and nothing else.
            """
        }
    ]

    suggestion = handle_openai_response(messages)

    # Ensure suggestion is treated as a string
    suggestion_str = str(suggestion) if suggestion is not None else ""

    if suggestion_str:

        suggestion_with_prefix = "[пер. ИИ] " + suggestion_str

        return suggestion_with_prefix

    else:
        return suggestion


def translate_pali_roots(root, root_meaning, root_example):

    # Generate the chat messages based on provided values
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that translates English text to Russian considering the context."
        },
        {
            "role": "user",
            "content": f"""
                **Pali Root**: {root}
                **Pali word example**: {root_example}
                **English Definition**: {root_meaning}
                Please provide 2 distinct Russian translations for the English definition, considering the Pali root and its Pali word example. Ensure that the translations are in the infinitive forms of the verb, avoiding repetition. In the answer give only 2 Russian words weparated by `,` in one line and nothing else. 
            """
        }
    ]

    suggestion = handle_openai_response(messages)

    return suggestion


def translate_sk_roots(sk_root, sk_root_meaning):

    # Generate the chat messages based on provided values
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that translates English text to Russian considering the context."
        },
        {
            "role": "user",
            "content": f"""
                **Sanskrit Root**: {sk_root}
                **English Definition**: {sk_root_meaning}
                Please provide Russian translation for the English definition, considering the Sanskrit root. Ensure that the translation is in the infinitive form of the verb, avoiding repetition. In the ansywer give only Russian words in one line and nothing else.
            """
        }
    ]

    suggestion = handle_openai_response(messages)

    return suggestion


if __name__ == "__main__":
    ru_meaning_generating()

    # roots_meaning_generating("pali")

    # ru_notes_generating()

