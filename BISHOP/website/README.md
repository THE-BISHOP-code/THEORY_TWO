# BISHOP Website

This is the official website for the BISHOP Discord bot, providing information about the bot, pricing, and a dashboard for users to manage their bot settings.

## Features

- **Main Website**: Information about the bot, pricing, and contact information
- **User Dashboard**: Allows users to manage their bot settings, tokens, and configuration
- **Discord OAuth Integration**: Secure login with Discord
- **Tier-Based Access**: Different features available based on user subscription tier
- **Responsive Design**: Works on desktop and mobile devices

## Directory Structure

- `assets/`: Static assets (CSS, JavaScript, images, fonts)
- `dashboard/`: Dashboard pages for logged-in users
- `includes/`: PHP includes (configuration, functions, database)
- `db/`: Database schema and migrations
- `index.php`: Main landing page
- `about.php`: About page
- `pricing.php`: Pricing page
- `contact.php`: Contact page
- `login.php`: Login page with Discord OAuth

## Requirements

- PHP 7.4 or higher
- MySQL 5.7 or higher
- Web server (Apache, Nginx)
- SSL certificate (for secure Discord OAuth)

## Installation

1. Clone the repository to your web server
2. Create a MySQL database and import the schema from `db/schema.sql`
3. Configure your web server to serve the website
4. Copy `includes/config.example.php` to `includes/config.php` and update the settings
5. Create a Discord application at https://discord.com/developers/applications
6. Configure the OAuth2 redirect URI to point to your `login.php` page
7. Update the Discord application credentials in `includes/config.php`

## Configuration

The main configuration file is `includes/config.php`. You'll need to update the following settings:

- Database connection details
- Discord OAuth credentials
- Website URL and email
- Pricing information

## Development

To set up a development environment:

1. Install PHP and MySQL locally
2. Configure a local web server (Apache, Nginx) or use PHP's built-in server
3. Create a local database and import the schema
4. Update the configuration file with your local settings

## Deployment

To deploy to production:

1. Upload the files to your web server
2. Create a production database and import the schema
3. Update the configuration file with production settings
4. Configure your web server for production (SSL, caching, etc.)
5. Update your Discord application's OAuth2 redirect URI to point to your production URL

## Security

- All user passwords are handled by Discord OAuth
- API tokens are securely generated and stored
- CSRF protection is implemented for all forms
- XSS protection is implemented for all user input
- SQL injection protection is implemented for all database queries

## License

© 2025 Reign Spectre. All rights reserved.
