#!/usr/bin/env python3
"""
Simple test script for gmailtail
"""

import os
import sys
import tempfile
import pytest
from gmailtail.config import Config, AuthConfig, FilterConfig

def test_config():
    """Test configuration loading"""
    print("Testing configuration...")
    
    # Test default config
    config = Config()
    assert config.auth.token_cache.endswith('.gmailtail/tokens')
    assert config.monitoring.poll_interval == 30
    print("✓ Default configuration OK")
    
    # Test CLI args
    cli_args = {
        'from_email': 'test@example.com',
        'poll_interval': 60,
        'output_format': 'json-lines'
    }
    config = Config.from_cli_args(**cli_args)
    assert config.filters.from_email == 'test@example.com'
    assert config.monitoring.poll_interval == 60
    assert config.output.format == 'json-lines'
    print("✓ CLI args configuration OK")
    
    # Test YAML config
    yaml_content = """
auth:
  credentials_file: /path/to/creds.json
  token_cache: /custom/token/path

filters:
  query: "label:test"
  unread_only: true

output:
  format: compact
  include_body: true
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_yaml = f.name
    
    try:
        config = Config.from_file(temp_yaml)
        assert config.auth.credentials == '/path/to/creds.json'
        assert config.filters.query == 'label:test'
        assert config.filters.unread_only == True
        assert config.output.format == 'compact'
        assert config.output.include_body == True
        print("✓ YAML configuration OK")
    finally:
        os.unlink(temp_yaml)

def test_formatter():
    """Test output formatting"""
    print("Testing formatter...")
    
    from gmailtail.formatter import OutputFormatter
    
    config = Config()
    formatter = OutputFormatter(config)
    
    test_message = {
        'id': 'test123',
        'subject': 'Test Subject',
        'from': {'name': 'Test Sender', 'email': 'test@example.com'},
        'timestamp': '2025-07-01T10:30:00Z',
        'body': 'Test email body'
    }
    
    # Test JSON format
    config.output.format = 'json'
    json_output = formatter.format_message(test_message)
    assert 'test123' in json_output
    assert 'Test Subject' in json_output
    print("✓ JSON formatting OK")
    
    # Test compact format
    config.output.format = 'compact'
    compact_output = formatter.format_message(test_message)
    assert '2025-07-01T10:30:00Z' in compact_output
    assert 'test@example.com' in compact_output
    assert 'Test Subject' in compact_output
    print("✓ Compact formatting OK")
    
    # Test field filtering
    config.output.format = 'json'  # Reset to JSON format
    config.output.fields = ['id', 'subject']
    filtered_output = formatter.format_message(test_message)
    # Should only contain id and subject
    import json
    parsed = json.loads(filtered_output)
    assert set(parsed.keys()) == {'id', 'subject'}
    print("✓ Field filtering OK")

def main():
    """Run all tests"""
    print("Running gmailtail tests...\n")
    
    try:
        test_config()
        test_formatter()
        print("\n✅ All tests passed!")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())