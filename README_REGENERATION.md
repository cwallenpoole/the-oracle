# Oracle Reading Regeneration Utilities

This directory contains two command-line utilities for managing and regenerating Oracle readings:

## 1. `list_readings.py` - List Available Readings

Lists all available readings in the database that can be regenerated.

### Usage

```bash
# Activate virtual environment
source the-oracle/bin/activate

# List all readings (default: last 50)
python list_readings.py

# List readings for specific user
python list_readings.py --user john

# List only I Ching readings
python list_readings.py --type iching

# List only Runic readings
python list_readings.py --type runes

# Show more results
python list_readings.py --limit 100

# Show full question text (not truncated)
python list_readings.py --verbose
```

### Example Output

```
Found 5 reading(s):

Reading ID      User         Type     Date             Question
--------------------------------------------------------------------------------
f57926bacca8    cwa          iching   2025-07-03 23:10 I'm really struggling to get my partn...
df2f445a1c44    f            iching   2025-07-02 12:27 Huh>
90b5083a        cwa          iching   2025-07-02 12:20 foo
d1ba5ef2        f            runes    2025-07-02 08:47 I don't know how to deal with other p...
cd665bb0        cwa          runes    2025-07-01 16:02 I want to incorporate Christian divin...

To regenerate a reading, use:
python regenerate_reading.py <reading_id>
Example: python regenerate_reading.py f57926bacca8
```

## 2. `regenerate_reading.py` - Regenerate Reading Predictions

Regenerates ChatGPT predictions for existing readings by sending the original data back to the AI.

### Usage

```bash
# Activate virtual environment
source the-oracle/bin/activate

# Regenerate by reading ID
python regenerate_reading.py f57926bacca8

# Regenerate by reading path
python regenerate_reading.py john-2024-01-15-abc123def456

# Show what would be done without making changes
python regenerate_reading.py f57926bacca8 --dry-run

# Enable verbose logging
python regenerate_reading.py f57926bacca8 --verbose

# Force regeneration even if recently done
python regenerate_reading.py f57926bacca8 --force

# Use a different OpenAI model
python regenerate_reading.py f57926bacca8 --model gpt-4o
```

### How It Works

1. **Finds the reading** by ID or path in the database
2. **Checks if recently regenerated** (within last hour) - can override with `--force`
3. **Recreates the original reading context** including:
   - User's original question
   - Hexagram/rune casting data
   - User profile information
   - Reading history context
4. **Calls ChatGPT** with the same prompt structure as the original
5. **Updates the database** with the new AI response
6. **Logs the LLM request** for tracking purposes

### Safety Features

- **Recent regeneration check**: Prevents accidental double-regeneration
- **Dry-run mode**: Shows what would be done without making changes
- **Verbose logging**: Detailed information about the process
- **Error handling**: Graceful handling of missing readings, users, etc.
- **Database validation**: Only processes readings with valid data

### Supported Reading Types

- **I Ching readings**: ✅ Fully supported
- **Runic readings**: ⚠️ Not yet implemented (planned for future release)

### Example Output

```bash
$ python regenerate_reading.py f57926bacca8 --verbose --force

[2025-07-03 23:25:45] DEBUG: Searching for reading with identifier: f57926bacca8
[2025-07-03 23:25:45] DEBUG: Found reading by ID: f57926bacca8
[2025-07-03 23:25:45] INFO: Found reading:
[2025-07-03 23:25:45] INFO:   ID: f57926bacca8
[2025-07-03 23:25:45] INFO:   User: cwa
[2025-07-03 23:25:45] INFO:   Type: iching
[2025-07-03 23:25:45] INFO:   Date: 2025-07-03T23:10:15.194362
[2025-07-03 23:25:45] INFO:   Question: I'm really struggling to get my partner to understand...
[2025-07-03 23:25:45] INFO: Regenerating reading f57926bacca8 for user cwa
[2025-07-03 23:25:45] DEBUG: Regenerating I Ching reading with question: I'm really struggling...
[2025-07-03 23:25:52] DEBUG: Generated new response (3515 characters)
[2025-07-03 23:25:52] INFO: Successfully updated reading f57926bacca8 in database
[2025-07-03 23:25:52] INFO: Successfully regenerated reading f57926bacca8
[2025-07-03 23:25:52] INFO: New response preview: Your inquiry echoes the silent depths of the mountains...
```

## Workflow Example

1. **Find readings to regenerate:**
   ```bash
   python list_readings.py --user john --limit 10
   ```

2. **Test regeneration (dry-run):**
   ```bash
   python regenerate_reading.py abc123def456 --dry-run --verbose
   ```

3. **Regenerate the reading:**
   ```bash
   python regenerate_reading.py abc123def456 --verbose
   ```

## Error Codes

- **Exit Code 0**: Success
- **Exit Code 1**: Error (reading not found, regeneration failed, etc.)

## Requirements

- Python virtual environment must be activated (`source the-oracle/bin/activate`)
- OpenAI API key must be configured in `.env`
- Database must contain readings (`data/users.db`)

## Performance

The regeneration utility uses the optimized I Ching cache for fast hexagram lookups, ensuring regeneration completes quickly even for complex readings.

## Notes

- The regeneration preserves the original reading structure and context
- LLM requests are logged in the `llm_requests` table for audit purposes
- The original hexagram casting is not changed - only the AI interpretation is regenerated
- Reading paths can be used instead of reading IDs (format: `username-YYYY-MM-DD-readingid`)
