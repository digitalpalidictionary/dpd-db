# print list of available engines for your account in openai

import configparser
import openai


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


def check_remaining_quota():

    # Make a request to the OpenAI API to get the rate limit information
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Translate the following English text to French: 'Hello, how are you?'"}
        ]
    )

    # Extract rate limit information from the response headers
    rate_limit_limit = response.http_response.headers['X-RateLimit-Limit']
    rate_limit_remaining = response.http_response.headers['X-RateLimit-Remaining']
    rate_limit_reset = response.http_response.headers['X-RateLimit-Reset']

    # Convert the reset time from epoch seconds to a human-readable format
    from datetime import datetime
    reset_time = datetime.utcfromtimestamp(int(rate_limit_reset)).strftime('%Y-%m-%d %H:%M:%S')

    print(f"Limit for today: {rate_limit_limit}")
    print(f"Requests left for today: {rate_limit_remaining}")
    print(f"Reset time (UTC): {reset_time}")


def test_request():
    query = """
    
    Use the below context please provide a few distinct Russian translations for the English definition, taking into account the Pali term and its grammatical context and Pali sentence. Separate each synonym with `;`. Avoid repeating the same word, even between main words and literal meanings. Provide a lot of Russian synonyms in the answer and nothing else."

Grammatical context:
\"\"\"
                **Pali Term**: eṇijaṅgha

                **Grammar Details**: adjective, compound

                **Pali sentence**: eṇijaṅgho kho pana so bhavaṃ gotamo, idam'pi tassa bhoto gotamassa mahāpurisassa mahāpurisalakkhaṇaṃ bhavati.

                **English Definition**: with calves like an antelope; with haunches like a deer; eighth of the thirty-two marks of a great man 
\"\"\"

"""

    response = openai.ChatCompletion.create(
        messages=[
            {'role': 'system', 'content': 'You are a helpful assistant that translates English text to Russian considering the context.'},
            {'role': 'user', 'content': query},
        ],
        model="gpt-3.5-turbo-0125",
        temperature=0,
    )

    print(response.choices[0].message.content)


# check_remaining_quota()

# check_availible_engines()

# test_request()


