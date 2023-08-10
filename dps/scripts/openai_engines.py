# print list of available engines for your account in openai

import openai
from dps.tools.config import OPENAI_API_KEY

# Set your API key
openai.api_key = OPENAI_API_KEY

# Fetch list of available engines
engines = openai.Engine.list()

# Print each engine's ID
for engine in engines["data"]:
    print(engine["id"])