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

WORDPRESS_URL=http://your-wordpress-url

WORDPRESS_USERNAME=your-wordpress-username

WORDPRESS_PASSWORD=your-wordpress-password

GOOGLE_SHEET_ID=your-google-sheet-id

GOOGLE_API_CREDENTIALS=path-to-google-api-credentials.json

OPENAI_API_KEY=your-openai-api-key

GOOGLE_SHEET_NAME=your-google-sheet-name

## Usage

1. Run the script
   ` python rrepair.py`

The script will:

- Scrape recipe URLs from the Google Sheet
- Fetch data from each URL
- Generate new content using the OpenAI API
- Update the corresponding WordPress articles
- Update the status in the Google Sheet
