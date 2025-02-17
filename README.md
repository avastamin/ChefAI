# ChefAI (Recipe Content Updater)

Automate the process of updating recipe content on WordPress websites by leveraging OpenAI for content generation and managing updates through WordPress REST API and Google Sheets.

## Features

- **Scrape Recipe Data**: Extract title, ingredients, total time, and images from recipe URLs
- **Content Generation**: Generate engaging recipe content using OpenAI API, including:
  - Introductions
  - Main ingredients breakdown
  - Serving instructions
  - Storage guidelines
  - Substitution options
  - Common mistakes
  - FAQ sections
- **WordPress Integration**: Seamlessly update posts via WordPress REST API
- **Google Sheets Integration**: Track article processing status
- **Image Management**: Extract and incorporate recipe images

## Prerequisites

- Python 3.x
- WordPress site with REST API enabled
- Google Sheets API credentials
- OpenAI API access
- Virtual environment (recommended)

## Installation

1. Clone the repository
   git clone https://github.com/avastamin/ChefAI
   cd ChefAI

2. Install dependencies
   `pip install -r requirements.txt`

3. Configure environment variables
   `cp .env.example .env`

4. Activate virtual environment
   `source venv/bin/activate`

5. Set up environment variables

Create a .env file to store the credentials and API keys:

# .env file

OPENAI_API_KEY=your_openai_api_key_here

WP_BASE_URL=your_wordpress_url_here

WP_USERNAME=your_wordpress_username

WP_PASSWORD=your_wordpress_password

ANTHROPIC_API_KEY=your_anthropic_api_key_here

GOOGLE_SHEETS_CREDENTIALS_FILE=your_google_sheet_url_here

GOOGLE_SHEET_KEY=your_google_sheet_name_here

## Usage

1. Run the script
   ` python rrepair.py`

The script will:

- Scrape recipe URLs from the Google Sheet
- Fetch data from each URL
- Generate new content using the OpenAI API
- Update the corresponding WordPress articles
- Update the status in the Google Sheet
