import streamlit as st
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import Channel, Chat
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.tl.functions.messages import DeleteChatUserRequest
from telethon.errors import PhoneCodeExpiredError, PhoneCodeInvalidError, SessionPasswordNeededError, FloodWaitError
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

class TelegramAuthenticator:
    def __init__(self, api_id, api_hash):
        self.api_id = api_id
        self.api_hash = api_hash
        self.client = None
        self.phone_code_hash = None
        
    async def start_auth(self, phone):
        """Start authentication process and send verification code"""
        try:
            # Create client with StringSession and timeout
            self.client = TelegramClient(
                StringSession(), 
                self.api_id, 
                self.api_hash,
                connection_retries=1,
                retry_delay=1
            )
            
            # Add timeout to prevent hanging
            try:
                await asyncio.wait_for(self.client.connect(), timeout=10.0)
            except asyncio.TimeoutError:
                return False, None, "Connection timeout - please check your internet connection"
            
            # Check if already authorized
            try:
                is_authorized = await asyncio.wait_for(
                    self.client.is_user_authorized(), 
                    timeout=5.0
                )
                if is_authorized:
                    session_string = self.client.session.save()
                    await self.client.disconnect()
                    return True, session_string, "already_authorized"
            except asyncio.TimeoutError:
                await self.client.disconnect()
                return False, None, "Authorization check timeout"
            
            # Send code request with timeout
            try:
                sent_code = await asyncio.wait_for(
                    self.client.send_code_request(phone), 
                    timeout=15.0
                )
                self.phone_code_hash = sent_code.phone_code_hash
                
                # Save the session state
                session_string = self.client.session.save()
                await self.client.disconnect()
                return False, session_string, "code_sent"
                
            except asyncio.TimeoutError:
                await self.client.disconnect()
                return False, None, "Code request timeout - please try again"
            except FloodWaitError as e:
                await self.client.disconnect()
                return False, None, f"Rate limited - please wait {e.seconds} seconds"
            except Exception as e:
                await self.client.disconnect()
                error_msg = str(e).lower()
                if "phone number" in error_msg:
                    return False, None, "Invalid phone number format"
                elif "flood" in error_msg:
                    return False, None, "Too many attempts - please wait and try again"
                else:
                    return False, None, f"Failed to send code: {str(e)}"
                    
        except Exception as e:
            try:
                if self.client:
                    await self.client.disconnect()
            except:
                pass
            return False, None, f"Connection error: {str(e)}"
    
    async def verify_code(self, phone, code, session_string):
        """Verify the code using the same session"""
        try:
            # Recreate client with the saved session
            self.client = TelegramClient(
                StringSession(session_string), 
                self.api_id, 
                self.api_hash,
                connection_retries=1,
                retry_delay=1
            )
            
            try:
                await asyncio.wait_for(self.client.connect(), timeout=10.0)
            except asyncio.TimeoutError:
                return False, None, "Connection timeout during verification"
            
            try:
                # Use the stored phone_code_hash for verification
                await asyncio.wait_for(
                    self.client.sign_in(phone, code, phone_code_hash=self.phone_code_hash),
                    timeout=10.0
                )
                
                # Save the authenticated session
                final_session = self.client.session.save()
                await self.client.disconnect()
                return True, final_session, "success"
                
            except asyncio.TimeoutError:
                await self.client.disconnect()
                return False, None, "Verification timeout - please try again"
            except PhoneCodeExpiredError:
                await self.client.disconnect()
                return False, None, "code_expired"
            except PhoneCodeInvalidError:
                await self.client.disconnect()
                return False, None, "invalid_code"
            except SessionPasswordNeededError:
                final_session = self.client.session.save()
                await self.client.disconnect()
                return False, final_session, "2fa_required"
            except Exception as e:
                await self.client.disconnect()
                error_msg = str(e).lower()
                if "password" in error_msg or "two-factor" in error_msg:
                    final_session = self.client.session.save()
                    return False, final_session, "2fa_required"
                else:
                    return False, None, f"Sign-in error: {str(e)}"
                        
        except Exception as e:
            try:
                if self.client:
                    await self.client.disconnect()
            except:
                pass
            return False, None, f"Verification error: {str(e)}"
    
    async def verify_2fa(self, password, session_string):
        """Verify 2FA password"""
        try:
            self.client = TelegramClient(
                StringSession(session_string), 
                self.api_id, 
                self.api_hash,
                connection_retries=1,
                retry_delay=1
            )
            
            try:
                await asyncio.wait_for(self.client.connect(), timeout=10.0)
            except asyncio.TimeoutError:
                return False, None, "Connection timeout during 2FA"
            
            try:
                await asyncio.wait_for(
                    self.client.sign_in(password=password),
                    timeout=10.0
                )
                final_session = self.client.session.save()
                await self.client.disconnect()
                return True, final_session, "success"
            except asyncio.TimeoutError:
                await self.client.disconnect()
                return False, None, "2FA timeout - please try again"
            except Exception as e:
                await self.client.disconnect()
                return False, None, f"2FA error: {str(e)}"
                    
        except Exception as e:
            try:
                if self.client:
                    await self.client.disconnect()
            except:
                pass
            return False, None, f"2FA connection error: {str(e)}"

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
if 'authenticator' not in st.session_state:
    st.session_state.authenticator = None
if 'temp_session' not in st.session_state:
    st.session_state.temp_session = None

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
        if session_string:
            client = TelegramClient(StringSession(session_string), api_id, api_hash)
        else:
            client = TelegramClient(StringSession(), api_id, api_hash)
        
        async with client:
            matches = []
            try:
                async for dlg in client.iter_dialogs():
                    ent = dlg.entity
                    title = getattr(ent, 'title', '') or ''
                    if word.lower() in title.lower():
                        # Store more comprehensive entity information
                        entity_info = {
                            'id': ent.id,
                            'title': title,
                            'type': type(ent).__name__,
                            'access_hash': getattr(ent, 'access_hash', None),
                            'username': getattr(ent, 'username', None)
                        }
                        matches.append(entity_info)
            except Exception as e:
                st.error(f"Error fetching groups: {str(e)}")
            return matches
    
    return asyncio.run(_get_groups())

async def leave_entity_by_info(client, entity_info):
    """Leave entity using comprehensive entity information"""
    try:
        entity_id = entity_info['id']
        entity_type = entity_info['type']
        access_hash = entity_info['access_hash']
        username = entity_info['username']
        
        # Try different methods to get the entity
        entity = None
        
        # Method 1: Try by username if available
        if username:
            try:
                entity = await client.get_entity(username)
            except:
                pass
        
        # Method 2: Try by ID with access_hash if available
        if not entity and access_hash:
            try:
                if entity_type == 'Channel':
                    from telethon.tl.types import PeerChannel
                    entity = await client.get_entity(PeerChannel(entity_id))
                elif entity_type == 'Chat':
                    from telethon.tl.types import PeerChat
                    entity = await client.get_entity(PeerChat(entity_id))
            except:
                pass
        
        # Method 3: Try by just ID as fallback
        if not entity:
            try:
                entity = await client.get_entity(entity_id)
            except:
                pass
        
        if not entity:
            raise Exception(f"Could not resolve entity: {entity_info['title']}")
        
        # Leave the entity
        if entity_type == 'Channel':
            await client(LeaveChannelRequest(entity))
        elif entity_type == 'Chat':
            await client(DeleteChatUserRequest(entity.id, 'me'))
        
        return True
        
    except Exception as e:
        st.error(f"Error leaving {entity_info['title']}: {str(e)}")
        return False

def main():
    if not api_id or not api_hash:
        st.warning("Please enter your API credentials in the sidebar.")
        return

    # Initialize authenticator
    if not st.session_state.authenticator:
        st.session_state.authenticator = TelegramAuthenticator(int(api_id), api_hash)

    # Authentication flow
    if not st.session_state.logged_in:
        st.subheader("🔐 Authentication")
        
        if not st.session_state.phone_entered:
            phone = st.text_input("Enter your phone number (with country code, e.g., +1234567890):")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                send_code_btn = st.button("Send Verification Code", type="primary", disabled=not phone)
            with col2:
                if st.button("❌ Cancel") and 'sending_code' in st.session_state:
                    if 'sending_code' in st.session_state:
                        del st.session_state.sending_code
                    st.rerun()
            
            if send_code_btn and phone:
                st.session_state.sending_code = True
                progress_container = st.container()
                
                with progress_container:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("🔗 Connecting to Telegram...")
                    progress_bar.progress(25)
                    
                    try:
                        # Run authentication with progress updates
                        success, session_result, status = asyncio.run(
                            st.session_state.authenticator.start_auth(phone)
                        )
                        
                        progress_bar.progress(100)
                        status_text.text("✅ Complete!")
                        
                        # Clear progress indicators
                        progress_container.empty()
                        
                        if 'sending_code' in st.session_state:
                            del st.session_state.sending_code
                        
                        if status == "already_authorized":
                            st.session_state.logged_in = True
                            st.session_state.session_string = session_result
                            st.success("Already authenticated!")
                            st.rerun()
                        elif status == "code_sent":
                            st.session_state.phone_entered = True
                            st.session_state.phone = phone
                            st.session_state.code_sent = True
                            st.session_state.temp_session = session_result
                            st.success("✅ Verification code sent! Check your Telegram app.")
                            st.info("⚡ Enter the code IMMEDIATELY - it expires in 2-3 minutes!")
                            st.rerun()
                        else:
                            st.error(f"Failed to send code: {status}")
                            
                    except Exception as e:
                        progress_container.empty()
                        if 'sending_code' in st.session_state:
                            del st.session_state.sending_code
                        st.error(f"Error: {str(e)}")
                        
            elif 'sending_code' in st.session_state:
                st.info("🔄 Sending verification code... This may take up to 30 seconds.")
                if st.button("🛑 Cancel Operation"):
                    if 'sending_code' in st.session_state:
                        del st.session_state.sending_code
                    st.rerun()
        
        elif st.session_state.code_sent and not st.session_state.get('requires_2fa', False):
            st.info("📱 Enter the verification code from your Telegram app")
            st.warning("⚡ IMPORTANT: Enter the code within 2-3 minutes!")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                verification_code = st.text_input(
                    "Verification Code:", 
                    placeholder="12345",
                    max_chars=5,
                    help="Enter the 5-digit code exactly as received"
                )
            
            with col2:
                if st.button("🔄 New Code"):
                    # Reset and get a new code
                    with st.spinner("Sending new code..."):
                        try:
                            success, session_result, status = asyncio.run(
                                st.session_state.authenticator.start_auth(st.session_state.phone)
                            )
                            if status == "code_sent":
                                st.session_state.temp_session = session_result
                                st.success("New code sent!")
                                st.rerun()
                            else:
                                st.error(f"Error sending new code: {status}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            
            if st.button("✅ Verify Code", type="primary") and verification_code:
                if len(verification_code) != 5 or not verification_code.isdigit():
                    st.error("Please enter exactly 5 digits")
                else:
                    with st.spinner("Verifying code..."):
                        try:
                            success, session_result, status = asyncio.run(
                                st.session_state.authenticator.verify_code(
                                    st.session_state.phone, 
                                    verification_code,
                                    st.session_state.temp_session
                                )
                            )
                            
                            if success:
                                st.session_state.logged_in = True
                                st.session_state.session_string = session_result
                                st.success("🎉 Authentication successful!")
                                st.rerun()
                            elif status == "2fa_required":
                                st.session_state.requires_2fa = True
                                st.session_state.temp_session = session_result
                                st.info("🔒 Two-factor authentication required")
                                st.rerun()
                            elif status == "code_expired":
                                st.error("⏰ Code expired! Click 'New Code' to get a fresh one.")
                            elif status == "invalid_code":
                                st.error("❌ Invalid code. Check the number and try again.")
                            else:
                                st.error(f"Verification failed: {status}")
                        except Exception as e:
                            st.error(f"Error during verification: {str(e)}")
            
            # Reset option
            if st.button("🔙 Use Different Phone Number"):
                for key in ['phone_entered', 'code_sent', 'phone', 'temp_session', 'requires_2fa']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        
        elif st.session_state.get('requires_2fa', False):
            st.info("🔒 Your account has Two-Factor Authentication enabled")
            password = st.text_input("2FA Password:", type="password", help="Your Telegram 2FA password")
            
            if st.button("Verify 2FA", type="primary") and password:
                with st.spinner("Verifying 2FA password..."):
                    try:
                        success, session_result, status = asyncio.run(
                            st.session_state.authenticator.verify_2fa(
                                password,
                                st.session_state.temp_session
                            )
                        )
                        
                        if success:
                            st.session_state.logged_in = True
                            st.session_state.session_string = session_result
                            st.success("🎉 2FA verification successful!")
                            st.rerun()
                        else:
                            st.error(f"2FA failed: {status}")
                    except Exception as e:
                        st.error(f"2FA error: {str(e)}")

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
                group_options = {f"{group['title']} ({group['type']})": group 
                               for group in st.session_state.found_groups}
                
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
                            client = TelegramClient(StringSession(st.session_state.session_string), int(api_id), api_hash)
                            
                            async with client:
                                for i, group_name in enumerate(selected_groups):
                                    entity_info = group_options[group_name]
                                    success = await leave_entity_by_info(client, entity_info)
                                    if success:
                                        success_count += 1
                                    progress_bar.progress((i + 1) / len(selected_groups))
                                    await asyncio.sleep(1.5)  # Rate limiting
                        
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
    for key in ['client', 'logged_in', 'phone_entered', 'code_sent', 'phone', 'phone_code_hash', 'session_string', 'found_groups', 'requires_2fa', 'authenticator', 'temp_session']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# Run the main function
if __name__ == "__main__":
    main() 