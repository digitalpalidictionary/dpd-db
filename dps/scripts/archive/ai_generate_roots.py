#!/usr/bin/env python3

"""making ai generated translation for roots  saving to db"""

from openai import OpenAI

from db.db_helpers import get_db_session
from db.models import DpdHeadword, DpdRoot
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths    
from dps.tools.ai_related import load_openai_config

from sqlalchemy import and_
from sqlalchemy import func

from timeout_decorator import timeout, TimeoutError as TimeoutDecoratorError

pth = ProjectPaths()
dpspth = DPSPaths()
db_session = get_db_session(pth.dpd_db_path)

# model="gpt-4o"
# model="gpt-4o-mini"
model="gpt-4o-2024-08-06"
hight_model="gpt-4o-2024-08-06"

api_key = load_openai_config()
client = OpenAI(api_key=api_key)


def roots_meaning_generating(lang):

    #! for filling those which does not have Russian root meaing

    # Define a subquery that counts the related DpdHeadword entries
    subquery = db_session.query(
        DpdHeadword.root_key, func.count(DpdHeadword.id) \
            .label('headword_count')) \
            .group_by(DpdHeadword.root_key) \
            .subquery()

    if lang == "pali":

        roots = db_session.query(DpdRoot) \
            .join(subquery, DpdRoot.root == subquery.c.root_key) \
            .filter(and_(DpdRoot.root_ru_meaning == '', )) \
            .order_by(subquery.c.headword_count.desc()) \
            .limit(1000) \
            .all()

    elif lang == "sk":

        roots = db_session.query(DpdRoot).join(
                subquery, DpdRoot.root == subquery.c.root_key
            ).filter(
                and_(
                    DpdRoot.sanskrit_root_ru_meaning == '',
                    DpdRoot.sanskrit_root_ru_meaning != '-',
                )
            ).order_by(
                subquery.c.headword_count.desc()
            ).limit(1000).all()

    else:
        print("wrong language")

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


@timeout(10, timeout_exception=TimeoutDecoratorError)  # Setting a 10-second timeout
def call_openai(messages):
    return client.chat.completions.create(
        model=model,
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
                Please provide Russian translation for the English definition, considering the Pali root and its Pali word example. Ensure that the translation is in the infinitive form of the verb, avoiding repetition. In the answer give only Russian words in one line and nothing else. 
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
                Please provide Russian translation for the English definition, considering the Sanskrit root. Ensure that the translation is in the infinitive form of the verb, avoiding repetition. In the answer give only Russian words in one line and nothing else.
            """
        }
    ]

    suggestion = handle_openai_response(messages)

    return suggestion


if __name__ == "__main__":

    print("Translationg with the help of AI")

    roots_meaning_generating("pali")

    # roots_meaning_generating("sk")


