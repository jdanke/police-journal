# Police PDF Scraper Setup Instructions

Used to schedule retrieval of PDF logs and create a dataframe of their data.

## Automated Scheduling with launchd (Recommended for macOS)

### Step 1: Create a launchd plist file

Copy `com.user.granby-scraper.plist` into `~/Library/LaunchAgents/`:

#### Hardcoded URL
To scrape from a different URL, modify the plist:
```xml
<key>ProgramArguments</key>
<array>
    <string>/Users/joel/opt/anaconda3/envs/base312/bin/python</string>
    <string>/Users/joel/Scripts/granby_scraper.py</string>
    <string>--url</string>
    <string>https://example.com/different-archive</string>
    <string>--download-dir</string>
    <string>/Users/joel/Documents/Different_Archive</string>
</array>
```

#### Option: Use a Config File
Create a config file at `/Users/joel/Scripts/scraper_config.json`:

```json
{
    "url": "https://www.granby-ct.gov/Archive.aspx?AMID=40",
    "download_dir": "/Users/joel/Documents/Granby_Police_Journals"
}
```

Then modify the plist to use the config file:
```xml
<key>ProgramArguments</key>
<array>
    <string>/Users/joel/opt/anaconda3/envs/base312/bin/python</string>
    <string>/Users/joel/Scripts/granby_scraper.py</string>
    <string>--config-file</string>
    <string>/Users/joel/Scripts/scraper_config.json</string>
</array>
```

### Step 2: Load the launch agent

```bash
launchctl load ~/Library/LaunchAgents/com.user.granby-scraper.plist
```

### Step 3: Verify it's loaded

```bash
launchctl list | grep granby
```

## Manual Testing

## Command Line Usage Examples

You can now run the script with various options:

### Basic Usage (uses defaults)
```bash
/Users/joel/opt/anaconda3/envs/base312/bin/python /Users/joel/Scripts/granby_scraper.py
```

### Specify Custom URL and Directory
```bash
/Users/joel/opt/anaconda3/envs/base312/bin/python /Users/joel/Scripts/granby_scraper.py \
  --url "https://www.granby-ct.gov/Archive.aspx?AMID=40" \
  --download-dir "/Users/joel/Documents/Custom_Police_Journals"
```

### Enable Verbose Logging
```bash
/Users/joel/opt/anaconda3/envs/base312/bin/python /Users/joel/Scripts/granby_scraper.py --verbose
```

### Use Configuration File
```bash
/Users/joel/opt/anaconda3/envs/base312/bin/python /Users/joel/Scripts/granby_scraper.py \
  --config-file "/Users/joel/Scripts/scraper_config.json"
```

### View Help
```bash
/Users/joel/opt/anaconda3/envs/base312/bin/python /Users/joel/Scripts/granby_scraper.py --help
```

## Configuration Options

### Command Line Arguments
- `--url`: Specify the URL to scrape
- `--download-dir`: Set the download directory (supports `~` expansion)
- `--verbose`: Enable detailed logging
- `--config-file`: Use a JSON configuration file

### Configuration File
Create a JSON file with your settings:

```json
{
    "url": "https://www.granby-ct.gov/Archive.aspx?AMID=40",
    "download_dir": "/Users/joel/Documents/Granby_Police_Journals",
    "verbose": true
}
```

### Environment Variables (Advanced)
You can also set these environment variables:
- `GRANBY_SCRAPER_URL`
- `GRANBY_SCRAPER_DIR`

The priority order is: Command Line Args > Config File > Environment Variables > Defaults

## Monitoring

The script creates several log files in your download directory:

- `scraper.log` - Main application log
- `downloaded_files.json` - Database of downloaded files
- `launchd_output.log` - Output from the scheduled runs
- `launchd_error.log` - Error messages from scheduled runs

## Troubleshooting

## Troubleshooting the "__main__" Module Error

If you're getting "can't find '__main__' module" error, try these steps:

### Step 1: Verify File Permissions and Location

```bash
# Check if the file exists and is executable
ls -la /Users/joel/Scripts/granby_scraper.py
chmod +x /Users/joel/Scripts/granby_scraper.py
```

### Step 2: Test the Script Manually First

```bash
# Test with full path
/Users/joel/opt/anaconda3/envs/base312/bin/python /Users/joel/Scripts/granby_scraper.py

# Test from the Scripts directory
cd /Users/joel/Scripts
/Users/joel/opt/anaconda3/envs/base312/bin/python granby_scraper.py
```

### Step 3: Check Python Path

```bash
# Verify Python executable works
/Users/joel/opt/anaconda3/envs/base312/bin/python --version

# Test Python can find modules
/Users/joel/opt/anaconda3/envs/base312/bin/python -c "import requests; print('OK')"
```

### Step 4: Reload the Launch Agent

```bash
# Unload the current agent
launchctl unload ~/Library/LaunchAgents/com.user.granby-scraper.plist

# Reload with updated plist
launchctl load ~/Library/LaunchAgents/com.user.granby-scraper.plist

# Verify it's loaded
launchctl list | grep granby
```

### Step 5: Test the Launch Agent Immediately

```bash
# Trigger the job manually to test
launchctl start com.user.granby-scraper

# Check the logs immediately
tail -f /Users/joel/Documents/Granby_Police_Journals/launchd_error.log
```

## Stopping the Scheduled Job

To stop the daily scraping:

```bash
launchctl unload ~/Library/LaunchAgents/com.user.granby-scraper.plist
```

To start it again:

```bash
launchctl load ~/Library/LaunchAgents/com.user.granby-scraper.plist
```

## Alternative: Using cron (if launchd doesn't work)

### Alternative: Create a Shell Wrapper Script

If the Python path issues persist, create a wrapper shell script:

```bash
# Create wrapper script
nano /Users/joel/Scripts/run_granby_scraper.sh
```

Add this content:
```bash
#!/bin/bash
cd /Users/joel/Scripts
export PATH="/Users/joel/opt/anaconda3/envs/base312/bin:$PATH"
/Users/joel/opt/anaconda3/envs/base312/bin/python granby_scraper.py
```

Make it executable:
```bash
chmod +x /Users/joel/Scripts/run_granby_scraper.sh
```

Then modify your plist to use the shell script instead:
```xml
<key>ProgramArguments</key>
<array>
    <string>/Users/joel/Scripts/run_granby_scraper.sh</string>
</array>
```
