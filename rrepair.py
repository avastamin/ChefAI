import os
import sys
from concurrent.futures import ThreadPoolExecutor
from google.oauth2.service_account import Credentials

import content
import gspread
import requests
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth

# WordPress API Credentials
WORDPRESS_URL = os.getenv("WP_BASE_URL")
WORDPRESS_USERNAME = os.getenv("WP_USERNAME")
WORDPRESS_PASSWORD = os.getenv("WP_PASSWORD")

# Path to the credentials file
GOOGLE_SHEETS_CREDENTIALS_FILE = 'credentials.json'
STATUS_COLUMN=2

# Fügen Sie den Pfad zu Ihrem benutzerdefinierten Modul-Verzeichnis hinzu
sys.path.insert(0, "/www/htdocs/w01a6aec/python-module")

# Set up Google Sheets credentials
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
creds = Credentials.from_service_account_file(
    'credentials.json',  # Replace with your credentials file path
    scopes=SCOPES
)
gc = gspread.authorize(creds)

# Open the spreadsheet and get the worksheet
sheet = gc.open_by_key(os.getenv('GOOGLE_SHEET_KEY', '1iQTmq-x9rwQUfQyOAHqYiz67ywi-TmMeZusyIxrwG4k')).sheet1  # Get sheet name from environment variable

def update_article(url, new_content):
    """Update the article on WordPress with new content."""
    
    # LOCAL_WORDPRESS_URL = "http://demo.local"
    # WORDPRESS_USERNAME = "admin"
    # WORDPRESS_PASSWORD = "ojCo KAnm zoWo bGop fIty LX4Z"

    # Find correct post ID
    response = requests.get(f"{WORDPRESS_URL}/wp-json/wp/v2/posts")
    posts = response.json()
    
    post_id = None
    for post in posts:
        if post["link"].strip("/") == url.strip("/"):
            post_id = post["id"]
            break

    if not post_id:
        print(f"❌ No matching post found for URL: {url}")
        return False

    # Update post content
    response = requests.post(
        f"{WORDPRESS_URL}/wp-json/wp/v2/posts/{post_id}",
        auth=(WORDPRESS_USERNAME, WORDPRESS_PASSWORD),
        json={"content": new_content}
    )
    
    if response.status_code == 200:
        print(f"✅ Article {url} updated successfully!")
        return True
    else:
        print(f"❌ Failed to update article {url}: {response.text}")
        return False
    

def update_spreadsheet(url, status):
    """Update Google Sheets status column."""
    try:
        cell = sheet.find(url)  # Find row where URL exists
        sheet.update_cell(cell.row, STATUS_COLUMN, status)
        print(f"✅ Updated spreadsheet for {url}: {status}")
    except Exception as e:
        print(f"❌ Failed to update spreadsheet for {url}: {str(e)}")

article_urls = sheet.col_values(1)[1:]  # Get all URLs from first column, skip header


for url in article_urls:
    print(f"\n=== Processing Recipe: {url} ===")
    
    if not url.strip():  # Skip empty rows
        continue
        
    try:
        # Fetch and parse the webpage
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get title from h1
        title_tag = soup.find('h1')
        title = title_tag.text.strip() if title_tag else "Unknown Recipe"

        # Get ingredients list
        ingredients_section = soup.find('h2', string='Ingredients')
        
        if ingredients_section:
            # Find the ul with class 'ingr' directly after the h2
            ingredients_list = ingredients_section.find_next('ul', class_='ingr')
            
            if ingredients_list:
                ingredients = '\n'.join([item.text.strip() for item in ingredients_list.find_all('li')])

        # Get total time from table
        time = ""
        table = soup.find('table')
        
        if table:
            for row in table.find_all('tr'):
                td = row.find('td')
                if td and td.find('b') and 'Total Time' in td.find('b').text:
                    time_td = td.find_next('td')
                    if time_td:
                        time = time_td.text.strip()
                    break
        
        # Extract images (handling lazy loading)
        images = []
        for img in soup.find_all('img', src=True):
            actual_src = img.get('data-src') or img.get('data-lazy-src') or img.get('src')
            if actual_src and not actual_src.startswith('data:image/svg+xml'):  # Skip placeholder SVGs
                images.append(actual_src)
        
        # Use placeholder images if no valid images are found
        if not images:
            print("⚠️ No valid images found. Using placeholder images.")
            images = [
                "https://via.placeholder.com/600x400",
                "https://via.placeholder.com/600x400",
                "https://via.placeholder.com/600x400"
            ]
        
        image1 = images[0] if len(images) > 0 else None
        image2 = images[1] if len(images) > 1 else None
        image3 = images[2] if len(images) > 2 else None

        # Extract nutrition info if available (example for a simple 'Nutrition' heading)
        nutrition = ""
        nutrition_section = soup.find('div', class_='nutrition')
        if nutrition_section:
            nutrition = nutrition_section.get_text().strip()

        # Extract steps if available (example)
        steps = ""
        steps_section = soup.find('div', class_='steps')
        if steps_section:
            steps = "\n".join([step.get_text().strip() for step in steps_section.find_all('p')])

        # Combine the extracted content into {html_rest}
        html_rest = f"""
        <!-- NUTRITION SECTION -->
        {nutrition}

        <!-- STEPS SECTION -->
        {steps}
        """

        print(f"\nExtracted data:")
        print(f"Title: {title} \n")
        print(f"Ingredients: \n{ingredients}\n")
        print(f"Total Time: {time}\n")
        
    except Exception as e:
        print(f"❌ Error scraping the webpage: {str(e)}")
        continue

    print('Generating recipe...\n')

    # Create executor
    with ThreadPoolExecutor() as executor:
        # Submit all tasks
        future_intro = executor.submit(content.generate_intro_section, title)
        future_main_ingredient = executor.submit(content.generate_maine_ingredient_section, title, ingredients)
        future_serving = executor.submit(content.generate_serving_section, title, ingredients)
        future_storage = executor.submit(content.generate_new_storage_section, title, ingredients)
        future_why_love = executor.submit(content.generate_whylove_section, title, ingredients, time)
        future_mistakes = executor.submit(content.generate_mistakes_section, title, ingredients)
        future_substitution = executor.submit(content.generate_new_substitution_section, title, ingredients)
        future_faq = executor.submit(content.generate_faq_section, title, ingredients)

        # Get results in order
        intro = future_intro.result()
        html_main_ingredient = future_main_ingredient.result()
        html_serving = future_serving.result()
        html_storage = future_storage.result()
        html_why_love = future_why_love.result()
        html_mistakes = future_mistakes.result()
        html_substitution = future_substitution.result()
        html_faq = future_faq.result()

    # Combine all generated sections into final content
    new_content = f"""
    <!-- INTRO SECTION -->
    {intro}


    <!-- IMAGE 1 -->
    <img src="{image1}" alt="Recipe Image 1">


    <!-- WHY YOU'LL LOVE THIS SECTION -->
    {html_why_love}

    <!-- MAIN INGREDIENT SECTION -->
    {html_main_ingredient}

    <!-- IMAGE 2 -->
    <img src="{image2}" alt="Recipe Image 2">

    <!-- SUBSTITUTION SECTION -->
    {html_substitution}

    <!-- MISTAKES SECTION -->
    {html_mistakes}

    <!-- SERVING SECTION -->
    {html_serving}

    <!-- IMAGE 3 -->
    <img src="{image3}" alt="Recipe Image 3">

    <!-- STORAGE SECTION -->
    {html_storage}

    <!-- FAQ SECTION -->
    {html_faq}
    
    <!-- The Rest of the Recipe -->
    {html_rest}
    """

    print(new_content)
    # Update WordPress article
    if update_article(url, new_content):
        update_spreadsheet(url, "Done")