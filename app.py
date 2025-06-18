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
if 'phone_entered' not in st.session_state:
    st.session_state.phone_entered = False
if 'code_sent' not in st.session_state:
    st.session_state.code_sent = False
if 'phone_code_hash' not in st.session_state:
    st.session_state.phone_code_hash = None

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

@st.cache_data
def get_target_groups_sync(api_id, api_hash, word, session_string=None):
    """Synchronous wrapper for async function to work with Streamlit caching"""
    async def _get_groups():
        client = TelegramClient('session', api_id, api_hash)
        if session_string:
            client.session.load(session_string)
        
        await client.connect()
        matches = []
        try:
            async for dlg in client.iter_dialogs():
                ent = dlg.entity
                title = getattr(ent, 'title', '') or ''
                if word.lower() in title.lower():
                    matches.append((ent.id, title, type(ent).__name__))
        finally:
            await client.disconnect()
        return matches
    
    return asyncio.run(_get_groups())

async def leave_entity_by_id(client, entity_id, entity_type):
    """Leave entity by ID and type"""
    try:
        if entity_type == 'Channel':
            entity = await client.get_entity(entity_id)
            await client(LeaveChannelRequest(entity))
        elif entity_type == 'Chat':
            await client(DeleteChatUserRequest(entity_id, 'me'))
        return True
    except Exception as e:
        st.error(f"Error leaving entity {entity_id}: {str(e)}")
        return False

async def authenticate_user(api_id, api_hash, phone, verification_code=None, phone_code_hash=None):
    """Handle user authentication"""
    try:
        client = TelegramClient('session', api_id, api_hash)
        await client.connect()
        
        if not await client.is_user_authorized():
            if verification_code and phone_code_hash:
                await client.sign_in(phone, verification_code, phone_code_hash=phone_code_hash)
                session_string = client.session.save()
                await client.disconnect()
                return True, session_string
            else:
                result = await client.send_code_request(phone)
                phone_code_hash = result.phone_code_hash
                await client.disconnect()
                return False, phone_code_hash
        else:
            session_string = client.session.save()
            await client.disconnect()
            return True, session_string
    except Exception as e:
        await client.disconnect()
        return False, str(e)

def main():
    if not api_id or not api_hash:
        st.warning("Please enter your API credentials in the sidebar.")
        return

    # Authentication flow
    if not st.session_state.logged_in:
        st.subheader("🔐 Authentication")
        
        if not st.session_state.phone_entered:
            phone = st.text_input("Enter your phone number (with country code, e.g., +1234567890):")
            if st.button("Send Verification Code") and phone:
                try:
                    success, result = asyncio.run(authenticate_user(int(api_id), api_hash, phone))
                    if not success and result != "code_sent":
                        # result contains phone_code_hash
                        st.session_state.phone_entered = True
                        st.session_state.phone = phone
                        st.session_state.code_sent = True
                        st.session_state.phone_code_hash = result
                        st.success("Verification code sent! Please check your Telegram app.")
                        st.rerun()
                    elif success:
                        st.session_state.logged_in = True
                        st.session_state.session_string = result
                        st.success("Authentication successful!")
                        st.rerun()
                    else:
                        st.error(f"Authentication failed: {result}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        elif st.session_state.code_sent:
            st.info("Please enter the verification code sent to your Telegram app.")
            verification_code = st.text_input("Verification Code:")
            if st.button("Verify Code") and verification_code:
                try:
                    success, result = asyncio.run(
                        authenticate_user(
                            int(api_id), 
                            api_hash, 
                            st.session_state.phone, 
                            verification_code, 
                            st.session_state.phone_code_hash
                        )
                    )
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.session_string = result
                        st.success("Authentication successful!")
                        st.rerun()
                    else:
                        st.error(f"Verification failed: {result}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # Main functionality
    if st.session_state.logged_in:
        st.success("✅ Successfully authenticated!")
        
        keyword = st.text_input("Enter the keyword to search for in group titles:", 
                              help="Groups containing this keyword will be listed for removal")
        
        if keyword:
            if st.button("🔍 Search Groups"):
                with st.spinner("Searching for matching groups..."):
                    try:
                        groups = get_target_groups_sync(
                            int(api_id), api_hash, keyword, st.session_state.get('session_string')
                        )
                        
                        if not groups:
                            st.info("No groups found matching your keyword.")
                            return
                        
                        st.session_state.found_groups = groups
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error searching groups: {str(e)}")
            
            # Display found groups
            if 'found_groups' in st.session_state and st.session_state.found_groups:
                st.write("### 📋 Found Groups:")
                group_options = {f"{title} ({entity_type})": (entity_id, entity_type) 
                               for entity_id, title, entity_type in st.session_state.found_groups}
                
                selected_groups = st.multiselect(
                    "Select groups to leave:",
                    options=list(group_options.keys()),
                    default=list(group_options.keys())
                )
                
                if selected_groups:
                    st.warning(f"⚠️ You are about to leave {len(selected_groups)} group(s). This action cannot be undone.")
                    confirm = st.checkbox("I confirm that I want to leave these groups")
                    
                    if confirm and st.button("🚪 Leave Selected Groups", type="primary"):
                        progress_bar = st.progress(0)
                        success_count = 0
                        
                        async def leave_groups():
                            nonlocal success_count
                            client = TelegramClient('session', int(api_id), api_hash)
                            if 'session_string' in st.session_state:
                                client.session.load(st.session_state.session_string)
                            
                            await client.connect()
                            try:
                                for i, group_name in enumerate(selected_groups):
                                    entity_id, entity_type = group_options[group_name]
                                    success = await leave_entity_by_id(client, entity_id, entity_type)
                                    if success:
                                        success_count += 1
                                    progress_bar.progress((i + 1) / len(selected_groups))
                                    await asyncio.sleep(1.5)  # Rate limiting
                            finally:
                                await client.disconnect()
                        
                        try:
                            asyncio.run(leave_groups())
                            st.success(f"✅ Successfully left {success_count}/{len(selected_groups)} groups!")
                            # Clear the found groups to start fresh
                            if 'found_groups' in st.session_state:
                                del st.session_state.found_groups
                        except Exception as e:
                            st.error(f"Error during group leaving process: {str(e)}")

# Logout functionality
if st.sidebar.button("🚪 Logout", key="logout"):
    for key in ['client', 'logged_in', 'phone_entered', 'code_sent', 'phone', 'phone_code_hash', 'session_string', 'found_groups']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# Run the main function
if __name__ == "__main__":
    main() 