from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from google.auth import default
import os


class GoogleDocsAutomation:
    def __init__(self, json_path, template_file_id, copy_title, email, report_file_content):
        self.json_path = json_path
        self.template_file_id = template_file_id
        self.copy_title = copy_title
        self.email = email
        self.report_file_content = report_file_content
        self.drive_service = None
        self.docs_service = None

        self.replace_requests = [
            {
                'containsText': {
                    'text': 'New text content',
                    'matchCase': False
                },
                'replaceText': self.report_file_content
            },
        ]

        self.initialize()

    def initialize(self):
        if os.path.exists(self.json_path):
            # JSON file exists, use it to obtain credentials
            credentials = self.load_credentials(self.json_path)
        else:
            # Load the credentials from the service account JSON file
            credentials, project = default()

        print(credentials)
        
        self.drive_service = build('drive', 'v3', credentials=credentials)
        self.docs_service = build('docs', 'v1', credentials=credentials)

    @staticmethod
    def load_credentials(json_path):
        return service_account.Credentials.from_service_account_file(json_path)

    def create_copy(self):
        copy_metadata = {'name': self.copy_title}
        copied_file = self.drive_service.files().copy(fileId=self.template_file_id, body=copy_metadata).execute()
        return copied_file['id']

    def replace_text(self, copied_file_id):
        requests = [{'replaceAllText': request} for request in self.replace_requests]

        try:
            self.docs_service.documents().batchUpdate(documentId=copied_file_id, body={'requests': requests}).execute()
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def share_document(self, copied_file_id):
        for e in self.email:
            share_request = {
                'role': 'writer',
                'type': 'user',
                'emailAddress': e
            }
            self.drive_service.permissions().create(fileId=copied_file_id, body=share_request).execute()


    def get_copied_document_url(self, copied_file_id):
        return f'https://docs.google.com/document/d/{copied_file_id}/edit'

    def automate_process(self):
        self.initialize()
        copied_file_id = self.create_copy()
        self.replace_text(copied_file_id)
        self.share_document(copied_file_id)
        copied_document_url = self.get_copied_document_url(copied_file_id)
        print("Copied Document URL:", copied_document_url)
        return copied_document_url
