# OC_project_1

Ce projet fait partie du cours de développement Python d'OpenClassrooms. Le but de ce projet est d'utiliser les bases de Python pour analyser des pages web.

## Description

Ce projet consiste à scraper des informations à partir du site [Books to Scrape](https://books.toscrape.com/). Le script `extract.py` permet, à partir de la page d'accueil du site, de trier les livres par catégorie et d'extraire de chaque livre les informations suivantes  :
- URL de la page produit
- Titre du livre
- Description du produit
- UPC
- Prix hors taxes
- Prix toutes taxes comprises
- Disponibilité
- Nombre d'exemplaires disponibles
- Catégorie
- URL de l'image du produit

## Prérequis

- Python 3.x
- Git
- Les bibliothèques suivantes :
  - `requests`
  - `beautifulsoup4`

## Installation

1. Clonez ce dépôt :
    Dans un terminal, exécuter la commande suivante : 
    git clone https://github.com/xavierjeanne/OC_project_1.git

2. Accéder au répertoire du projet :
    cd Oc_project_1

3. Créer un environnement virtuel, l'activer puis installer les dépendances :
    python -m venv env
    source env\Scripts\activate
    pip install -r requirements.txt

4. Executer le script :
    python extract.py

5. Récupérer les fichier générés dans le dossier export et utiliser un logiciel pouvant importer des fichiers CSV (Excel par exemple) pour voir les informations extraites

