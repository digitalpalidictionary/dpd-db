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

# Fetch list of available engines
engines = openai.Engine.list()

# Print each engine's ID
for engine in engines["data"]:
    print(engine["id"])