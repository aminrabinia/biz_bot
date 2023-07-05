
import requests
from fastapi import FastAPI
import gradio as gr
import os
import openai
import uvicorn
import json
import gspread 
from contact import UserData
import emails
# from google.cloud import secretmanager
# from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv, find_dotenv
from google.auth import default

# Use Application Default Credentials
credentials, project = default()

_ = load_dotenv(find_dotenv()) # read local .env file

openai.api_key  = os.environ['OPENAI_API_KEY']


scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
 
# credentials = ServiceAccountCredentials.from_json_keyfile_name(get_service_account_json(), scope)
client = gspread.authorize(credentials)
worksheet = client.open("Lexus_dealership").sheet1
print("\n\nWriting contacts to", worksheet.title)

user = UserData()

functions=[
    {
        "name": "get_user_info",
        "description": "Get users contact information and selected car.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},        
                "email": {"type": "string"},
                "car": {"type": "string", 
                "description": "the type of car that user is interested in",
                "enum": ["Lexus RX", "Lexus NX", "Lexus IS", "Lexus GX"]}
            },
            "required": [],
        },
    }
]


def get_completion_from_messages(messages, 
                                 model="gpt-3.5-turbo-16k", 
                                 temperature=0, 
                                 max_tokens=100):
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature, # this is the degree of randomness of the model's output
            max_tokens=max_tokens, # the maximum number of tokens the model can ouptut 
            functions=functions,
            function_call="auto",
        )
    except requests.exceptions.RequestException as e:
        print("Network error:", e)
        return "Sorry, there is a technical issue on my side... \
        please wait a few seconds and try again."

    gpt_response = response["choices"][0]["message"]
    print(gpt_response)

    if gpt_response.get("function_call"):
        function_name = gpt_response["function_call"]["name"]
        if function_name == "get_user_info":
            arguments = json.loads(gpt_response["function_call"]["arguments"])
            user.get_user_info(
	            name=arguments.get("name"),
	            email=arguments.get("email"),
	            car=arguments.get("car")
                )
            worksheet.insert_row([user.name, user.email, user.car])
        else:
            print("get_user_info not activated")
    else: 
        print("No function activated")
    return response.choices[0].message["content"]



product_information="""

Products name, year and price:
Lexus RX 2022 $30,000
Lexus NX 2023 $43,000
Lexus IS 2020 $23,000
Lexus GX 2023 $43,000

Services available at the dealership:
Leasing a new car
Buying a new car
Buying a pre-owned car
Car inspection and repair

"""

def process_user_message(user_input, all_messages):
    delimiter = "```"
    # Step 4: Answer the user question
    system_message = f"""
    You are a customer service assistant for a Lexus car dealership. \
    Respond in a friendly and helpful tone, with concise answers from the relevant information available. \
    Ask for user's selected car, name and email, one by one, to contact them later.
    """
    messages = [
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': f"{delimiter}{user_input}{delimiter}"},
        {'role': 'assistant', 'content': f"Relevant product and service information:\n{product_information}"}
    ]

    final_response = get_completion_from_messages(all_messages + messages)
    all_messages = all_messages + messages[1:]
    
    return final_response, all_messages
    

app = FastAPI()

@app.get('/')
def root():
    return {"message": "hello from chatbot! Redirect to /chatbot"}


context = [{'role':'system', 'content':"You are Service Assistant"}]
chat_history = []

print("\n===chatbot started======\n")
with gr.Blocks(css="footer {visibility: hidden}") as demo:
    chatbot = gr.Chatbot([["","Hello from LEXUS Dealership! How can I help?"]])
    msg = gr.Textbox()
    clear = gr.ClearButton([msg, chatbot])

    def respond(message, chat_history):
        global context
        response, context = process_user_message(message, context)
        context.append({'role':'assistant', 'content':f"{response}"})
        chat_history.append((message, response))
        return "", chat_history

    msg.submit(respond, [msg, chatbot], [msg, chatbot])
gr.mount_gradio_app(app, demo, path="/chatbot")



if __name__ == "__main__":
    print("\n======api started to redirect=====\n")
    uvicorn.run(app, host='0.0.0.0', port=8080)
    print('\n+++++++sending email')
    emails.send_out_email(my_user=user)
    print('\n*******email has been sent')

