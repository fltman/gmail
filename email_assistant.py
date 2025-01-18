import os
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import pickle
import openai
from datetime import datetime
import time
from email.parser import BytesParser
from email.policy import default
from email.message import EmailMessage

class GmailAssistant:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
        self.creds = None
        self.service = None
        openai.api_key = os.getenv('OPENAI_API_KEY')

    def authenticate(self):
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', 
                    self.SCOPES,
                    redirect_uri='http://localhost:8080'
                )
                self.creds = flow.run_local_server(
                    port=8080,
                    access_type='offline',
                    include_granted_scopes='true'
                )
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)

        self.service = build('gmail', 'v1', credentials=self.creds)

    def get_unread_emails(self):
        results = self.service.users().messages().list(
            userId='me', labelIds=['INBOX', 'UNREAD']).execute()
        return results.get('messages', [])

    def analyze_email(self, message):
        msg = self.service.users().messages().get(
            userId='me', id=message['id']).execute()
        
        headers = msg['payload']['headers']
        subject = next(h['value'] for h in headers if h['name'] == 'Subject')
        sender = next(h['value'] for h in headers if h['name'] == 'From')
        
        # Get email body
        if 'parts' in msg['payload']:
            body = msg['payload']['parts'][0]['body'].get('data', '')
        else:
            body = msg['payload']['body'].get('data', '')
        
        if body:
            body = base64.urlsafe_b64decode(body).decode('utf-8')

        # Ask OpenAI to analyze the email
        prompt = f"""
        Analyze this email and determine the best action:
        From: {sender}
        Subject: {subject}
        Body: {body}

        Possible actions:
        1. FORWARD_TO_MERCH - Forward to merchandise distributor
        2. JOB_APPLICATION - Sort as job application
        3. ARCHIVE - Move to archive (use this for any other emails)

        Analyze if this is a merchandise/product related email that needs distributor attention,
        or if it's a job application (look for resume mentions, job inquiries, or application related content).
        Respond with only one of the above action keywords and a brief reason.
        """

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content.strip().split('\n')[0]

    def take_action(self, message_id, action):
        try:
            if action.startswith('FORWARD_TO_MERCH'):
                # First try to forward the email
                try:
                    self.forward_email(message_id, 'name@email.se')
                    print("Email forwarded successfully")
                except Exception as e:
                    print(f"Error forwarding email: {str(e)}")

                # Then try to move it to the Merchandise folder
                try:
                    self.service.users().messages().modify(
                        userId='me',
                        id=message_id,
                        body={
                            'addLabelIds': [self.label_ids['Merchandise']],
                            'removeLabelIds': ['INBOX', 'UNREAD']
                        }
                    ).execute()
                    print("Email moved to Merchandise folder")
                except Exception as e:
                    print(f"Error moving email: {str(e)}")

            elif action.startswith('JOB_APPLICATION'):
                try:
                    self.service.users().messages().modify(
                        userId='me',
                        id=message_id,
                        body={
                            'addLabelIds': [self.label_ids['JobApplications']],
                            'removeLabelIds': ['INBOX', 'UNREAD']
                        }
                    ).execute()
                    print("Email moved to Job Applications folder")
                except Exception as e:
                    print(f"Error moving email: {str(e)}")

            elif action.startswith('ARCHIVE'):
                try:
                    self.service.users().messages().modify(
                        userId='me',
                        id=message_id,
                        body={
                            'addLabelIds': [self.label_ids['Archived']],
                            'removeLabelIds': ['INBOX', 'UNREAD']
                        }
                    ).execute()
                    print("Email archived")
                except Exception as e:
                    print(f"Error archiving email: {str(e)}")
            
            print(f"Email processed with action: {action}")
            
        except Exception as e:
            print(f"Error processing email: {str(e)}")

    def forward_email(self, message_id, to_address):
        try:
            # Get the original message
            msg = self.service.users().messages().get(
                userId='me', id=message_id).execute()
            
            # Extract headers
            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
            from_email = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
            
            # Get email body
            if 'parts' in msg['payload']:
                body = msg['payload']['parts'][0]['body'].get('data', '')
            else:
                body = msg['payload']['body'].get('data', '')
            
            if body:
                body = base64.urlsafe_b64decode(body).decode('utf-8')
            
            # Create forwarded message
            forward_text = f"""
---------- Forwarded message ---------
From: {from_email}
Subject: {subject}

{body}
"""
            # Create message
            message = MIMEText(forward_text)
            message['to'] = to_address
            message['subject'] = f"Fwd: {subject}"
            
            # Encode and send
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            self.service.users().messages().send(
                userId='me', body={'raw': raw}).execute()
            
            print(f"Successfully forwarded email to {to_address}")
        except Exception as e:
            print(f"Error in forward_email: {str(e)}")
            raise

    def _get_subject(self, message_id):
        """Helper method to get email subject"""
        try:
            msg = self.service.users().messages().get(userId='me', id=message_id).execute()
            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
            return subject
        except Exception as e:
            print(f"Error getting subject: {str(e)}")
            return 'No Subject'

    def add_label(self, message_id, label_name):
        self.service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'addLabelIds': [label_name]}
        ).execute()

    def archive_email(self, message_id):
        self.service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['INBOX']}
        ).execute()

    def ensure_labels_exist(self):
        """Ensure required labels exist in Gmail and return a mapping of our labels to Gmail IDs"""
        try:
            # Get existing labels
            results = self.service.users().labels().list(userId='me').execute()
            existing_labels = {label['name']: label['id'] for label in results.get('labels', [])}
            
            # Define all required labels with their display names
            required_labels = {
                'Merchandise': 'Forwarded to Merchandise',
                'JobApplications': 'Job Applications',
                'Archived': 'Archived Emails'
            }
            
            # Store label IDs for use in modifications
            self.label_ids = {}
            
            for label_id, display_name in required_labels.items():
                # Check if label exists by display name
                label_gmail_id = next((label['id'] for label in results.get('labels', []) 
                                    if label['name'] == display_name), None)
                
                if not label_gmail_id:
                    # Create new label if it doesn't exist
                    label_object = {
                        'name': display_name,
                        'labelListVisibility': 'labelShow',
                        'messageListVisibility': 'show'
                    }
                    created_label = self.service.users().labels().create(
                        userId='me',
                        body=label_object
                    ).execute()
                    label_gmail_id = created_label['id']
                    print(f"Created label: {display_name}")
                
                self.label_ids[label_id] = label_gmail_id
                
        except Exception as e:
            print(f"Error creating labels: {str(e)}")

    def run(self):
        print("Starting Gmail Assistant...")
        # Ensure labels exist before starting
        self.ensure_labels_exist()
        
        while True:
            try:
                messages = self.get_unread_emails()
                for message in messages:
                    action = self.analyze_email(message)
                    self.take_action(message['id'], action)
                    print(f"Processed email with action: {action}")
                
                time.sleep(5)
            except Exception as e:
                print(f"Error occurred: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying

if __name__ == "__main__":
    assistant = GmailAssistant()
    assistant.authenticate()
    assistant.run() 