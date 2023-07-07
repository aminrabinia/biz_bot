import openai
from dotenv import load_dotenv, find_dotenv
import os
import requests

_ = load_dotenv(find_dotenv()) # read local .env file

openai.api_key  = os.environ['OPENAI_API_KEY']

def test_api(messages, 
            model="gpt-3.5-turbo-16k", 
            temperature=0, 
            max_tokens=100, call_type="auto"):
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature, # this is the degree of randomness of the model's output
            max_tokens=max_tokens, # the maximum number of tokens the model can ouptut 
        )
    except requests.exceptions.RequestException as e:  # to be improved to handle any possible errors such as service overload
        print("Network error:", e)
        return "Sorry, there is a technical issue on my side... \
        please wait a few seconds and try again."

    gpt_response = response["choices"][0]["message"]
    print('gpt response------: ', gpt_response)

# test OpenAI API
# test_api([{'role': 'system', 'content': "is the api available?"}])

import fastapi

print(fastapi.__version__)


