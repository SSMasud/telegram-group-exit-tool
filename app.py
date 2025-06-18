import streamlit as st
import asyncio
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.tl.functions.messages import DeleteChatUserRequest
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="Telegram Group Exit Tool",
    page_icon="🚪",
    layout="centered"
)

# Add custom CSS
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        margin-top: 20px;
    }
    .success-message {
        padding: 20px;
        border-radius: 5px;
        background-color: #d4edda;
        color: #155724;
        margin: 10px 0;
    }
    .warning-message {
        padding: 20px;
        border-radius: 5px;
        background-color: #fff3cd;
        color: #856404;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Title and description
st.title("🚪 Telegram Group Exit Tool")
st.markdown("""
This tool helps you automatically leave Telegram groups containing specific keywords in their titles.
Please enter your Telegram API credentials and the keyword to get started.
""")

# Initialize session state
if 'client' not in st.session_state:
    st.session_state.client = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Sidebar for API credentials
with st.sidebar:
    st.header("📱 API Credentials")
    st.markdown("""
    Get your API credentials from:
    1. Visit [my.telegram.org](https://my.telegram.org)
    2. Log in with your phone number
    3. Click "API Development Tools"
    4. Create a new application
    """)
    
    api_id = st.text_input("API ID", type="password", help="Enter your Telegram API ID")
    api_hash = st.text_input("API Hash", type="password", help="Enter your Telegram API Hash")
    
async def get_target_groups(client, word):
    matches = []
    async for dlg in client.iter_dialogs():
        ent = dlg.entity
        title = getattr(ent, 'title', '') or ''
        if word.lower() in title.lower():
            matches.append((ent, title))
    return matches

async def leave_entity(client, ent):
    if isinstance(ent, Channel):
        await client(LeaveChannelRequest(ent))
    elif isinstance(ent, Chat):
        await client(DeleteChatUserRequest(ent.id, 'me'))

async def initialize_client(api_id, api_hash):
    try:
        client = TelegramClient('anon', api_id, api_hash)
        await client.connect()
        if not await client.is_user_authorized():
            phone = st.text_input("Enter your phone number (with country code):")
            if phone:
                try:
                    code = await client.send_code_request(phone)
                    verification_code = st.text_input("Enter the verification code sent to your Telegram app:")
                    if verification_code:
                        await client.sign_in(phone, verification_code)
                        st.session_state.logged_in = True
                        return client
                except Exception as e:
                    st.error(f"Error during authentication: {str(e)}")
                    return None
        else:
            st.session_state.logged_in = True
            return client
    except Exception as e:
        st.error(f"Error initializing client: {str(e)}")
        return None

async def main():
    if not api_id or not api_hash:
        st.warning("Please enter your API credentials in the sidebar.")
        return

    if not st.session_state.client and not st.session_state.logged_in:
        st.session_state.client = await initialize_client(int(api_id), api_hash)

    if st.session_state.logged_in and st.session_state.client:
        keyword = st.text_input("Enter the keyword to search for in group titles:", 
                              help="Groups containing this keyword will be listed for removal")
        
        if keyword:
            if st.button("Search Groups"):
                with st.spinner("Searching for matching groups..."):
                    groups = await get_target_groups(st.session_state.client, keyword)
                    
                    if not groups:
                        st.info("No groups found matching your keyword.")
                        return
                    
                    st.write("### Found Groups:")
                    group_options = {title: ent for ent, title in groups}
                    selected_groups = st.multiselect(
                        "Select groups to leave:",
                        options=list(group_options.keys()),
                        default=list(group_options.keys())
                    )
                    
                    if selected_groups:
                        if st.button("Leave Selected Groups", key="leave_groups"):
                            confirm = st.checkbox("I confirm that I want to leave these groups")
                            if confirm:
                                progress_bar = st.progress(0)
                                for i, title in enumerate(selected_groups):
                                    try:
                                        await leave_entity(st.session_state.client, group_options[title])
                                        progress_bar.progress((i + 1) / len(selected_groups))
                                        await asyncio.sleep(1.5)
                                    except Exception as e:
                                        st.error(f"Error leaving {title}: {str(e)}")
                                st.success("Successfully left all selected groups!")
                            else:
                                st.warning("Please confirm that you want to leave these groups.")

if __name__ == "__main__":
    if st.sidebar.button("Logout", key="logout"):
        st.session_state.client = None
        st.session_state.logged_in = False
        st.experimental_rerun()
    
    asyncio.run(main()) 