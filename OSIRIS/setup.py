#!/usr/bin/env python
# setup.py

import os
import sys
import subprocess
from pathlib import Path

def create_directories():
    """Create necessary directories for the bot."""
    directories = [
        "saves",
        "temp",
        "logs",
        "commands/free",
        "commands/premium"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def check_env_file():
    """Check if .env file exists, create template if not."""
    if not Path(".env").exists():
        with open(".env", "w") as f:
            f.write("""# .env
DISCORD_BOT_TOKEN=your_bot_token_here
BOT_OWNER_ID=your_discord_id_here
REVIEW_CHANNEL_ID=channel_id_for_reviews
WEBSITE_URL=your_website_url
BUSINESS_EMAIL=your_email
""")
        print("Created template .env file. Please edit it with your actual values.")
    else:
        print(".env file already exists.")

def install_dependencies():
    """Install required dependencies."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError:
        print("Failed to install dependencies. Please install them manually using 'pip install -r requirements.txt'.")

def main():
    """Main setup function."""
    print("Setting up BISHOP Discord Bot...")
    
    # Create directories
    create_directories()
    
    # Check for .env file
    check_env_file()
    
    # Install dependencies
    install_dependencies()
    
    print("\nSetup complete! You can now run the bot using 'python main.py'.")
    print("Make sure to edit the .env file with your actual values before running the bot.")

if __name__ == "__main__":
    main()
