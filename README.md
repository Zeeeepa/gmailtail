# gmailtail

A command-line tool to monitor Gmail messages and output them as JSON, designed for automation, monitoring, and integration with other tools.

## Features

- 🔄 **Real-time monitoring** - Continuous monitoring of new emails with `--follow` mode
- 📧 **Flexible filtering** - Filter by sender, subject, labels, attachments, and more
- 💾 **Checkpoint support** - Resume monitoring from where you left off
- 🎯 **Multiple output formats** - JSON, JSON Lines, and compact formats
- ⚙️ **Configuration files** - YAML configuration for complex setups
- 🔍 **Gmail search syntax** - Full support for Gmail's powerful search queries
- 🚀 **Easy authentication** - Support for OAuth2 and service accounts

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
   uv run gmailtail --credentials credentials.json --follow
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
gmailtail --follow

# Monitor emails from specific sender
gmailtail --from "noreply@github.com" --follow

# Monitor with Gmail search query
gmailtail --query "subject:alert OR subject:error" --follow
```

### Filtering options
```bash
# Monitor unread emails only
gmailtail --unread-only --follow

# Monitor emails with attachments
gmailtail --has-attachment --include-attachments --follow

# Monitor specific labels
gmailtail --label important --label work --follow

# Monitor since specific date
gmailtail --since "2025-01-01T00:00:00Z" --follow
```

### Output formats
```bash
# Pretty JSON output
gmailtail --format json --pretty --follow

# JSON Lines format (one JSON per line)
gmailtail --format json-lines --follow

# Compact format
gmailtail --format compact --follow

# Include email body
gmailtail --include-body --max-body-length 500 --follow

# Custom fields only
gmailtail --fields "id,subject,from,timestamp" --follow
```

### Checkpoint management
```bash
# Resume from last checkpoint
gmailtail --resume --follow

# Reset checkpoint and start fresh
gmailtail --reset-checkpoint --follow

# Custom checkpoint file
gmailtail --checkpoint-file ./my-checkpoint --follow
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
- `--follow, -f` - Continuous monitoring (like `tail -f`)
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
  follow: true
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

