"""
Gmail client for fetching and filtering emails
"""

import re
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Generator
from dateutil.parser import parse as parse_date

from .config import Config
from .auth import GmailAuth


class GmailClient:
    """Gmail client for fetching and filtering emails"""
    
    def __init__(self, config: Config):
        self.config = config
        self.auth = GmailAuth(config)
        self.service = None
    
    def connect(self):
        """Connect to Gmail API"""
        self.service = self.auth.authenticate()
        return self.service
    
    def build_query(self) -> str:
        """Build Gmail search query from filters"""
        query_parts = []
        
        # Start with user-provided query
        if self.config.filters.query:
            query_parts.append(f"({self.config.filters.query})")
        
        # Add individual filters
        if self.config.filters.from_email:
            query_parts.append(f"from:{self.config.filters.from_email}")
        
        if self.config.filters.to:
            query_parts.append(f"to:{self.config.filters.to}")
        
        if self.config.filters.subject:
            # Escape special characters in subject
            subject = self.config.filters.subject.replace('"', '\\"')
            query_parts.append(f'subject:"{subject}"')
        
        if self.config.filters.has_attachment:
            query_parts.append("has:attachment")
        
        if self.config.filters.unread_only:
            query_parts.append("is:unread")
        
        # Add label filters
        for label in self.config.filters.labels:
            query_parts.append(f"label:{label}")
        
        # Add date filter
        if self.config.filters.since:
            try:
                # Parse the date and format it for Gmail
                since_date = parse_date(self.config.filters.since)
                formatted_date = since_date.strftime("%Y/%m/%d")
                query_parts.append(f"after:{formatted_date}")
            except Exception as e:
                if not self.config.quiet:
                    print(f"Warning: Invalid date format for --since: {e}")
        
        query = " ".join(query_parts) if query_parts else ""
        
        if self.config.verbose:
            print(f"Gmail query: {query}")
        
        return query
    
    def list_messages(self, query: str = "", page_token: str = None, max_results: int = None) -> Dict[str, Any]:
        """List messages matching the query"""
        if not self.service:
            self.connect()
        
        try:
            result = self.service.users().messages().list(
                userId='me',
                q=query,
                pageToken=page_token,
                maxResults=max_results or self.config.monitoring.batch_size
            ).execute()
            
            return result
            
        except Exception as e:
            if not self.config.quiet:
                print(f"Error listing messages: {e}")
            return {'messages': []}
    
    def get_message(self, message_id: str, format: str = 'full') -> Optional[Dict[str, Any]]:
        """Get a specific message by ID"""
        if not self.service:
            self.connect()
        
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format=format
            ).execute()
            
            return message
            
        except Exception as e:
            if not self.config.quiet:
                print(f"Error getting message {message_id}: {e}")
            return None
    
    def get_history(self, start_history_id: str, max_results: int = None) -> Dict[str, Any]:
        """Get history of changes since a specific history ID"""
        if not self.service:
            self.connect()
        
        try:
            result = self.service.users().history().list(
                userId='me',
                startHistoryId=start_history_id,
                maxResults=max_results or self.config.monitoring.batch_size,
                historyTypes=['messageAdded']
            ).execute()
            
            return result
            
        except Exception as e:
            if not self.config.quiet:
                print(f"Error getting history: {e}")
            return {'history': []}
    
    def get_profile(self) -> Optional[Dict[str, Any]]:
        """Get user profile information"""
        if not self.service:
            self.connect()
        
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            return profile
            
        except Exception as e:
            if not self.config.quiet:
                print(f"Error getting profile: {e}")
            return None
    
    def parse_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a Gmail message into a structured format"""
        parsed = {
            'id': message['id'],
            'threadId': message['threadId'],
            'labelIds': message.get('labelIds', []),
            'snippet': message.get('snippet', ''),
            'historyId': message.get('historyId'),
            'internalDate': message.get('internalDate'),
            'sizeEstimate': message.get('sizeEstimate')
        }
        
        # Parse timestamp
        if 'internalDate' in message:
            timestamp = int(message['internalDate']) / 1000
            parsed['timestamp'] = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
        
        # Parse headers
        headers = {}
        payload = message.get('payload', {})
        
        for header in payload.get('headers', []):
            name = header['name'].lower()
            value = header['value']
            headers[name] = value
        
        # Extract common fields from headers
        parsed['subject'] = headers.get('subject', '')
        parsed['from'] = self._parse_email_address(headers.get('from', ''))
        parsed['to'] = self._parse_email_addresses(headers.get('to', ''))
        parsed['cc'] = self._parse_email_addresses(headers.get('cc', ''))
        parsed['bcc'] = self._parse_email_addresses(headers.get('bcc', ''))
        parsed['date'] = headers.get('date', '')
        parsed['message-id'] = headers.get('message-id', '')
        
        # Store all headers if requested
        if self.config.output.include_body or 'headers' in (self.config.output.fields or []):
            parsed['headers'] = headers
        
        # Extract body if requested
        if self.config.output.include_body:
            parsed['body'] = self._extract_body(payload)
        
        # Extract attachment info if requested
        if self.config.output.include_attachments:
            parsed['attachments'] = self._extract_attachments(payload)
        
        # Convert label IDs to label names
        parsed['labels'] = self._convert_label_ids(parsed['labelIds'])
        
        return parsed
    
    def _parse_email_address(self, email_str: str) -> Dict[str, str]:
        """Parse email address string into name and email components"""
        if not email_str:
            return {'name': '', 'email': ''}
        
        # Try to parse "Name <email@domain.com>" format
        match = re.match(r'^(.+?)\s*<(.+?)>$', email_str.strip())
        if match:
            name = match.group(1).strip().strip('"')
            email = match.group(2).strip()
            return {'name': name, 'email': email}
        
        # If no match, assume it's just an email address
        return {'name': '', 'email': email_str.strip()}
    
    def _parse_email_addresses(self, email_str: str) -> List[Dict[str, str]]:
        """Parse multiple email addresses"""
        if not email_str:
            return []
        
        # Split by comma and parse each address
        addresses = []
        for addr in email_str.split(','):
            parsed = self._parse_email_address(addr.strip())
            if parsed['email']:
                addresses.append(parsed)
        
        return addresses
    
    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Extract email body from payload"""
        body = ""
        
        def extract_text_from_part(part):
            part_body = ""
            if part.get('mimeType') == 'text/plain':
                if 'data' in part.get('body', {}):
                    import base64
                    data = part['body']['data']
                    # Add padding if needed
                    data += '=' * (4 - len(data) % 4)
                    try:
                        part_body = base64.urlsafe_b64decode(data).decode('utf-8')
                    except Exception:
                        part_body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif part.get('mimeType') == 'text/html' and not part_body:
                # Fallback to HTML if no plain text
                if 'data' in part.get('body', {}):
                    import base64
                    data = part['body']['data']
                    data += '=' * (4 - len(data) % 4)
                    try:
                        html_body = base64.urlsafe_b64decode(data).decode('utf-8')
                        # Simple HTML to text conversion
                        import html
                        part_body = html.unescape(re.sub(r'<[^>]+>', '', html_body))
                    except Exception:
                        pass
            
            return part_body
        
        # Handle multipart messages
        if 'parts' in payload:
            for part in payload['parts']:
                part_body = extract_text_from_part(part)
                if part_body:
                    body += part_body + "\n"
                
                # Recursively handle nested parts
                if 'parts' in part:
                    for nested_part in part['parts']:
                        nested_body = extract_text_from_part(nested_part)
                        if nested_body:
                            body += nested_body + "\n"
        else:
            # Single part message
            body = extract_text_from_part(payload)
        
        # Truncate if too long
        if len(body) > self.config.output.max_body_length:
            body = body[:self.config.output.max_body_length] + "..."
        
        return body.strip()
    
    def _extract_attachments(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract attachment information from payload"""
        attachments = []
        
        def extract_from_part(part):
            if part.get('filename'):
                attachment = {
                    'filename': part['filename'],
                    'mimeType': part.get('mimeType', ''),
                    'size': part.get('body', {}).get('size', 0)
                }
                
                if 'attachmentId' in part.get('body', {}):
                    attachment['attachmentId'] = part['body']['attachmentId']
                
                attachments.append(attachment)
            
            # Check nested parts
            if 'parts' in part:
                for nested_part in part['parts']:
                    extract_from_part(nested_part)
        
        # Handle multipart messages
        if 'parts' in payload:
            for part in payload['parts']:
                extract_from_part(part)
        else:
            extract_from_part(payload)
        
        return attachments
    
    def _convert_label_ids(self, label_ids: List[str]) -> List[str]:
        """Convert label IDs to human-readable names"""
        # Basic conversion for common labels
        label_mapping = {
            'INBOX': 'INBOX',
            'SENT': 'SENT',
            'DRAFT': 'DRAFT',
            'SPAM': 'SPAM',
            'TRASH': 'TRASH',
            'UNREAD': 'UNREAD',
            'STARRED': 'STARRED',
            'IMPORTANT': 'IMPORTANT'
        }
        
        return [label_mapping.get(label_id, label_id) for label_id in label_ids]
    
    def watch_messages(self, query: str = "") -> Generator[Dict[str, Any], None, None]:
        """Watch for new messages matching the query"""
        if not self.service:
            self.connect()
        
        last_history_id = None
        processed_messages = set()
        
        while True:
            try:
                if last_history_id:
                    # Use history API for incremental updates
                    history = self.get_history(last_history_id)
                    
                    for history_item in history.get('history', []):
                        for message_added in history_item.get('messagesAdded', []):
                            message_id = message_added['message']['id']
                            
                            if message_id not in processed_messages:
                                message = self.get_message(message_id)
                                if message and self._message_matches_query(message, query):
                                    processed_messages.add(message_id)
                                    yield self.parse_message(message)
                    
                    if 'historyId' in history:
                        last_history_id = history['historyId']
                else:
                    # Initial fetch
                    result = self.list_messages(query)
                    
                    for message_info in result.get('messages', []):
                        message_id = message_info['id']
                        
                        if message_id not in processed_messages:
                            message = self.get_message(message_id)
                            if message:
                                processed_messages.add(message_id)
                                yield self.parse_message(message)
                    
                    # Get profile to establish initial history ID
                    profile = self.get_profile()
                    if profile:
                        last_history_id = profile.get('historyId')
                
                # Clean up old processed messages to prevent memory bloat
                if len(processed_messages) > 10000:
                    processed_messages = set(list(processed_messages)[-5000:])
                
                time.sleep(self.config.monitoring.poll_interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                if not self.config.quiet:
                    print(f"Error in watch loop: {e}")
                time.sleep(self.config.monitoring.poll_interval)
    
    def _message_matches_query(self, message: Dict[str, Any], query: str) -> bool:
        """Check if a message matches the given query (simplified check)"""
        # This is a simplified implementation
        # In practice, you'd want to implement proper Gmail query parsing
        if not query:
            return True
        
        # For now, just return True and let Gmail API handle the filtering
        return True