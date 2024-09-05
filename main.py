import os
import hashlib
import requests
from bs4 import BeautifulSoup
import re

### Konfiguration ###
timetable_url = "https://service.viona24.com/stpusnl/"   # URL der Webseite mit dem Stundenplan
search_text = re.compile(r"US IT 2024 Sommer FIAE [DE]") # RegEx für den gesuchten Text: Siehe https://regexr.com/85b01
dist_dir = './dist/'                                     # Temporärer Speicherort für heruntergeladene Dateien
docs_dir = './docs/'                                     # Endgültiger Speicherort für Dateien
#####################

# Funktion zum Berechnen des Hashes einer Datei: Siehe https://de.wikipedia.org/wiki/Message-Digest_Algorithm_5 & https://www.md5hashgenerator.com/
# Wichtig: MD5 ist nicht mehr sicher! Verwenden Sie für sensible Daten z.B. SHA-256. Siehe weiter Zeile 71.
def file_hash(filepath):
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

################################################################################

# Die oben definierten Verzeichnisse erstellen, wenn sie nicht existieren
os.makedirs(dist_dir, exist_ok=True)
os.makedirs(docs_dir, exist_ok=True)

# Die Webseite mit dem Stundenplan herunterladen
response = requests.get(timetable_url)
# Wenn der Statuscode nicht 200 ist, geben wir eine entsprechende Meldung aus und beenden das Programm mit Exit-Code 1.
if response.status_code != 200: # HTTP-Statuscode 200 bedeutet, dass die Anfrage erfolgreich war. Siehe https://de.wikipedia.org/wiki/HTTP-Statuscode
    print("HTTP Fehler aufgetreten:", response.status_code)
    exit(1)

# HTML parsen: Das HTML-Dokument wird in ein Objekt umgewandelt, das wir durchsuchen können.
soup = BeautifulSoup(response.text, 'lxml')

# Die Liste mit der ID 'thelist' finden -> <ul id="thelist">...</ul>. Diese Liste enthält für jeden Stundenplan ein <li>-Element.
thelist = soup.find('ul', id='thelist')

# Variable, um zu verfolgen, ob neue Dateien gefunden wurden. Damit wir am Ende des Programms eine entsprechende Meldung ausgeben können.
new_files_found = False

# Alle li-Elemente in der Liste abrufen: Ein li-Element entspricht einem Kurs im Stundenplan -> <li>...</li>
li_list = thelist.find_all('li')

# Falls keine li-Elemente gefunden wurden, geben wir eine entsprechende Meldung aus und beenden das Programm mit Exit-Code 1. Danke an @iptoux für den Hinweis.
if not li_list:
    print("Keine li-Elemente gefunden.")
    exit(1) # Exit-Code 1 bedeutet, dass es keine Änderungen gab.

# Alle li-Elemente in der Liste durchsuchen -> <li>...</li>
for li in li_list:
    # Den span mit der Klasse 'name' finden: Das Span-Element mit der Klasse 'name' enthält den Namen des Kurses -> <span class="name">...</span>
    name_span = li.find('span', class_='name')
    
    # Überprüfen, ob der Kursname dem Suchtext entspricht: Siehe `search_text` oben.
    if name_span and search_text.search(name_span.get_text()):
        # Das href-Attribut des a-Tags extrahieren. Das href-Attribut enthält den Link zur Datei -> <a href="...">...</a>
        link = li.find('a').get('href')
        full_link = timetable_url + link.strip('./') # Den vollständigen Link zur Datei erstellen
        filename = os.path.basename(link)            # Den Dateinamen extrahieren
        dist_path = os.path.join(dist_dir, filename) # Pfad zum temporären Speicherort
        docs_path = os.path.join(docs_dir, filename) # Pfad zum endgültigen Speicherort
        
        # Datei herunterladen und in `./dist/` temporär speichern.
        file_response = requests.get(full_link)
        with open(dist_path, 'wb') as file:
            file.write(file_response.content)
        
        # Prüfen, ob die Datei bereits in ./docs/ existiert
        if os.path.exists(docs_path):
            # Hash der heruntergeladenen Datei und der vorhandenen Datei vergleichen
            # Der Hash wird verwendet, um festzustellen, ob sich die Datei geändert hat.
            # Wenn sich auch nur ein einziges Bit in der Datei ändert, ändert sich auch der Hash -> Lawinenprinzip: https://de.wikipedia.org/wiki/Lawineneffekt_(Kryptographie)
            if file_hash(dist_path) != file_hash(docs_path):
                # Die Datei hat sich geändert. Daher ersetzen wir die alte Datei durch die neue im `./docs/`-Verzeichnis.
                new_files_found = True
                os.replace(dist_path, docs_path)
        else:
            # Die Datei existiert noch nicht in `./docs/`. Daher kopieren wir sie dorthin.
            new_files_found = True
            os.replace(dist_path, docs_path)

# Wenn keine neuen Dateien gefunden wurden, geben wir eine entsprechende Meldung aus und beenden das Programm mit Exit-Code 1.
# Die Fehler-Codes sind standardisiert: Exit-Code 0 bedeutet, dass das Programm erfolgreich beendet wurde. Alle anderen Werte bedeuten, dass ein Fehler aufgetreten ist.
if not new_files_found:
    print("Keine neuen oder aktualisierten Dateien gefunden.")
    exit(1)
else:
    print("Neue oder aktualisierte Dateien gefunden und kopiert.")
    # Wenn neue Dateien gefunden wurden, beendet sich das Programm hier von selbst mit Exit-Code 0.