
import requests
from fastapi import FastAPI
import gradio as gr
import os
import openai
import uvicorn
import json
import gspread 
# import emails
from dotenv import load_dotenv, find_dotenv
from google.auth import default
from oauth2client.service_account import ServiceAccountCredentials
from crawler import WebCrawler
from google_docs_automation import GoogleDocsAutomation


_ = load_dotenv(find_dotenv()) # read local .env file

openai.api_key  = os.environ['OPENAI_API_KEY']

json_path = 'bizgsheetkey.json'
# Local Setup: check if the JSON file exists
if os.path.exists(json_path):
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
# Cloud Setup: obtain credentials with GCP Application Default Credentials
else: 
    credentials, project = default()

client = gspread.authorize(credentials)
worksheet = client.open("ChatGPT Prompts for Emails, Ads, Landing Pages").sheet1
print("\n\nReading Prompts from", worksheet.title)

# Values for creating Google Doc Report Files
json_path = 'googledocreport.json'
template_file_id = os.environ['TEMPLATE_FILE_ID']
emails = os.getenv("EMAILS").split(",")




def read_sheet():
    sheet_content = worksheet.get_all_values()
    if sheet_content:
        print("\n\ngoogle sheet loaded successfully!\n\n")
        # Drop the first row (header) [title, prompt]
        prompts_without_header = sheet_content[1:]
        # Keep only the second column (prompt) from each row
        # prompts_from_sheet = [row[1] for row in prompts_without_header]
        print(prompts_without_header[:][0])
        return prompts_without_header
    else: 
        print("\n\ngoogle sheet failed to load!\n\n")
        return ["no title","no prompts"]


def read_website(website_url, text_limit = 10000):
    crawler = WebCrawler(website_url, text_limit)
    text_content = crawler.collect_texts()
    biz_information = "\n\nThere is no information about this business!\n\n" # defult msg
    if text_content:
        biz_information = text_content
    print("\n\n", biz_information ,"\n\n")
    return biz_information



def save_and_email_leads(file_content_gdoc, url):
    # Create an instance of GoogleDocsAutomation and automate the process
    print("\n***saving google doc for the generated report***\n")
    copy_title = 'Report for ' + url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
    automation = GoogleDocsAutomation(json_path, template_file_id, copy_title, emails, file_content_gdoc)
    gdoc_url = automation.automate_process()
    # print('\n*******sending out email')
    # emails.send_out_email(my_user=user)
    # print('\n*******email has been sent')
    



def call_openai_api(messages, 
                    model= "gpt-3.5-turbo-16k", 
                    temperature=0.0, 
                    max_tokens=250):
    try:
        response = openai.ChatCompletion.create(model=model,
                                                messages=messages,
                                                temperature=temperature, # this is the degree of randomness of the model's output
                                                max_tokens=max_tokens, # the maximum number of tokens the model can ouptut 
                                                )
        print("\n\nAPI call successful for: ", messages[1]['content'])
        return response.choices[0].message["content"]
    
    except Exception as e:  # to be improved to handle any possible errors such as service overload
        print("Network error:", e)
        return "Sorry, there is a technical issue on my side... \
        please wait a few seconds and try again."


def process_user_message(user_input, all_messages, instruction_knowledge):
    delimiter = "```"
    messages = [
        {'role': 'system', 'content': instruction_knowledge},
        {'role': 'user', 'content': f"{delimiter}{user_input}{delimiter}"},
    ]
    api_response = call_openai_api(messages) #(all_messages + messages)
    # all_messages = all_messages + messages[1:]
    return api_response #, all_messages
    

app = FastAPI()

@app.get('/')
def root():
    return {"message": "hello from biz report! Redirect to /report"}



def run_report(url, sys_instructions):
    sheet_results = read_sheet()
    if not url.startswith("https://") and not url.startswith("http://"):
        url = "https://" + url
    web_results = read_website(url)
    overall_instructions = f"{sys_instructions} {web_results}"
    overall_resutls = ""
    for question in sheet_results:
        api_answer = process_user_message(question[1], None, overall_instructions)
        if api_answer:
            overall_resutls += "\n" + question[0] +"\n"+ api_answer + "\n\n"
    if overall_resutls:
        save_and_email_leads(overall_resutls, url) # write to google doc

    return overall_resutls

system_instruction = """Help me analyze a business based on the DotComSecrets and Expert Secrets by Russell Brunson \
    and Copywriting frameworks by Gary Halbert. \
    Use these frameworks to answer any questions and prompts about the business \
    with their provided information in the knowledge-base here \
    """

print("\n===gradio block started======\n")
with gr.Blocks(css="footer {visibility: hidden}") as demo:
    url = gr.Textbox(label="About Page URL", value="https://blitzfrontmedia.com/about/")
    instructions = gr.Textbox(label="Instructions", value=system_instruction)
    submit = gr.Button("Submit")
    textbox = gr.Textbox(label="Report", show_copy_button=True)
    submit.click(fn=run_report, inputs=[url,instructions], outputs=textbox)
gr.mount_gradio_app(app, demo, path="/report")



if __name__ == "__main__":
    print("\n\napp v.2 starts...\n\n")
    print("\n======api started to redirect=====\n")
    uvicorn.run(app, host='0.0.0.0', port=8080)


