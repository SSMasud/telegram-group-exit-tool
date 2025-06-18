# Telegram Group Exit Tool

A Streamlit-based web application that helps you easily leave Telegram groups containing specific keywords in their titles.

## Features

- User-friendly web interface
- Secure API credential handling
- Search groups by keyword
- Multi-select groups to leave
- Progress tracking
- Confirmation steps to prevent accidents

## Prerequisites

- Python 3.7 or higher
- Telegram account
- Telegram API credentials (API ID and API Hash)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd telegram-group-exit-tool
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

## Getting Telegram API Credentials

1. Visit [my.telegram.org](https://my.telegram.org)
2. Log in with your Telegram phone number
3. Click on "API Development Tools"
4. Create a new application
5. Copy your API ID and API Hash

## Running the Application

1. Start the Streamlit app:
```bash
streamlit run app.py
```

2. Open your web browser and navigate to the URL shown in the terminal (usually http://localhost:8501)

3. Enter your API credentials in the sidebar

4. Follow the on-screen instructions to:
   - Enter your phone number
   - Enter the verification code sent to your Telegram app
   - Search for groups by keyword
   - Select groups to leave
   - Confirm and execute the operation

## Safety Features

- Password-protected API credential input
- Confirmation step before leaving groups
- Multi-select option to choose specific groups
- Progress tracking during the operation
- Error handling and user feedback

## Note

This tool is designed to help manage Telegram group memberships efficiently. Please use it responsibly and ensure you want to leave the selected groups before confirming the action. 