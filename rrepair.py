import sys
import os
import gspread
from google.oauth2.service_account import Credentials

# Path to the credentials file
GOOGLE_SHEETS_CREDENTIALS_FILE = 'credentials.json'

# Fügen Sie den Pfad zu Ihrem benutzerdefinierten Modul-Verzeichnis hinzu
sys.path.insert(0, "/www/htdocs/w01a6aec/python-module")



from concurrent.futures import ThreadPoolExecutor
import content


# #Input from user
import requests
from bs4 import BeautifulSoup

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
sheet = gc.open('Ruhul of Article Revising & Extending mollyshomeguide.com').sheet1  # Replace with your sheet name

def update_article(url, new_content):
    """Update the article on WordPress with new content."""
    post_id = url.split("/")[-1]
    response = requests.post(
        f"{WORDPRESS_URL}/wp-json/wp/v2/posts/{post_id}",
        auth=HTTPBasicAuth(WORDPRESS_USERNAME, WORDPRESS_PASSWORD),
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

print(article_urls)

for url in article_urls:
    print(f"\n=== Processing Recipe: {url} ===")
    
    if not url.strip():  # Skip empty rows
        continue
        
    try:
        # Fetch and parse the webpage
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get title from h1
        title = soup.find('h1').text.strip()

        # Get ingredients list
        ingredients_section = soup.find('h2', string='Ingredients')
        ingredients = ""
        
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
                # Find the td that contains 'Total Time'
                td = row.find('td')
                if td and td.find('b') and 'Total Time' in td.find('b').text:
                    # Get the next td which contains the time value
                    time_td = td.find_next('td')
                    if time_td:
                        time = time_td.text.strip()
                    break
        
        print(f"\nExtracted data:")
        print(f"Title: {title} \n")
        print(f"Ingredients: \n{ingredients}\n")
        print(f"Total Time: {time}\n")
        
    except Exception as e:
        print(f"Error scraping the webpage: {str(e)}")
        continue

    print('Generating recipe...'+ '\n')
    
    
    # Create executor
    with ThreadPoolExecutor() as executor:
        #Submit all tasks
        future_intro = executor.submit(content.generate_intro_section, title)
        future_main_ingredient = executor.submit(content.generate_maine_ingredient_section, title, ingredients)
        future_serving = executor.submit(content.generate_serving_section, title, ingredients)
        future_storage = executor.submit(content.generate_new_storage_section, title, ingredients)
        future_why_love = executor.submit(content.generate_whylove_section, title, ingredients, time)
        future_mistakes = executor.submit(content.generate_mistakes_section, title, ingredients)
        future_substitution = executor.submit(content.generate_new_substitution_section, title, ingredients)
        future_faq = executor.submit(content.generate_faq_section, title, ingredients)

        #Get results in order
        intro = future_intro.result()
        html_main_ingredient = future_main_ingredient.result()
        html_serving = future_serving.result()
        
        html_storage = future_storage.result()
        html_why_love = future_why_love.result()
        html_mistakes = future_mistakes.result()
        html_substitution = future_substitution.result()
        html_faq = future_faq.result()


        #Output the result
        print("\n")
        print("<!-- INTRO SECTION -->")
        print(intro)
        print("\n")
        print("<!-- WHY YOU'LL LOVE THIS SECTION -->")
        print(html_why_love)

        print("\n")
        print("<!-- MAIN INGREDIENT SECTION -->")
        print(html_main_ingredient)

        print("\n")
        print("<!-- SUBSTITUTION SECTION -->")
        print(html_substitution)

        print("\n")
        print("<!-- MISTAKES SECTION -->")
        print(html_mistakes)

        print("\n")
        print("<!-- SERVING SECTION -->")
        print(html_serving)

        print("\n")
        print("<!-- STORAGE SECTION -->")
        print(html_storage)

        print("\n")
        print("<!-- FAQ SECTION -->")
        print(html_faq)
