import requests
import re
import csv
import os
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

url = input("Veuillez entrer l'URL que vous souhaitez scraper : ")

base_url = 'https://books.toscrape.com/'

expected_prefix = "https://books.toscrape.com/catalogue"

if not url.startswith(expected_prefix):
    print(f"Erreur : L'URL doit commencer par {expected_prefix}")
else:
    try:
        page = requests.get(url, timeout=10)  
        if page.status_code == 200:
            soup = BeautifulSoup(page.content, "html.parser")
            
            product_page_url = url
            title = soup.find("h1").string
        
            product_image_active = soup.find("div",class_="item active")
           
            if product_image_active:
                img_tag = product_image_active.find("img")
                if img_tag and 'src' in img_tag.attrs:
                    relative_img_url = img_tag['src']
                    absolute_img_url = urljoin(base_url, relative_img_url)
                    image_url = absolute_img_url
                else:
                    image_url = 'Information non disponible'
            else:
                image_url = 'Information non disponible'
            
            product_description_section = soup.find(id="product_description")
              
            if product_description_section:
                next_element = product_description_section.find_next("p")
                if next_element:
                    product_description = next_element.text.strip()  
                else:
                    product_description = 'Information non disponible'
            else:
                product_description = 'Information non disponible'
            
            product_page = soup.find("article",class_="product_page")
           
            if product_page:
                table = product_page.find("table")
                if table:
                    product_info = {}
                    for row in table.find_all("tr"):
                        header = row.find("th")  
                        data = row.find("td") 

                        if header and data:  
                            key = header.text.strip()  
                            value = data.text.strip() 
                            product_info[key] = value  

                else:
                    product_info = {}
            else:
                product_info = {}
                
            upc = product_info.get('UPC', 'Information non disponible')
            price_excluding_taxe = product_info.get('Price (excl. tax)', 'Information non disponible')
            price_including_taxe = product_info.get('Price (incl. tax)', 'Information non disponible')
            availability = product_info.get('Availability', 'Information non disponible')
            number_available = re.search(r'\((\d+)', availability).group(1) if 'Availability' in product_info else 'Information non disponible'
            
            breadcrumb_items = soup.select("ul.breadcrumb li")
            
            category = breadcrumb_items[1].get_text(strip=True) if len(breadcrumb_items) > 1 else "Information non disponible"
            
            product_review_rating = soup.find('p', class_='star-rating') 
            
            if  product_review_rating :
                rating_class = product_review_rating.get('class')[1]  
    
                rating_map = {
                    'One': 1,
                    'Two': 2,
                    'Three': 3,
                    'Four': 4,
                    'Five': 5
                }

                review_rating = rating_map.get(rating_class, 0)  
                
            else:
                review_rating = 'Information non disponible'
                
            data_to_export = {
                'product_page_url': product_page_url,
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
            
            export_folder = 'export'
            if not os.path.exists(export_folder):
                os.makedirs(export_folder)
                
            timestamp = time.strftime("%Y%m%d_%H%M%S")  
            filename = f"{title.replace(' ', '_')}_{timestamp}.csv"  
            file_path = os.path.join(export_folder, filename)
            
            file_exists = False
            try:
                with open(file_path, mode='r'):
                    file_exists = True
            except FileNotFoundError:
                pass
            
            with open(file_path, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=data_to_export.keys())
                
                if not file_exists:
                    writer.writeheader()  
                
                writer.writerow(data_to_export)  

            print(f"Les informations ont été exportées dans {file_path}")
        else:
            print(f"Erreur : Impossible de récupérer la page. Code statut : {page.status_code}")
    except requests.exceptions.MissingSchema:
        print("Erreur : L'URL entrée n'est pas valide. Assurez-vous qu'elle commence par 'http://' ou 'https://'.")
    except requests.exceptions.RequestException as e:
        print(f"Une erreur est survenue : {e}")
