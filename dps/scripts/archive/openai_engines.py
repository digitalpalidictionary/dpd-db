# print list of available engines for your account in openai

import configparser
import openai


import json
from timeout_decorator import timeout, TimeoutError as TimeoutDecoratorError



def load_openai_config(filename="config.ini"):
    config = configparser.ConfigParser()
    config.read(filename)
    
    openai_config = {
        "openai": config["openai"]["key"],
    }
    return openai_config


# Setup OpenAI API key
openai_config = load_openai_config()
openai.api_key = openai_config["openai"]


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


# check_remaining_quota()

# check_availible_engines()

# test_request()


