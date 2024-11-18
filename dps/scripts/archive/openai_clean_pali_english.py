# extract pali from english

from tools.configger import config_read


import openai

# Setup OpenAI API key
openai.api_key = config_read("openai", "key")



def main():

    input_text = read_text()

    chunks = separate_language_chunks(input_text)

    separated_results = []

    for chunk in chunks:
        separated_result = separate_languages_openai(chunk)
        separated_results.append(separated_result)

    output_text = "\n".join(separated_results)

    with open("resources/other_pali_texts/anandajoti_safeguard_recitals_pali_only.txt", "w", encoding="utf-8") as output_file:
        output_file.write(output_text)
    

def call_openai(messages):
    return openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0125",
        messages=messages
    )


def separate_language_chunks(text, max_chunk_size=4096):
    chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]
    return chunks


def separate_languages_openai(chunk):

    
    # Generate the chat messages based on provided values
    message = [
        {
            "role": "system",
            "content": "You are a helpful assistant that separate English text from Pāli text."
        },
        {
            "role": "user",
            "content": f"""
                ---
                **Full text**: {chunk}

                Pāli sentences has diacritics āīūṅñṭḍṇḷṃṁ. English does not. Separate the Pāli and English sentences in the following text and return only clean Pāli sentences
                ---
            """
        }
    ]

    suggestion = handle_openai_response(message)

    return suggestion



def read_text():

    file = "resources/other_pali_texts/anandajoti_safeguard_recitals_pe.txt"

    # files = [
    #     "resources/other_pali_texts/anandajoti_daily_chanting_pe.txt",
    #     "resources/other_pali_texts/anandajoti_safeguard_recitals_pe.txt"
    # ]
    
    # for file in files:
    with open(file, "r") as f:
        text = f.read()

    return text



def handle_openai_response(messages):

    response = call_openai(messages)
    suggestion = response.choices[0].message['content'].replace('**Русский перевод**: ', '').strip().lower() # type: ignore

    return suggestion



if __name__ == "__main__":
    main()
