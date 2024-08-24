import os
import hashlib
import requests
from bs4 import BeautifulSoup

# Configuration
timetable_url = "https://service.viona24.com/stpusnl/"
search_text = "US IT 2024 Sommer FIAE D"
dist_dir = './dist/' # Temporärer Speicherort für heruntergeladene Dateien
docs_dir = './docs/' # Endgültiger Speicherort für Dateien

# Funktion zum Berechnen des Hashes einer Datei
def file_hash(filepath):
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

################################################################################

# Die Verzeichnisse erstellen, falls sie nicht existieren
os.makedirs(dist_dir, exist_ok=True)
os.makedirs(docs_dir, exist_ok=True)

# Webseite herunterladen
response = requests.get(timetable_url)
response.raise_for_status() # Wirft eine Exception, wenn ein HTTP-Fehler auftritt

# HTML parsen
soup = BeautifulSoup(response.text, 'lxml')

# Die Liste mit der ID 'thelist' finden -> <ul id="thelist">...</ul>
thelist = soup.find('ul', id='thelist')

# Variable, um zu verfolgen, ob neue Dateien gefunden wurden
new_files_found = False

# Alle li-Elemente in der Liste durchsuchen -> <li>...</li>
for li in thelist.find_all('li'):
    # Den span mit der Klasse 'name' finden: Das Span-Element mit der Klasse 'name' enthält den Namen des Kurses.
    name_span = li.find('span', class_='name')
    
    # Überprüfen, ob der Name den gesuchten Text enthält
    if name_span and search_text in name_span.get_text():
        # Das href-Attribut des a-Tags extrahieren
        link = li.find('a').get('href')
        full_link = timetable_url + link.strip('./')
        filename = os.path.basename(link)
        dist_path = os.path.join(dist_dir, filename)
        docs_path = os.path.join(docs_dir, filename)
        
        # Datei herunterladen und in ./dist/ speichern
        file_response = requests.get(full_link)
        with open(dist_path, 'wb') as file:
            file.write(file_response.content)
        
        # Prüfen, ob die Datei bereits in ./docs/ existiert
        if os.path.exists(docs_path):
            # Hash der heruntergeladenen Datei und der vorhandenen Datei vergleichen
            # Ein Hash ist eine eindeutige Zeichenfolge, die den Inhalt einer Datei repräsentiert
            if file_hash(dist_path) != file_hash(docs_path):
                # Datei ist neuer oder hat sich geändert, kopieren
                new_files_found = True
                os.replace(dist_path, docs_path)
        else:
            # Datei ist neu, kopieren
            new_files_found = True
            os.replace(dist_path, docs_path)

# Programm mit Fehlercode beenden, wenn keine neuen Dateien vorhanden sind.
# Der Workflow beachtet den Fehlercode und erstellt keinen Release, wenn das Skript mit einem Fehlercode beendet wird.
if not new_files_found:
    print("No new or updated files found.")
    exit(1)
else:
    print("New or updated files were found and copied.")
