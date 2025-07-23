"""
Gmail API authentication module
"""

import os
import pickle
import platform
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import service_account
from googleapiclient.discovery import build

from .config import Config


class GmailAuth:
    """Handle Gmail API authentication"""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    def __init__(self, config: Config):
        self.config = config
        self.service = None
    
    def _is_headless_environment(self) -> bool:
        """Detect if running in a headless environment"""
        # Check for SSH connection
        if os.environ.get('SSH_CLIENT') or os.environ.get('SSH_TTY'):
            return True
        
        # Check for DISPLAY variable on Linux systems (not macOS)
        if os.name == 'posix' and platform.system() == 'Linux' and not os.environ.get('DISPLAY'):
            return True
        
        # Check for common headless indicators
        if os.environ.get('CI') or os.environ.get('GITHUB_ACTIONS'):
            return True
        
        # Check if we're in a Docker container
        if os.path.exists('/.dockerenv'):
            return True
        
        return False
    
    def authenticate(self):
        """Authenticate and build Gmail service"""
        creds = None
        
        # Try to load existing token
        token_file = self.config.auth.cached_auth_token
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    if not self.config.quiet:
                        print(f"Failed to refresh token: {e}")
                    creds = None
            
            if not creds:
                creds = self._get_new_credentials()
            
            # Save the credentials for the next run
            os.makedirs(os.path.dirname(token_file), exist_ok=True)
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        # Build the Gmail service
        self.service = build('gmail', 'v1', credentials=creds)
        return self.service
    
    def _get_new_credentials(self) -> Credentials:
        """Get new credentials using available authentication methods"""
        # Try service account first
        if self.config.auth.auth_token:
            return self._authenticate_service_account()
        
        # Try OAuth2 credentials
        credentials_file = self.config.auth.credentials
        
        if credentials_file and os.path.exists(credentials_file):
            return self._authenticate_oauth2(credentials_file)
        
        raise Exception(
            "No valid authentication method found. Please provide either:\n"
            "  --credentials <oauth2_credentials.json>\n"
            "  --auth-token <service_account.json>"
        )
    
    def _authenticate_service_account(self) -> Credentials:
        """Authenticate using service account"""
        service_account_file = self.config.auth.auth_token
        
        if not os.path.exists(service_account_file):
            raise Exception(f"Service account file not found: {service_account_file}")
        
        creds = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=self.SCOPES
        )
        
        return creds
    
    def _authenticate_oauth2(self, credentials_file: str) -> Credentials:
        """Authenticate using OAuth2 flow"""
        if not os.path.exists(credentials_file):
            raise Exception(f"Credentials file not found: {credentials_file}")
        
        flow = InstalledAppFlow.from_client_secrets_file(
            credentials_file, self.SCOPES
        )
        
        # Auto-detect headless environment and use appropriate auth method
        if self._is_headless_environment():
            if not self.config.quiet:
                print("Headless environment detected - using console-based authentication")
            creds = flow.run_console()
        else:
            # Use local server for environments with browser access
            creds = flow.run_local_server(port=0)
        
        return creds
    
    def get_service(self):
        """Get authenticated Gmail service"""
        if not self.service:
            self.authenticate()
        return self.service