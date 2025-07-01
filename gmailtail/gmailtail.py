"""
Main gmailtail application
"""

import time
import signal
import sys
from typing import Optional

from .config import Config
from .gmail_client import GmailClient
from .checkpoint import Checkpoint
from .formatter import OutputFormatter


class GmailTail:
    """Main gmailtail application class"""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = GmailClient(config)
        self.formatter = OutputFormatter(config)
        self.checkpoint = None
        self.running = True
        self.message_count = 0
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.formatter.output_info("Shutting down...")
        self.running = False
    
    def run(self):
        """Main run loop"""
        try:
            # Ensure directories exist
            self.config.ensure_directories()
            
            # Connect to Gmail
            self.formatter.output_verbose("Connecting to Gmail API...")
            self.client.connect()
            self.formatter.output_verbose("Connected successfully")
            
            # Initialize checkpoint
            with Checkpoint(self.config) as checkpoint:
                self.checkpoint = checkpoint
                
                # Build query
                query = self.client.build_query()
                self.formatter.output_verbose(f"Using query: {query}")
                
                if self.config.dry_run:
                    self.formatter.output_info("Dry run mode - no emails will be processed")
                    return
                
                # Run monitoring
                if self.config.monitoring.once:
                    self._run_once(query)
                elif self.config.monitoring.tail:
                    self._run_follow(query)
                else:
                    self._run_once(query)
        
        except Exception as e:
            self.formatter.output_error(str(e))
            raise
    
    def _run_once(self, query: str):
        """Run once and exit"""
        self.formatter.output_verbose("Running in single-shot mode")
        
        try:
            # Get messages
            result = self.client.list_messages(
                query=query,
                max_results=self.config.monitoring.batch_size
            )
            
            messages = result.get('messages', [])
            self.formatter.output_verbose(f"Found {len(messages)} messages")
            
            # Process messages
            for message_info in messages:
                if not self.running:
                    break
                
                if (self.config.monitoring.max_messages and 
                    self.message_count >= self.config.monitoring.max_messages):
                    break
                
                self._process_message(message_info['id'])
            
            self.formatter.output_verbose(f"Processed {self.message_count} messages")
            
        except Exception as e:
            self.formatter.output_error(f"Error in single-shot mode: {e}")
            raise
    
    def _run_follow(self, query: str):
        """Run in follow mode (continuous monitoring)"""
        self.formatter.output_verbose("Running in follow mode")
        
        try:
            last_history_id = self.checkpoint.get_last_history_id()
            processed_count = 0
            
            while self.running:
                try:
                    if last_history_id:
                        # Use history API for incremental updates
                        history = self.client.get_history(
                            last_history_id,
                            max_results=self.config.monitoring.batch_size
                        )
                        
                        new_messages = []
                        for history_item in history.get('history', []):
                            for message_added in history_item.get('messagesAdded', []):
                                new_messages.append(message_added['message']['id'])
                        
                        if new_messages:
                            self.formatter.output_verbose(f"Found {len(new_messages)} new messages from history")
                        
                        # Process new messages
                        for message_id in new_messages:
                            if not self.running:
                                break
                            
                            if (self.config.monitoring.max_messages and 
                                self.message_count >= self.config.monitoring.max_messages):
                                self.formatter.output_verbose("Reached maximum message limit")
                                self.running = False
                                break
                            
                            self._process_message(message_id)
                        
                        # Update history ID
                        if 'historyId' in history:
                            last_history_id = history['historyId']
                            self.checkpoint.update_history_id(last_history_id)
                    
                    else:
                        # Initial fetch using list API
                        result = self.client.list_messages(
                            query=query,
                            max_results=self.config.monitoring.batch_size
                        )
                        
                        messages = result.get('messages', [])
                        if messages:
                            self.formatter.output_verbose(f"Initial fetch: {len(messages)} messages")
                        
                        # Process messages in reverse order (oldest first)
                        for message_info in reversed(messages):
                            if not self.running:
                                break
                            
                            if (self.config.monitoring.max_messages and 
                                self.message_count >= self.config.monitoring.max_messages):
                                self.formatter.output_verbose("Reached maximum message limit")
                                self.running = False
                                break
                            
                            self._process_message(message_info['id'])
                        
                        # Get initial history ID from profile
                        profile = self.client.get_profile()
                        if profile and 'historyId' in profile:
                            last_history_id = profile['historyId']
                            self.checkpoint.update_history_id(last_history_id)
                    
                    # Save checkpoint periodically
                    self.checkpoint.save()
                    
                    # Clean up old message IDs
                    self.checkpoint.cleanup_old_message_ids()
                    
                    # Sleep between polls
                    if self.running:
                        time.sleep(self.config.monitoring.poll_interval)
                    
                    processed_count += 1
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.formatter.output_error(f"Error in follow loop: {e}")
                    if self.running:
                        time.sleep(self.config.monitoring.poll_interval)
            
            self.formatter.output_verbose(f"Total processed: {self.message_count} messages")
            
        except Exception as e:
            self.formatter.output_error(f"Error in follow mode: {e}")
            raise
    
    def _process_message(self, message_id: str) -> bool:
        """Process a single message"""
        try:
            # Check if already processed
            if self.checkpoint and self.checkpoint.is_message_processed(message_id):
                self.formatter.output_verbose(f"Skipping already processed message: {message_id}")
                return False
            
            # Fetch full message
            message = self.client.get_message(message_id)
            if not message:
                self.formatter.output_verbose(f"Could not fetch message: {message_id}")
                return False
            
            # Parse message
            parsed_message = self.client.parse_message(message)
            
            # Filter by subject pattern if specified
            if self.config.filters.subject and parsed_message.get('subject'):
                import re
                if not re.search(self.config.filters.subject, parsed_message['subject'], re.IGNORECASE):
                    self.formatter.output_verbose(f"Message filtered out by subject pattern: {message_id}")
                    return False
            
            # Output message
            self.formatter.output_message(parsed_message)
            
            # Update checkpoint
            if self.checkpoint:
                self.checkpoint.add_processed_message(message_id)
                if parsed_message.get('timestamp'):
                    self.checkpoint.update_timestamp(parsed_message['timestamp'])
            
            self.message_count += 1
            self.formatter.output_verbose(f"Processed message {self.message_count}: {message_id}")
            
            return True
            
        except Exception as e:
            self.formatter.output_error(f"Error processing message {message_id}: {e}")
            return False