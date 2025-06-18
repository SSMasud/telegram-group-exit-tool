# 🚪 Telegram Group Exit Tool

A Streamlit-based web application that helps you easily leave Telegram groups containing specific keywords in their titles.

## ✨ Features

- 🌐 User-friendly web interface
- 🔒 Secure API credential handling
- 🔍 Search groups by keyword
- ✅ Multi-select groups to leave
- 📊 Progress tracking with visual feedback
- ⚠️ Confirmation steps to prevent accidents
- 🚀 Ready for Streamlit Community Cloud deployment

## 🔧 Prerequisites

- Python 3.7 or higher
- Telegram account
- Telegram API credentials (API ID and API Hash)

## 🚀 Quick Start (Streamlit Community Cloud)

1. **Fork this repository** to your GitHub account

2. **Get Telegram API credentials:**
   - Visit [my.telegram.org](https://my.telegram.org)
   - Log in with your Telegram phone number
   - Click on "API Development Tools"
   - Create a new application
   - Copy your API ID and API Hash

3. **Deploy on Streamlit Community Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub account
   - Deploy this repository
   - The app will be available at your custom Streamlit URL

## 💻 Local Development

### Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/telegram_exit_script.git
cd telegram_exit_script
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

### Running Locally

1. Start the Streamlit app:
```bash
streamlit run app.py
```

2. Open your web browser and navigate to `http://localhost:8501`

## 📱 How to Use

1. **Enter API Credentials:** Input your Telegram API ID and Hash in the sidebar
2. **Authenticate:** Enter your phone number and the verification code sent to your Telegram app
3. **Search Groups:** Enter a keyword to search for groups containing that word in their titles
4. **Select Groups:** Choose which groups you want to leave from the search results
5. **Confirm & Execute:** Confirm your selection and let the tool do the rest!

## 🛡️ Safety Features

- 🔐 Password-protected API credential input
- ✋ Confirmation step before leaving groups
- 🎯 Multi-select option to choose specific groups
- 📈 Progress tracking during the operation
- ⚠️ Comprehensive error handling and user feedback
- 🔄 Rate limiting to prevent API abuse

## 🏗️ Technical Details

- **Framework:** Streamlit
- **Telegram API:** Telethon library
- **Authentication:** Secure session management
- **Deployment:** Optimized for Streamlit Community Cloud

## ⚠️ Important Notes

- This tool is designed to help manage Telegram group memberships efficiently
- Please use it responsibly and ensure you want to leave the selected groups before confirming
- The tool implements rate limiting to comply with Telegram's API guidelines
- Your API credentials are only stored temporarily during the session

## 🤝 Contributing

Feel free to open issues or submit pull requests to improve this tool!

## 📄 License

This project is open source and available under the MIT License. 