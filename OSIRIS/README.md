# BISHOP Discord Bot

BISHOP is an advanced Discord bot that combines AI capabilities with powerful server management tools and integrations with Notion and Linear.

## Features

### AI Interaction
Use `/spectre` to interact with a powerful AI assistant that can help with various tasks, from creative writing to problem-solving.

### Content Management
Save and organize your AI-generated content with `/vault` for easy access later.

### Community Marketplace
Share your creations with others and discover content from the community with `/the_exchange`.

### Command Execution
Execute saved commands with `/commit` to automate Discord server management tasks.

### Integrations
- **Notion**: Access and search your Notion workspace directly through the bot
- **Linear**: Create, update, and manage tickets in Linear directly through the bot
- **GPT**: Powered by g4f client with access to gpt-4o-mini model

## Tiers

- **Drifter** (Free): 3 replies per conversation, 5 saved files max, 10-minute cooldown after 3 uses in 5 minutes
- **Seeker** (Premium): 5 replies per conversation, 12 saved files max, 2-minute cooldown
- **Abysswalker** (VIP): 7 replies per conversation, 30 saved files max, no cooldown

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with the following variables:
   ```
   DISCORD_BOT_TOKEN=your_bot_token
   BOT_OWNER_ID=your_discord_id
   REVIEW_CHANNEL_ID=channel_id_for_reviews
   WEBSITE_URL=your_website_url
   BUSINESS_EMAIL=your_email
   ```
4. Run the bot:
   ```
   python main.py
   ```

## Directory Structure

- `cogs/`: Contains the bot's command modules
  - `spectre.py`: AI interaction commands
  - `manager.py`: Content management commands
  - `executor.py`: Command execution functionality
- `commands/`: Contains command execution modules
  - `free/`: Commands available to all users
  - `premium/`: Commands available to premium users
- `saves/`: User-saved content
- `temp/`: Temporary files

## Usage

- `/spectre`: Start an AI conversation
- `/vault`: Access your saved content
- `/the_exchange`: Browse and share creations
- `/commit`: Execute saved commands

## License

© 2025 Reign Spectre. All rights reserved.
