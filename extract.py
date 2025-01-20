import requests
import re
import csv
import os
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin


# URL de base pour les images
BASE_URL = 'https://books.toscrape.com/'
EXPECTED_PREFIX = "https://books.toscrape.com/catalogue/category/books"

def validate_url(url):
    """
    Vérifie si l'URL fournie est valide et commence par le préfixe attendu.
    """
    if not url.startswith(EXPECTED_PREFIX):
        print(f"L'URL doit commencer par {EXPECTED_PREFIX}.")
        return False
    return True

def extract_urls_book(soup,url):
    """
    Extrait toutes les URL des livres appartenant à une catégorie.
    Gère la pagination si le nombre total de résultats dépasse 20.
    """
    try:
        if url.endswith("index.html"):
           url = url[:-10]  
        
        # Extraire le nombre total de résultats
        results_text = soup.find("form", class_="form-horizontal").find("strong").text.strip()
        total_results = int(results_text) 

        # Calculer le nombre de pages nécessaires
        results_per_page = 20
        total_pages = (total_results // results_per_page) + (1 if total_results % results_per_page != 0 else 0)

        # Extraire les URL de la première page
        book_urls = []
        book_list = soup.find_all('h3')  
        for book in book_list:
            book_url = book.find('a')['href']
            full_url = urljoin(url, book_url)  
            book_urls.append(full_url)

        # Générer les URLs pour toutes les pages suivantes si nécessaire
        for page_num in range(2, total_pages + 1):
            page_url = f"{url}/page-{page_num}.html"
           
            page_soup = fetch_page(page_url)
            if page_soup:
                
                book_list = page_soup.find_all('h3') 
                for book in book_list:
                    book_url = book.find('a')['href']
                    full_url = urljoin(url, book_url)
                    book_urls.append(full_url)

       
        return book_urls
    except Exception as e:
        print(f"Erreur lors de l'extraction des données : {e}")
        return None
    
def fetch_page(url):
    """
    Effectue une requête HTTP pour récupérer le contenu de la page.
    """
    try:
        # Connexion a la page
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("Page récupérée avec succès.")
            return BeautifulSoup(response.content, "html.parser")
        else:
            print(f"Impossible de récupérer la page. Code statut : {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Une erreur est survenue lors de la requête : {e}")
        return None

def extract_product_data(soup, url):
    """
    Extrait les données du livre depuis le contenu HTML.
    """
    try:
        title = soup.find("h1").string if soup.find("h1") else "Information non disponible"

        # Image du livre
        product_image_active = soup.find("div", class_="item active")
        if product_image_active:
            img_tag = product_image_active.find("img")
            relative_img_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None
            image_url = urljoin(BASE_URL, relative_img_url) if relative_img_url else "Information non disponible"
        else:
            image_url = "Information non disponible"

        # Description du livre
        product_description_section = soup.find(id="product_description")
        if product_description_section:
            next_element = product_description_section.find_next("p")
            product_description = next_element.text.strip() if next_element else "Information non disponible"
        else:
            product_description = "Information non disponible"

        # Informations sur le livre
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

        # Catégorie
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

        # Compilation des données
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
    Exporte les données dans un fichier CSV dans le dossier 'export'.
    """
    try:
        if not data_list:
            print("Aucune donnée à exporter.")
            return
        
        export_folder = 'export'
        if not os.path.exists(export_folder):
            os.makedirs(export_folder)

        # Créer un nom de fichier unique
        timestamp = time.strftime("%d%m%Y_%H%M%S")
        sanitized_category_name = re.sub(r'[^\w\-_\. ]', '_', category_name)
        filename = f"{sanitized_category_name}_{timestamp}.csv"
        file_path = os.path.join(export_folder, filename)
        
        # Récupérer les clés à partir du premier dictionnaire de la liste
        fieldnames = data_list[0].keys()
        
        # Écriture des données dans le fichier
        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames= fieldnames)
            writer.writeheader()
            writer.writerows(data_list)

        print(f"Données exportées avec succès dans {file_path}")
    except Exception as e:
        print(f"Erreur lors de l'exportation des données : {e}")

def main():
    url = input("Veuillez entrer l'URL que vous souhaitez scraper : ")

    # Valider l'URL
    if not validate_url(url):
        return

    # Récupérer la page
    soup = fetch_page(url)
    if not soup:
        return
    
    # Extraire les URLs des livres de cette catégorie
    book_urls = extract_urls_book(soup, url)
    
    # Extraire les données pour chaque livre
    product_data_list = []
    for book_url in book_urls:
        page_soup = fetch_page(book_url)
        if not page_soup:
            continue
        product_data, product_category = extract_product_data(page_soup, book_url)
        if product_data:
            product_data_list.append(product_data)
            category = product_category
            
    # Exporter les données
    if product_data_list:
        
        export_to_csv(product_data_list, category)

if __name__ == "__main__":
    main()
