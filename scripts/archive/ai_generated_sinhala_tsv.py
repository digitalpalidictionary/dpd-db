#!/usr/bin/env python3

"""making ai generated translation into Sinhala and saving to csv and xlsx"""

import pandas as pd
import csv
import re
from openai import OpenAI

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.tsv_read_write import write_tsv_list
from tools.meaning_construction import make_meaning_combo
from sqlalchemy import and_, or_
from dps.tools.ai_related import load_openai_config

from timeout_decorator import timeout, TimeoutError as TimeoutDecoratorError

api_key = load_openai_config()
client = OpenAI(api_key=api_key)

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

def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    conditions = [DpdHeadword.source_1.like(f"%{comment}%") for comment in commentary_list]
    combined_condition = or_(*conditions)

    db = db_session.query(DpdHeadword).filter(
            and_(
                DpdHeadword.meaning_1 != '',
                DpdHeadword.example_1 != '',
                ~combined_condition
            )
        ).order_by(DpdHeadword.ebt_count.desc()).limit(1000).all()

    data = []
    for counter, i in enumerate(db):
        meaning = make_meaning_combo(i)
        if i.meaning_1:
            test = "✔"
        else:
            test = "✘"

        if i.example_1:
            example = i.example_1
        else:
            example = ""

        sinhala = translate_with_openai(pth, i.lemma_1, i.grammar, meaning, example)
        
        row = [i.id, i.lemma_1, i.grammar, meaning, example, test, sinhala]
        data.append(row)

        print(f"{counter +  1}. {i.id} {i.lemma_1} {sinhala}")


    headers = ["id", "lemma_1", "grammar", "english", "example", "check", "sinhala"]
    
    
    # write tsv
    write_tsv_list("temp/dpd_sinhala_machine.tsv", headers, data)


@timeout(10, timeout_exception=TimeoutDecoratorError)  # Setting a 10-second timeout
def call_openai(messages):
    return client.chat.completions.create(
        model="gpt-4o-mini",
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


def translate_with_openai(pth, lemma_1, grammar, meaning, example):

    # Replace abbreviations in grammar
    grammar = replace_abbreviations(pth, grammar)
    
    # Generate the chat messages based on provided values
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that translates English text to Sinhalese considering the context."
        },
        {
            "role": "user",
            "content": f"""
                ---
                **Pali Term**: {lemma_1}

                **Grammar Details**: {grammar}

                **Pali sentence**: {example}

                **English Definition**: {meaning}

                Please provide a few distinct Sinhalese translations for the English definition, taking into account the Pali term and its grammatical context and Pali sentence. Separate each synonym with `;`. Avoid repeating the same word. Using Sinhalese script provide at least 3 Sinhalese synonyms in the answer and nothing else.
                ---
            """
        }
    ]

    suggestion = handle_openai_response(messages)

    return suggestion


if __name__ == "__main__":
    main()
