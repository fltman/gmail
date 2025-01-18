# Gmail Assistant

An automated email assistant that monitors your Gmail inbox, analyzes emails using GPT-4, and takes appropriate actions like forwarding merchandise inquiries and sorting job applications.

## Features

- Automatically monitors Gmail inbox for new emails
- Uses GPT-4 to analyze email content
- Forwards merchandise-related emails to specified address
- Sorts job applications into a dedicated folder
- Creates organized labels in Gmail

## Prerequisites

- Python 3.7 or higher
- Gmail account
- Google Cloud Platform account
- OpenAI API key

## Installation

1. Clone this repository
2. Install requirements:
```bash
pip install -r requirements.txt
```

## Setup Steps

### 1. Google Cloud Platform Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project
3. Enable Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

4. Configure OAuth Consent Screen:
   - Go to "APIs & Services" > "OAuth consent screen"
   - Choose "External" user type
   - Fill in required information:
     - App name: "Gmail Assistant"
     - User support email: your email
     - Developer contact email: your email
   - Add scope: `https://www.googleapis.com/auth/gmail.modify`
   - Add your Gmail address as a test user

5. Create OAuth Credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop application"
   - Download JSON file
   - Save as `credentials.json` in project directory

### 2. OpenAI API Setup

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Create or log into your account
3. Navigate to API section
4. Create new API key
5. Set as environment variable:

```bash
# On Unix/Linux/macOS
export OPENAI_API_KEY='your-api-key-here'

# On Windows (Command Prompt)
set OPENAI_API_KEY=your-api-key-here

# On Windows (PowerShell)
$env:OPENAI_API_KEY='your-api-key-here'
```

### 3. Email Configuration

Edit `email_assistant.py` to set your forwarding email address:
```python
self.forward_email(message_id, 'your-email@domain.com')
```

## Usage

1. Run the assistant:
```bash
python email_assistant.py
```

2. First run:
   - Browser window will open
   - Log in with Gmail account
   - Grant requested permissions
   - `token.pickle` will be created for future use

3. The assistant will:
   - Create required Gmail labels automatically
   - Monitor inbox for new emails
   - Process emails according to content
   - Print status messages to console

## Gmail Labels

The assistant creates three labels:
- "Forwarded to Merchandise" - for forwarded merchandise emails
- "Job Applications" - for job application emails
- "Archived Emails" - for other processed emails

## Troubleshooting

### Authentication Issues
If you get authentication errors:
- Delete `token.pickle`
- Verify `credentials.json` is present and valid
- Run script again

### Email Processing Issues
If emails aren't being processed:
- Check console for error messages
- Verify OpenAI API key is set correctly
- Check Gmail permissions
- Ensure internet connection is stable

## Security Notes

- Keep `credentials.json` and `token.pickle` secure
- Never commit these files to version control
- Regularly monitor OpenAI API usage
- Keep your OpenAI API key secure

## Files in Project

- `email_assistant.py` - Main script
- `requirements.txt` - Python dependencies
