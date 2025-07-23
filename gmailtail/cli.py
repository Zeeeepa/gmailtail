#!/usr/bin/env python3
"""
Command line interface for gmailtail
"""

import os
import sys
import click
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from . import __version__
from .config import Config
from .gmailtail import GmailTail


@click.command()
@click.version_option(version=__version__)

# Authentication options
@click.option('--credentials', type=click.Path(exists=True),
              help='OAuth2 credentials file path')
@click.option('--auth-token', type=click.Path(exists=True),
              help='Service account authentication token file path')
@click.option('--cached-auth-token', type=click.Path(),
              default=lambda: os.path.expanduser('~/.gmailtail/tokens'),
              help='Cached authentication token file path')
@click.option('--force-headless', is_flag=True,
              help='Force headless authentication mode (console-based)')
@click.option('--ignore-token', is_flag=True,
              help='Ignore cached authentication token and force re-authentication')

# Filter and query options
@click.option('--query', help='Gmail search query syntax')
@click.option('--label', multiple=True, help='Filter by label (can be used multiple times)')
@click.option('--from', 'from_email', help='Filter by sender email')
@click.option('--to', help='Filter by recipient email')
@click.option('--subject', help='Filter by subject pattern (regex supported)')
@click.option('--has-attachment', is_flag=True, help='Only monitor emails with attachments')
@click.option('--unread-only', is_flag=True, help='Only monitor unread emails')
@click.option('--since', help='Start from specified datetime (ISO 8601 format)')

# Checkpoint options
@click.option('--checkpoint-file', type=click.Path(),
              default=lambda: os.path.expanduser('~/.gmailtail/checkpoint'),
              help='Checkpoint file path')
@click.option('--checkpoint-interval', type=int, default=60,
              help='Checkpoint save interval in seconds')
@click.option('--resume', is_flag=True, help='Resume from last checkpoint')
@click.option('--reset-checkpoint', is_flag=True, help='Reset checkpoint and start from current time')

# Output format options
@click.option('--format', 'output_format', 
              type=click.Choice(['json', 'json-lines', 'compact']), 
              default='json', help='Output format')
@click.option('--fields', help='Output fields list (comma-separated)')
@click.option('--include-body', is_flag=True, help='Include email body')
@click.option('--include-attachments', is_flag=True, help='Include attachment information')
@click.option('--max-body-length', type=int,
              help='Maximum email body length in characters')
@click.option('--pretty', is_flag=True, help='Pretty-print JSON output')

# Monitoring options
@click.option('--poll-interval', type=int, default=30,
              help='Polling interval in seconds')
@click.option('--batch-size', type=int, default=10,
              help='Number of emails to fetch per batch')
@click.option('--tail', '-t', is_flag=True, help='Continuous monitoring mode (like tail -f)')
@click.option('--once', is_flag=True, help='Run once, do not continue monitoring')
@click.option('--max-messages', type=int, help='Maximum number of messages to process')

# Cache options
@click.option('--no-cache', is_flag=True, help='Disable caching entirely')
@click.option('--cache-file', type=click.Path(), help='Cache database file path')
@click.option('--cache-max-age-days', type=int, default=30, help='Maximum cache age in days')
@click.option('--clear-cache', is_flag=True, help='Clear cache before running')

# Other options
@click.option('--verbose', '-v', is_flag=True, help='Verbose output mode')
@click.option('--quiet', is_flag=True, help='Quiet mode, only output email JSON')
@click.option('--log-file', type=click.Path(), help='Log file path')
@click.option('--config-file', type=click.Path(exists=True), help='Configuration file path')
@click.option('--dry-run', is_flag=True, help='Simulate run without actual processing')
@click.option('--repl', '-i', is_flag=True, help='Enter interactive REPL mode')

def main(**kwargs):
    """
    gmailtail - Monitor Gmail messages and output them as JSON
    
    Examples:
    
        # Monitor all new emails
        gmailtail --tail
        
        # Monitor emails from specific sender
        gmailtail --from "noreply@github.com" --tail
        
        # Monitor with query and include body
        gmailtail --query "subject:alert OR subject:error" --include-body --tail
        
        # Resume from checkpoint
        gmailtail --resume --tail
    """
    try:
        # Load configuration
        config = Config.from_cli_args(**kwargs)
        
        # Check if REPL mode is requested
        if kwargs.get('repl', False):
            from .repl import GmailTailREPL
            repl = GmailTailREPL(config)
            repl.run()
        else:
            # Initialize and run gmailtail
            gmailtail = GmailTail(config)
            gmailtail.run()
        
    except KeyboardInterrupt:
        if not config.quiet:
            click.echo("\nStopped by user", err=True)
        sys.exit(0)
    except Exception as e:
        if not kwargs.get('quiet', False):
            click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()