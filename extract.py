import requests
import re
import csv
import os
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin


# Base URL
BASE_URL = "https://books.toscrape.com/"
BASE_URL_BOOKS = "https://books.toscrape.com/catalogue/"

def fetch_page(url, content_type="unknown", current_item=None, total_items=None):
    """
     Makes an HTTP request to retrieve the content of the page.
    """
    try:
        # Get the current item and total items to display progress
        if total_items and current_item:
            progress = f"({current_item}/{total_items})"
        else:
            progress = ""
        print(f"Récupération de la page ({content_type}) {progress}: {url}")
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return BeautifulSoup(response.content, "html.parser")
        else:
            print(f"Impossible de récupérer la page. Code statut : {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Une erreur est survenue lors de la requête : {e}")
        return None
    
def extract_category_urls(soup):
    """
    Extracts all category URLs from the page.
    """
    try:
        side_categories = soup.find('div', class_='side_categories')
        if not side_categories:
            print("Erreur : conteneur des catégories introuvable.")
            return []
        # Extract all category links
        category_links = side_categories.find_all('a')
        category_urls = []
        
        for link in category_links:
            href = link.get('href')
            if href:
                full_url = urljoin(BASE_URL, href)
                if "catalogue/category/books_1/index.html" not in full_url:
                    category_urls.append(full_url)
                    
        print(f"{len(category_urls)} catégories trouvées :")
        
        return category_urls
    except Exception as e:
        print(f"Erreur lors de l'extraction des catégories : {e}")
        return []
    
def extract_urls_book(soup,url):
    """
    Extracts all book URLs from a category page.
    Handles pagination if the number of results exceeds 20.
    """
    try:
        if url.endswith("index.html"):
           url = url[:-11]  
       
        # Extract total number of results
        results_text = soup.find("form", class_="form-horizontal").find("strong").text.strip()
        total_results = int(results_text) 

        # Calculate the number of pages needed
        results_per_page = 20
        total_pages = (total_results // results_per_page) + (1 if total_results % results_per_page != 0 else 0)

        # Extract URLs from the first page
        book_urls = []
        book_list = soup.find_all('h3')  
        for book in book_list:
            book_url = book.find('a')['href']
            if book_url.startswith("../../../"):
                book_url = book_url[9:]  
            full_url = urljoin(BASE_URL_BOOKS, book_url)  
            book_urls.append(full_url)
        
        # Generate URLs for the remaining pages
        for page_num in range(2, total_pages + 1):
            page_url = f"{url}/page-{page_num}.html"
           
            page_soup = fetch_page(page_url, content_type="catégorie")
            if page_soup:
                
                book_list = page_soup.find_all('h3') 
                for book in book_list:
                    book_url = book.find('a')['href']
                    if book_url.startswith("../../../"):
                        book_url = book_url[9:] 
                    full_url = urljoin(BASE_URL_BOOKS, book_url)
                    book_urls.append(full_url)

       
        return book_urls
    except Exception as e:
        print(f"Erreur lors de l'extraction des données : {e}")
        return None
    
def extract_product_data(soup, url):
    """
    Extracts product data from a book page.
    """
    try:
        title = soup.find("h1").string if soup.find("h1") else "Information non disponible"

        # Book image
        product_image_active = soup.find("div", class_="item active")
        if product_image_active:
            img_tag = product_image_active.find("img")
            relative_img_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None
            image_url = urljoin(BASE_URL, relative_img_url) if relative_img_url else "Information non disponible"
        else:
            image_url = "Information non disponible"

        # Book description
        product_description_section = soup.find(id="product_description")
        if product_description_section:
            next_element = product_description_section.find_next("p")
            product_description = next_element.text.strip() if next_element else "Information non disponible"
        else:
            product_description = "Information non disponible"

        # Book information
        product_page = soup.find("article", class_="product_page")
        product_info = {}
        if product_page:
            table = product_page.find("table")
            if table:
                for row in table.find_all("tr"):
                    header = row.find("th")
                    data = row.find("td")
                    if header and data:
                        key = header.text.strip()
                        value = data.text.strip()
                        product_info[key] = value

        upc = product_info.get('UPC', 'Information non disponible')
        price_excluding_taxe = product_info.get('Price (excl. tax)', 'Information non disponible')
        price_including_taxe = product_info.get('Price (incl. tax)', 'Information non disponible')
        availability = product_info.get('Availability', 'Information non disponible')
        number_available = re.search(r'\((\d+)', availability).group(1) if 'Availability' in product_info else 'Information non disponible'

        # Catégory
        breadcrumb_items = soup.select("ul.breadcrumb li")
        category = breadcrumb_items[2].get_text(strip=True) if len(breadcrumb_items) > 2 else "Information non disponible"

        # Évaluation
        product_review_rating = soup.find('p', class_='star-rating')
        if product_review_rating:
            rating_class = product_review_rating.get('class')[1]
            rating_map = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}
            review_rating = rating_map.get(rating_class, 0)
        else:
            review_rating = 'Information non disponible'

        # Data compilation
        data = {
            'product_page_url': url,
            'universal_product_code (upc)': upc,
            'title': title,
            'price_including_taxe': price_including_taxe,
            'price_excluding_taxe': price_excluding_taxe,
            'number_available': number_available,
            'product_description': product_description,
            'category': category,
            'review_rating': review_rating,
            'image_url': image_url,
        }
        print("Données du livre extraites avec succès.")
        return data,category
    except Exception as e:
        print(f"Erreur lors de l'extraction des données : {e}")
        return None

def export_to_csv(data_list, category_name):
    """
    Exports the data to a CSV file.
    """
    try:
        if not data_list:
            print("Aucune donnée à exporter.")
            return
        
        export_folder = 'export'
        if not os.path.exists(export_folder):
            os.makedirs(export_folder)

        # Create a unique filename based on the category name and current timestamp
        timestamp = time.strftime("%d%m%Y_%H%M%S")
        sanitized_category_name = re.sub(r'[^\w\-.]', '_', category_name).replace(' ', '_')
        filename = f"{sanitized_category_name}_{timestamp}.csv"
        file_path = os.path.join(export_folder, filename)
        
        # Get the fieldnames from the first dictionary in the list
        fieldnames = data_list[0].keys()
        
        # Write data to the file
        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames= fieldnames)
            writer.writeheader()
            writer.writerows(data_list)

        print(f"Données exportées avec succès dans {file_path}")
    except Exception as e:
        print(f"Erreur lors de l'exportation des données : {e}")

def main():
    # Fetch the main page
    soup = fetch_page(BASE_URL, content_type="page principale")
    if not soup:
        return

    category_urls = extract_category_urls(soup)

    for category_index, category_url in enumerate(category_urls, start=1):
        # Indicate the total number of categories
        print(f"--- Catégorie {category_index}/{len(category_urls)} ---")

        # Fetch books from the category
        category_soup = fetch_page(category_url, content_type="catégorie")
        if not category_soup:
            continue

        book_urls = extract_urls_book(category_soup,category_url)
        if not book_urls:
            print("Aucun livre trouvé dans cette catégorie.")
            continue

        print(f"Nombre de livres trouvés dans la catégorie : {len(book_urls)}")

        # Extract data for each book
        product_data_list = []
        for book_index, book_url in enumerate(book_urls, start=1):
            book_soup = fetch_page(book_url, content_type="livre", current_item=book_index, total_items=len(book_urls))
            if not book_soup:
                continue
            product_data, product_category = extract_product_data(book_soup, book_url)
            if product_data:
                product_data_list.append(product_data)
                category = product_category

        # Export the data to a CSV file
        if product_data_list:
            export_to_csv(product_data_list, category)

    print("Tous les fichiers ont été exportés avec succès. Vous pouvez les trouver dans le dossier 'export'.")
    
if __name__ == "__main__":
    main()
