
import requests
from fastapi import FastAPI
import gradio as gr
import os
import openai
import uvicorn
import json
import gspread 
import emails
from dotenv import load_dotenv, find_dotenv
from google.auth import default
from oauth2client.service_account import ServiceAccountCredentials
import WebCrawler

_ = load_dotenv(find_dotenv()) # read local .env file

openai.api_key  = os.environ['OPENAI_API_KEY']

json_path = 'bizkey.json'
# Check if the JSON file exists
if os.path.exists(json_path):
    # Load the credentials from the service account JSON file
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
else:
    # JSON file exists, use it to obtain credentials with GCP Application Default Credentials
    credentials, project = default()

client = gspread.authorize(credentials)
worksheet = client.open("ChatGPT Prompts for Emails, Ads, Landing Pages").sheet1
print("\n\nReading Prompts from", worksheet.title)
sheet_content = worksheet.get_all_values()
if sheet_content:
    print("google sheet content loaded successfully!")


website_url = 'https://scikit-learn.org/stable/about.html'

crawler = WebCrawler(website_url, text_limit = 10000)
text_content = crawler.collect_texts()
biz_information = "There is no information about this business!"
if text_content:
    print(text_content)
    biz_information = text_content
else:
    print("--- no data extracted about the business ---")



def save_and_email_leads():
    print('\n*******sending out email')
    emails.send_out_email(my_user=user)
    print('\n*******email has been sent')



def call_openai_api(messages, 
                    model= "gpt-3.5-turbo-16k", 
                    temperature=0.0, 
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
    
    except Exception as e:  # to be improved to handle any possible errors such as service overload
        print("Network error:", e)
        return "Sorry, there is a technical issue on my side... \
        please wait a few seconds and try again."

def get_completion_from_messages(messages):

    # if all the arguments present, write to file and send email
    if user.customer_name and user.customer_email and user.selected_car:
        save_and_email_leads()
        # if function call activated it returns content null, 
        # so call api again to get response without function call
        return call_openai_api(messages = [
                                {'role': 'system', 'content': f"Thank customer for providing information. \
                                Ensure them someone will be in touch with them to follow up about {user.selected_car}."}],  
                                call_type="none"
                                ).choices[0].message["content"]  # return content 

    # else if args not complete, continue the chat and look for function activation
    api_response = call_openai_api(messages, 
                                    call_type="auto")
    gpt_response = api_response["choices"][0]["message"]

    if gpt_response.get("function_call"):
        function_name = gpt_response["function_call"]["name"]
        if function_name == "get_user_info":
            arguments = json.loads(gpt_response["function_call"]["arguments"])
            user.get_user_info(
                                customer_name=arguments.get("customer_name"),
                                customer_email=arguments.get("customer_email"),
                                selected_car=arguments.get("selected_car")
                                )
            # if args collected, continue the chat with no function activation
            return call_openai_api(messages = messages,  
                                     call_type="none"
                                     ).choices[0].message["content"]

    else: 
        print("No function activated")
        return api_response.choices[0].message["content"]





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
    ]

    final_response = get_completion_from_messages(all_messages + messages)
    all_messages = all_messages + messages[1:]
    
    return final_response, all_messages
    

app = FastAPI()

@app.get('/')
def root():
    return {"message": "hello from biz report! Redirect to /report"}


context = [{'role':'system', 'content':"You are Service Assistant"}, 
           {'role': 'assistant', 'content': f"Relevant product and service information:\n{biz_information}"}]
chat_history = []

print("\n===gradio block started======\n")
with gr.Blocks(css="footer {visibility: hidden}") as demo:
    gr.Textbox(value=sheet_content)
gr.mount_gradio_app(app, demo, path="/report")



if __name__ == "__main__":
    print("\n======api started to redirect=====\n")
    uvicorn.run(app, host='0.0.0.0', port=8080)


