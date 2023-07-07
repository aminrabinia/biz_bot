
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
from dotenv import load_dotenv, find_dotenv
from google.auth import default

_ = load_dotenv(find_dotenv()) # read local .env file

openai.api_key  = os.environ['OPENAI_API_KEY']

# Use GCP Application Default Credentials
# credentials, project = default()
# client = gspread.authorize(credentials)
# worksheet = client.open("Lexus_dealership").sheet1
# print("\n\nWriting contacts to", worksheet.title)

user = UserData()

functions=[
    {
        "name": "get_user_info",
        "description": "Collect customer's selected car, name and email.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string", 
                                  "description": "first and,or last name of customer"},        
                "customer_email": {"type": "string",
                                   "description": "customer's email address"},
                "selected_car": {"type": "string", 
                                 "description": "the type of car that customer is interested in",
                                 "enum": ["Lexus RX", "Lexus NX", "Lexus IS", "Lexus GX"]}
            },
            "required": ["customer_name", "customer_email", "selected_car"],
        },
    }
]

def save_and_email_leads():
    print('\n-- writing to the spreadsheet')
    # worksheet.insert_row([user.customer_name, user.customer_email, user.selected_car])
    print('\n*******sending out email')
    emails.send_out_email(my_user=user)
    print('\n*******email has been sent')
    # clean the object
    user.customer_name = ""
    user.customer_email = ""
    user.selected_car = ""


def call_openai_api(messages, 
                    model="gpt-3.5-turbo-16k", 
                    temperature=0, 
                    max_tokens=100, 
                    call_type="none"):
    try:
        response = openai.ChatCompletion.create(model=model,
                                                messages=messages,
                                                temperature=temperature, # this is the degree of randomness of the model's output
                                                max_tokens=max_tokens, # the maximum number of tokens the model can ouptut 
                                                functions=functions,
                                                function_call=call_type,
        )
        return response
    
    except requests.exceptions.RequestException as e:  # to be improved to handle any possible errors such as service overload
        print("Network error:", e)
        return "Sorry, there is a technical issue on my side... \
        please wait a few seconds and try again."

def get_completion_from_messages(messages):

    print("all msg history:\n", messages)

    api_response = call_openai_api(messages, 
                                    model="gpt-3.5-turbo-16k", 
                                    temperature=0, 
                                    max_tokens=100, 
                                    call_type="auto")
    gpt_response = api_response["choices"][0]["message"]
    print('gpt response------: ', gpt_response)

    if gpt_response.get("function_call"):
        function_name = gpt_response["function_call"]["name"]
        if function_name == "get_user_info":
            arguments = json.loads(gpt_response["function_call"]["arguments"])
            user.get_user_info(
                                customer_name=arguments.get("customer_name"),
                                customer_email=arguments.get("customer_email"),
                                selected_car=arguments.get("selected_car")
                                )
            return call_openai_api(messages = messages,  
                                     model="gpt-3.5-turbo-16k", 
                                     temperature=0, 
                                     max_tokens=100,
                                     call_type="none").choices[0].message["content"]
    # if all the arguments present, write to file and send email
    if user.customer_name and user.customer_email and user.selected_car:
        save_and_email_leads()
        # if function call activated it returns content null, 
        # so call api again to get response without function call
        return call_openai_api(messages = [
                                {'role': 'system', 'content': "Thank customer for providing information. \
                                Ensure them someone will be in touch with them to follow up."}],  
                                model="gpt-3.5-turbo-16k", 
                                temperature=0, 
                                max_tokens=100,
                                call_type="none").choices[0].message["content"]
    else: 
        print("No function activated")
        return api_response.choices[0].message["content"]



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
    system_message = f"""
    You are a customer service assistant for a Lexus car dealership. \
    Respond in a friendly and helpful tone, with concise answers from the relevant information available. \
    Don't make assumptions about what values to plug into functions. \
    Ask for customer's selected car, name and email, one by one. \
    Admit receiving any response and don't repeat already answered questions.
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


