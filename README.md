# gmailtail

A command-line tool to monitor Gmail messages and output them as JSON, designed for automation, monitoring, and integration with other tools.

Why: [My Blog](https://me.0xffff.me/gmailtail.html)

## Features

-  **Real-time monitoring** - Continuous monitoring of new emails with `--tail` mode
-  **Flexible filtering** - Filter by sender, subject, labels, attachments, and more
-  **Checkpoint support** - Resume monitoring from where you left off
-  **Multiple output formats** - JSON, JSON Lines, and compact formats
-  **Configuration files** - YAML configuration for complex setups
-  **Gmail search syntax** - Full support for Gmail's powerful search queries
-  **Easy authentication** - Support for OAuth2 and service accounts
-  **Interactive REPL mode** - Interactive shell for exploring and querying emails

## Quick Start

1. **Install using uv (recommended):**
   ```bash
   # Install uv if you haven't already
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Clone and setup the project
   git clone https://github.com/c4pt0r/gmailtail.git
   cd gmailtail
   uv sync
   ```

2. **Set up Google API credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Gmail API
   - Create credentials (OAuth 2.0 Client ID for desktop applications)
   - Download the credentials JSON file

3. **Run gmailtail:**
   ```bash
   # Start in tail mode (continuous monitoring)
   uv run gmailtail --credentials credentials.json --tail
   
   # Or start in interactive REPL mode
   uv run gmailtail --credentials credentials.json --repl
   ```

## Installation

### Using uv (recommended)
```bash
# Clone the repository
git clone https://github.com/c4pt0r/gmailtail.git
cd gmailtail

# Install dependencies and create virtual environment
uv sync

# Install in development mode
uv pip install -e .
```


## Usage Examples

### Basic monitoring
```bash
# Monitor all new emails
gmailtail --tail

# Monitor emails from specific sender
gmailtail --from "noreply@github.com" --tail

# Monitor with Gmail search query
gmailtail --query "subject:alert OR subject:error" --tail
```

### Filtering options
```bash
# Monitor unread emails only
gmailtail --unread-only --tail

# Monitor emails with attachments
gmailtail --has-attachment --include-attachments --tail

# Monitor specific labels
gmailtail --label important --label work --tail

# Monitor since specific date
gmailtail --since "2025-01-01T00:00:00Z" --tail
```

### Output formats
```bash
# Pretty JSON output
gmailtail --format json --pretty --tail

# JSON Lines format (one JSON per line)
gmailtail --format json-lines --tail

# Compact format
gmailtail --format compact --tail

# Include email body
gmailtail --include-body --max-body-length 500 --tail

# Custom fields only
gmailtail --fields "id,subject,from,timestamp" --tail
```

### Checkpoint management
```bash
# Resume from last checkpoint
gmailtail --resume --tail

# Reset checkpoint and start fresh
gmailtail --reset-checkpoint --tail

# Custom checkpoint file
gmailtail --checkpoint-file ./my-checkpoint --tail
```

### Configuration file
```bash
# Use configuration file
gmailtail --config-file gmailtail.yaml

# Example configuration file
cp gmailtail.yaml.example gmailtail.yaml
# Edit gmailtail.yaml as needed
gmailtail --config-file gmailtail.yaml
```

### Advanced usage with jq

```bash
# Extract only sender email and subject
gmailtail --format json-lines --tail | jq -r '.from.email + ": " + .subject'

# Filter emails by specific sender and get only timestamps
gmailtail --format json-lines --tail | jq -r 'select(.from.email == "noreply@github.com") | .timestamp'

# Count emails by sender
gmailtail --format json-lines --once | jq -r '.from.email' | sort | uniq -c | sort -nr

# Get all unique labels across emails
gmailtail --format json-lines --once | jq -r '.labels[]?' | sort | uniq

# Extract emails with attachments and show attachment info
gmailtail --format json-lines --include-attachments --tail | jq 'select(.attachments | length > 0) | {subject, from: .from.email, attachments: [.attachments[].filename]}'

# Monitor for urgent emails and send desktop notifications (macOS)
gmailtail --query "label:urgent OR subject:urgent" --format json-lines --tail | jq -r '.subject' | while read subject; do osascript -e "display notification \"$subject\" with title \"Urgent Email\""; done

# Extract email body text and save to files
gmailtail --include-body --format json-lines --once | jq -r '"\(.id).txt|\(.body // .snippet)"' | while IFS='|' read filename content; do echo "$content" > "$filename"; done

# Monitor GitHub notifications and extract PR/issue numbers
gmailtail --from "notifications@github.com" --format json-lines --tail | jq -r 'select(.subject | test("Pull Request|Issue")) | .subject | capture(".*#(?<number>[0-9]+).*") | .number'

# Create a summary of daily email activity
gmailtail --since "$(date -d 'today' '+%Y-%m-%dT00:00:00Z')" --format json-lines --once | jq -r '[group_by(.from.email) | .[] | {sender: .[0].from.email, count: length}] | sort_by(.count) | reverse'

# Monitor for emails with specific keywords in body and alert
gmailtail --include-body --format json-lines --tail | jq -r 'select(.body | test("error|fail|alert"; "i")) | "ALERT: \(.from.email) - \(.subject)"'

# Extract and format meeting invitations
gmailtail --query "has:attachment filename:ics" --include-attachments --format json-lines --tail | jq '{meeting: .subject, organizer: .from.email, time: .timestamp, location: (.body | capture("Location:.*(?<loc>.*)")? | .loc // "N/A")}'
```

## Interactive REPL Mode

The REPL (Read-Eval-Print Loop) mode provides an interactive shell for exploring and querying your Gmail account. This is perfect for ad-hoc email searches, debugging filters, and exploring your email data.

### Starting REPL Mode

```bash
# Start REPL with OAuth2 credentials
gmailtail --credentials credentials.json --repl

# Start REPL with configuration file
gmailtail --config-file gmailtail.yaml --repl
```

### REPL Commands

Once in REPL mode, you can use these commands:

#### Basic Email Operations
```
# Show unread emails from INBOX
gmailtail> unread

# Show 5 unread emails from a specific label
gmailtail> unread important 5

# Show recent emails from INBOX
gmailtail> tail

# Show 10 recent emails from a specific label
gmailtail> tail work 10

# Execute a Gmail search query
gmailtail> query from:noreply@github.com subject:pull
```

#### Account Information
```
# Show your Gmail profile info
gmailtail> profile

# List all available labels
gmailtail> labels

# Show current configuration
gmailtail> config
```

#### Navigation
```
# Show help for all commands
gmailtail> help

# Exit REPL
gmailtail> exit
# or
gmailtail> quit
# or press Ctrl+D
```

### REPL Examples

```bash
$ gmailtail --credentials credentials.json --repl

Welcome to gmailtail REPL mode. Type 'help' for commands.

gmailtail> unread important 3

=== Found 3 unread emails in important ===

 1. [2025-01-15 10:30:25] GitHub <noreply@github.com>     | New pull request assigned to you
 2. [2025-01-15 09:45:12] JIRA <noreply@jira.com>        | Issue updated: Bug in login system
 3. [2025-01-15 08:20:30] Slack <noreply@slack.com>      | You have 5 new mentions

gmailtail> query subject:alert OR subject:error

=== Found 2 messages ===

 1. [2025-01-15 11:15:00] Monitor <alerts@monitor.com>    | Database connection alert
 2. [2025-01-15 10:00:00] System <system@server.com>     | Error in backup process

gmailtail> profile
Email: john.doe@example.com
Messages Total: 15247
Threads Total: 8932
History ID: 1234567890

gmailtail> labels
Available labels:
  INBOX (INBOX)
  SENT (SENT)
  DRAFT (DRAFT)
  important (Label_1)
  work (Label_2)
  personal (Label_3)
  
gmailtail> exit
Goodbye!
```

### REPL Output Format

The REPL uses a human-readable compact format that shows:
- **Timestamp**: When the email was received
- **Sender**: Name (if available) or email address
- **Subject**: Email subject (truncated if too long)

This format is optimized for quick scanning and readability in the terminal.

## Command Line Options

### Authentication
- `--credentials PATH` - OAuth2 credentials file path
- `--auth-token PATH` - Service account authentication token file path
- `--cached-auth-token PATH` - Cached authentication token file path (default: `~/.gmailtail/tokens`)

### Filtering
- `--query QUERY` - Gmail search query syntax
- `--from EMAIL` - Filter by sender email
- `--to EMAIL` - Filter by recipient email
- `--subject PATTERN` - Filter by subject (regex supported)
- `--label LABEL` - Filter by label (can be used multiple times)
- `--has-attachment` - Only emails with attachments
- `--unread-only` - Only unread emails
- `--since DATETIME` - Start from specified time (ISO 8601)

### Output
- `--format FORMAT` - Output format: json, json-lines, compact
- `--fields FIELDS` - Comma-separated list of fields to include
- `--include-body` - Include email body in output
- `--include-attachments` - Include attachment information
- `--max-body-length N` - Maximum body length (default: 1000)
- `--pretty` - Pretty-print JSON output

### Monitoring
- `--tail, -f` - Continuous monitoring (like `tail -f`)
- `--repl` - Start interactive REPL mode
- `--once` - Run once and exit
- `--poll-interval N` - Polling interval in seconds (default: 30)
- `--batch-size N` - Messages per batch (default: 10)
- `--max-messages N` - Maximum messages to process

### Checkpoint
- `--checkpoint-file PATH` - Checkpoint file path
- `--checkpoint-interval N` - Save interval in seconds (default: 60)
- `--resume` - Resume from last checkpoint
- `--reset-checkpoint` - Reset checkpoint

### Other
- `--verbose, -v` - Verbose output mode
- `--quiet` - Quiet mode, only output email JSON
- `--log-file PATH` - Log file path
- `--config-file PATH` - Configuration file path
- `--dry-run` - Simulate run without actual processing

## Output Format

### JSON Format
```json
{
  "id": "18234567890abcdef",
  "threadId": "18234567890abcdef",
  "timestamp": "2025-07-01T10:30:00Z",
  "subject": "GitHub notification",
  "from": {
    "name": "GitHub",
    "email": "noreply@github.com"
  },
  "to": [
    {
      "name": "John Doe",
      "email": "john@example.com"
    }
  ],
  "labels": ["INBOX", "UNREAD"],
  "snippet": "You have a new pull request...",
  "body": "Full email body here...",
  "attachments": [
    {
      "filename": "report.pdf",
      "mimeType": "application/pdf",
      "size": 1024
    }
  ]
}
```

## Use Cases

- **Monitoring systems** - Alert on specific email patterns
- **Automation workflows** - Trigger actions based on email content
- **Data analysis** - Collect email metrics and statistics
- **Integration** - Feed email data into other tools and systems
- **Backup** - Archive important emails in structured format
- **CI/CD** - Monitor build notifications and alerts
- **Interactive exploration** - Use REPL mode for ad-hoc email searches and account exploration
- **Filter debugging** - Test and refine Gmail search queries interactively

## Configuration File

Create a `gmailtail.yaml` file for complex configurations:

```yaml
# Authentication settings
auth:
  credentials_file: ~/.config/gmailtail/credentials.json
  # auth_token: ~/.config/gmailtail/service-account.json
  cached_auth_token: ~/.config/gmailtail/tokens

# Email filtering settings
filters:
  query: "label:important"
  # from: "noreply@github.com"
  # to: "me@example.com"
  # subject: "alert|error|warning"
  # labels: ["important", "inbox"]
  # has_attachment: true
  unread_only: true
  # since: "2025-01-01T00:00:00Z"

# Output formatting
output:
  format: json-lines
  include_body: true
  include_attachments: true
  max_body_length: 500
  pretty: false
  # fields: ["id", "subject", "from", "timestamp", "labels"]

# Monitoring behavior
monitoring:
  poll_interval: 60
  batch_size: 20
  tail: true
  # max_messages: 1000

# Checkpoint settings
checkpoint:
  checkpoint_file: ~/.config/gmailtail/checkpoint
  checkpoint_interval: 120
  resume: true

# Logging
verbose: false
quiet: false
# log_file: ~/.config/gmailtail/gmailtail.log
```

## Authentication Setup

### OAuth2 (Recommended for personal use)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable Gmail API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Choose "Desktop application"
6. Download the JSON file
7. Use with `--credentials path/to/credentials.json`

### Service Account (For server/automated environments)

1. In Google Cloud Console, go to "Credentials"
2. Create "Service Account"
3. Download the JSON key file
4. Use with `--service-account path/to/service-account.json`

Note: Service accounts need domain-wide delegation for Gmail access.

## Development

### Setup development environment
```bash
# Clone the repository
git clone https://github.com/c4pt0r/gmailtail.git
cd gmailtail

# Install with development dependencies
uv sync --extra dev

# Install pre-commit hooks
uv run pre-commit install
```

### Running tests
```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=gmailtail

# Run specific test file
uv run pytest tests/test_config.py
```

### Code formatting and linting
```bash
# Format code with black
uv run black .

# Sort imports with isort
uv run isort .

# Run flake8 linting
uv run flake8 gmailtail/

# Run mypy type checking
uv run mypy gmailtail/
```



## License

MIT License - see LICENSE file for details.

