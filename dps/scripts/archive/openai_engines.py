# print list of available engines for your account in openai

import configparser
import openai

from googletrans import Translator


import json
from timeout_decorator import timeout, TimeoutError as TimeoutDecoratorError



def load_openia_config(filename="config.ini"):
    config = configparser.ConfigParser()
    config.read(filename)
    
    openia_config = {
        "openia": config["openia"]["key"],
    }
    return openia_config


# Setup OpenAI API key
openia_config = load_openia_config()
openai.api_key = openia_config["openia"]


def check_availible_engines():
    # Fetch list of available engines
    engines = openai.Engine.list()

    # Print each engine's ID
    for engine in engines["data"]:
        print(engine["id"])


@timeout(10, timeout_exception=TimeoutDecoratorError)  # Setting a 10-second timeout
def test_request():
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that translates English text to Russian considering the context."

        },
        {
            "role": "user",
            "content": """
                **Pali Term**: dissati
                **Grammar Details**: present tense, passive of   √dis, intransitive
                **Pali sentence**: seyyathā'pi, bhikkhave, palagaṇḍassa vā palagaṇḍ'antevāsissa vā vāsijaṭe <b>dissent</b>'eva aṅgulipadāni dissati aṅguṭṭhapadaṃ.
                **English Definition**: appears; lit. is seen
                Please provide a few distinct Russian translations for the English definition, considering the Pali term and its grammatical context and Pali sentence. Separate each synonym with `;`. Avoid repeating the same word.

            """
        }
    ]

    try:

        response = openai.ChatCompletion.create(
            messages=messages,  # Pass the list of dictionaries directly
            model="gpt-4-1106-preview",
            temperature=0,
        )

        print(response.choices[0].message.content)

    except TimeoutError:
        print("The request timed out.")

# Please provide a few distinct Russian translations for the English definition, taking into account the Pali term and its grammatical context and Pali sentence. Separate each synonym with `;`. Avoid repeating the same word, even between main words and literal meanings. Provide a lot of Russian synonyms in the answer and nothing else.


@timeout(10, timeout_exception=TimeoutDecoratorError)  # Setting a  10-second timeout
def translate_to_russian_googletrans():
    meaning = "factor; component; element; quality; aspect; lit. part"

    try:
        translator = Translator()
        translation = translator.translate(meaning, dest='ru')
        dps_ru_online_suggestion = translation.text.lower()

        # Add spaces after semicolons and lit. for better readability
        dps_ru_online_suggestion = dps_ru_online_suggestion.replace(";", "; ")
        dps_ru_online_suggestion = dps_ru_online_suggestion.replace("|", "| ")

        print(dps_ru_online_suggestion)

    except TimeoutDecoratorError:
        # Handle any exceptions that occur
        error_string = "Timed out"
        print(error_string)

    except Exception as e:
        # Handle any other exceptions that occur
        error_string = f"Error: {e} "
        print(error_string)


# check_remaining_quota()

# check_availible_engines()

# test_request()

# translate_to_russian_googletrans()


