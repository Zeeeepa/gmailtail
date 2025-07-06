"""
Interactive REPL mode for gmailtail
"""

import cmd
import shlex
import sys
from typing import List, Optional, Dict, Any

from .config import Config
from .gmail_client import GmailClient
from .formatter import OutputFormatter
from .checkpoint import Checkpoint


class GmailTailREPL(cmd.Cmd):
    """Interactive REPL for gmailtail"""
    
    intro = "Welcome to gmailtail REPL mode. Type 'help' for commands."
    prompt = "gmailtail> "
    
    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.client = GmailClient(config)
        self.formatter = OutputFormatter(config)
        self.checkpoint = None
        
        # Override output format for REPL to be human-readable
        self.config.output.format = 'compact'
        
    def run(self):
        """Start the REPL"""
        try:
            # Ensure directories exist
            self.config.ensure_directories()
            
            # Connect to Gmail
            print("Connecting to Gmail API...")
            self.client.connect()
            print("Connected successfully")
            
            # Initialize checkpoint
            self.checkpoint = Checkpoint(self.config)
            
            # Start command loop
            self.cmdloop()
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    def do_query(self, args: str):
        """Execute a Gmail query
        Usage: query <query-string>
        Example: query from:noreply@github.com subject:alert
        """
        if not args.strip():
            print("Error: Query string is required")
            return
        
        try:
            # Execute query
            result = self.client.list_messages(
                query=args.strip(),
                max_results=self.config.monitoring.batch_size
            )
            
            messages = result.get('messages', [])
            if messages:
                print(f"\n=== Found {len(messages)} messages ===")
                print()
                
                # Process and display messages
                for i, message_info in enumerate(messages, 1):
                    message = self.client.get_message(message_info['id'])
                    if message:
                        parsed_message = self.client.parse_message(message)
                        print(f"{i:2d}. ", end="")
                        self.formatter.output_message(parsed_message)
                print()
            else:
                print("No messages found for this query")
                    
        except Exception as e:
            print(f"Error executing query: {e}")
    
    def do_tail(self, args: str):
        """Tail emails from a mailbox or label
        Usage: tail [mailbox/label] [num_of_emails]
        Example: tail INBOX 10
        Example: tail important 5
        """
        parts = shlex.split(args) if args else []
        
        # Parse arguments
        label = "INBOX"
        num_emails = 10
        
        if len(parts) >= 1:
            label = parts[0]
        if len(parts) >= 2:
            try:
                num_emails = int(parts[1])
            except ValueError:
                print("Error: Number of emails must be an integer")
                return
        
        try:
            # Build query for the label
            query = f"in:{label}"
            
            # Get messages
            result = self.client.list_messages(
                query=query,
                max_results=num_emails
            )
            
            messages = result.get('messages', [])
            if messages:
                print(f"\n=== Showing {len(messages)} recent emails from {label} ===")
                print()
                
                # Process and display messages
                for i, message_info in enumerate(messages, 1):
                    message = self.client.get_message(message_info['id'])
                    if message:
                        parsed_message = self.client.parse_message(message)
                        print(f"{i:2d}. ", end="")
                        self.formatter.output_message(parsed_message)
                print()
            else:
                print(f"No emails found in {label}")
                    
        except Exception as e:
            print(f"Error tailing {label}: {e}")
    
    def do_unread(self, args: str):
        """Show unread emails from a label
        Usage: unread [label] [limit]
        Example: unread
        Example: unread important
        Example: unread INBOX 5
        """
        parts = shlex.split(args) if args else []
        
        # Parse arguments
        label = "INBOX"
        limit = self.config.monitoring.batch_size
        
        if len(parts) >= 1:
            label = parts[0]
        if len(parts) >= 2:
            try:
                limit = int(parts[1])
            except ValueError:
                print("Error: Limit must be an integer")
                return
        
        try:
            # Build query for unread emails in the label
            query = f"in:{label} is:unread"
            
            # Get messages
            result = self.client.list_messages(
                query=query,
                max_results=limit
            )
            
            messages = result.get('messages', [])
            if messages:
                print(f"\n=== Found {len(messages)} unread emails in {label} ===")
                print()
                
                # Process and display messages
                for i, message_info in enumerate(messages, 1):
                    message = self.client.get_message(message_info['id'])
                    if message:
                        parsed_message = self.client.parse_message(message)
                        print(f"{i:2d}. ", end="")
                        self.formatter.output_message(parsed_message)
                print()
            else:
                print(f"No unread emails found in {label}")
                    
        except Exception as e:
            print(f"Error getting unread emails from {label}: {e}")
    
    def do_labels(self, args: str):
        """List all available labels
        Usage: labels
        """
        try:
            labels = self.client.service.users().labels().list(userId='me').execute()
            
            print("Available labels:")
            for label in labels.get('labels', []):
                label_name = label['name']
                label_id = label['id']
                print(f"  {label_name} ({label_id})")
                
        except Exception as e:
            print(f"Error getting labels: {e}")
    
    def do_profile(self, args: str):
        """Show Gmail profile information
        Usage: profile
        """
        try:
            profile = self.client.get_profile()
            if profile:
                print(f"Email: {profile.get('emailAddress', 'N/A')}")
                print(f"Messages Total: {profile.get('messagesTotal', 'N/A')}")
                print(f"Threads Total: {profile.get('threadsTotal', 'N/A')}")
                print(f"History ID: {profile.get('historyId', 'N/A')}")
            else:
                print("Could not retrieve profile information")
                
        except Exception as e:
            print(f"Error getting profile: {e}")
    
    def do_config(self, args: str):
        """Show current configuration
        Usage: config
        """
        print("Current configuration:")
        print(f"  Batch size: {self.config.monitoring.batch_size}")
        print(f"  Poll interval: {self.config.monitoring.poll_interval}")
        print(f"  Output format: {self.config.output.format}")
        print(f"  Include body: {self.config.output.include_body}")
        print(f"  Include attachments: {self.config.output.include_attachments}")
        
        if self.config.filters.query:
            print(f"  Query filter: {self.config.filters.query}")
        if self.config.filters.from_email:
            print(f"  From filter: {self.config.filters.from_email}")
        if self.config.filters.to:
            print(f"  To filter: {self.config.filters.to}")
        if self.config.filters.subject:
            print(f"  Subject filter: {self.config.filters.subject}")
        if self.config.filters.labels:
            print(f"  Label filters: {', '.join(self.config.filters.labels)}")
    
    def do_exit(self, args: str):
        """Exit the REPL
        Usage: exit
        """
        print("Goodbye!")
        return True
    
    def do_quit(self, args: str):
        """Exit the REPL
        Usage: quit
        """
        return self.do_exit(args)
    
    def do_EOF(self, args: str):
        """Handle Ctrl+D"""
        print()
        return self.do_exit(args)
    
    def emptyline(self):
        """Handle empty line input"""
        pass
    
    def default(self, line: str):
        """Handle unknown commands"""
        print(f"Unknown command: {line}")
        print("Type 'help' for available commands")