import os
import hashlib
import requests
from bs4 import BeautifulSoup
import re

### Lies mich ###
## Das Skript ist in drei Teile unterteilt:
## - **Konfiguration**: Hier kann man Einstellungen wie die URL des Stundenplans, den Suchtext und die Speicherorte für Dateien ändern.
## -    **Funktionen**: Hier sind die Funktionen definiert, die im Hauptprogramm verwendet werden.
## - **Hauptprogramm**: Hier wird der Stundenplan heruntergeladen, analysiert und die Dateien werden kopiert oder ersetzt.
### ######### ###

### Konfiguration ###

timetable_url = "https://service.viona24.com/stpusnl/"   # URL der Webseite mit dem Stundenplan
search_text = re.compile(r"US IT 2024 Sommer FIAE [DE]") # RegEx für den gesuchten Text: Siehe https://regexr.com/85b01
dist_dir = './dist/'                                     # Temporärer Speicherort für heruntergeladene Dateien
docs_dir = './docs/'                                     # Endgültiger Speicherort für Dateien
#####################

########################## Funktionen ##########################

# Funktion zum Berechnen des Hashes einer Datei: Siehe https://de.wikipedia.org/wiki/Message-Digest_Algorithm_5 & https://www.md5hashgenerator.com/
# Wichtig: MD5 ist nicht mehr sicher! Verwenden Sie für sensible Daten z.B. SHA-256. Siehe weiter Zeile 71.
def file_hash(filepath):
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# Funktion zum Ersetzen oder Erstellen einer Datei: Siehe https://docs.python.org/3/library/os.html#os.replace
# Im Falle eines Fehlers wird das Programm mit Exit-Code 1 beendet.
def replace_or_create_file(dist_path, docs_path, action='Ersetzen'):
    try:
        os.replace(dist_path, docs_path)
    except Exception as e:
        print(f"Fehler beim {action} der Datei:", str(e))
        exit(1)

# Funktion zum Sicherstellen, dass die benötigten Verzeichnisse existieren: Siehe https://docs.python.org/3/library/os.html#os.makedirs
def create_directories(dir_paths):
    for dir_path in dir_paths:
        os.makedirs(dir_path, exist_ok=True)
        
# Funktion zum Herunterladen der Webseite mit dem Stundenplan.
# Im Falle eines Fehlers wird das Programm mit Exit-Code 1 beendet.
def fetch_timetable_response(timetable_url):
    response = requests.get(timetable_url)
    # Wenn der Statuscode nicht 200 ist, geben wir eine entsprechende Meldung aus und beenden das Programm mit Exit-Code 1.
    if response.status_code != 200: # HTTP-Statuscode 200 bedeutet, dass die Anfrage erfolgreich war. Siehe https://de.wikipedia.org/wiki/HTTP-Statuscode
        print("HTTP Fehler aufgetreten:", response.status_code)
        exit(1)
    return response

# Funktion zum Parsen des HTML-Dokuments und Rückgabe der Liste mit den li-Elementen.
# Im Falle eines Fehlers oder wenn keine li-Elemente gefunden wurden, wird das Programm mit Exit-Code 1 beendet.
def parse_timetable_html(response):
    try:
        # HTML parsen: Das HTML-Dokument wird in ein Objekt umgewandelt, das wir durchsuchen können.
        soup = BeautifulSoup(response.text, 'lxml')

        # Die Liste mit der ID 'thelist' finden -> <ul id="thelist">...</ul>. Diese Liste enthält für jeden Stundenplan ein <li>-Element.
        thelist = soup.find('ul', id='thelist')

        # Alle li-Elemente in der Liste abrufen: Ein li-Element entspricht einem Kurs im Stundenplan -> <li>...</li>
        li_list = thelist.find_all('li')

        # Falls keine li-Elemente gefunden wurden, geben wir eine entsprechende Meldung aus und beenden das Programm mit Exit-Code 1. Danke an @iptoux für den Hinweis.
        if not li_list or len(li_list) == 0:
            print("Keine li-Elemente gefunden.")
            exit(1) # Exit-Code 1 bedeutet, dass es keine Änderungen gab.
        
        return li_list
    except Exception as e:
        print("Fehler beim Parsen des HTML-Dokuments:", str(e))
        exit(1)
        

# Funktion zum Extrahieren der Dateiinformationen aus einem li-Element.
# Die Funktion gibt die folgenden Werte als Tuple zurück: Link zur Datei, Dateiname, Pfad zum temporären Speicherort, Pfad zum endgültigen Speicherort.
def extract_file_info(li, timetable_url, dist_dir, docs_dir):
    # Extrahiere den Link zur Datei
    link = li.find('a').get('href')

    # Erstelle den vollständigen Link zur Datei
    full_link = timetable_url + link.strip('./')
    
    # Extrahiere den Dateinamen aus dem Link
    filename = os.path.basename(link)
    
    # Erstelle den Pfad zum temporären Speicherort
    dist_path = os.path.join(dist_dir, filename)
    
    # Erstelle den Pfad zum endgültigen Speicherort
    docs_path = os.path.join(docs_dir, filename)
    
    # Gib die Werte als Tuple zurück
    return full_link, filename, dist_path, docs_path


# Funktion zum Herunterladen einer Datei von einem Link und Speichern im temporären Speicherort.
# Im Falle eines Fehlers wird das Programm mit Exit-Code 1 beendet.
def download_file(full_link, dist_path):
    try:
        # Datei herunterladen
        file_response = requests.get(full_link)
        file_response.raise_for_status()  # Überprüft, ob der Statuscode auf einen Fehler hinweist
        
        # Datei im temporären Speicherort speichern
        with open(dist_path, 'wb') as file:
            file.write(file_response.content)
        
        print(f"Datei erfolgreich heruntergeladen: {dist_path}")
        
    except Exception as e:
        # Fehlerbehandlung beim Herunterladen oder Speichern der Datei
        print(f"Fehler beim Herunterladen der Datei von {full_link}: {str(e)}")
        exit(1)

################################################################################

### Hauptprogramm ###

# Die oben definierten Verzeichnisse erstellen, wenn sie nicht existieren
create_directories([dist_dir, docs_dir])

# Die Webseite mit dem Stundenplan herunterladen
response = fetch_timetable_response(timetable_url)

# HTML parsen: Das HTML-Dokument wird in ein Objekt umgewandelt, das wir durchsuchen können:
# Wir erhalten eine Liste mit den li-Elementen, die die Kurse im Stundenplan repräsentieren.
li_list = parse_timetable_html(response)

# Variable, um zu verfolgen, ob neue Dateien gefunden wurden. Damit wir am Ende des Programms eine entsprechende Meldung ausgeben können.
new_files_found = False
        
# Alle li-Elemente in der Liste durchsuchen -> <li>...</li>
for li in li_list:
    # Den span mit der Klasse 'name' finden: Das Span-Element mit der Klasse 'name' enthält den Namen des Kurses -> <span class="name">$NAME_DES_KURSES</span>
    name_span = li.find('span', class_='name')
    
    # Überprüfen, ob der Kursname dem Suchtext entspricht: Siehe `search_text` oben.
    if name_span and search_text.search(name_span.get_text()):
        # Die Dateiinformationen aus dem li-Element extrahieren
        full_link, filename, dist_path, docs_path = extract_file_info(li, timetable_url, dist_dir, docs_dir)
        
        # Datei herunterladen und in `./dist/` temporär speichern.
        download_file(full_link, dist_path)
        
        # Prüfen, ob die Datei bereits in ./docs/ existiert
        if os.path.exists(docs_path):
            # Hash der heruntergeladenen Datei und der vorhandenen Datei vergleichen
            # Der Hash wird verwendet, um festzustellen, ob sich die Datei geändert hat.
            # Wenn sich auch nur ein einziges Bit in der Datei ändert, ändert sich auch der Hash -> Lawinenprinzip: https://de.wikipedia.org/wiki/Lawineneffekt_(Kryptographie)
            if file_hash(dist_path) != file_hash(docs_path):
                # Die Datei hat sich geändert. Daher ersetzen wir die alte Datei durch die neue im `./docs/`-Verzeichnis.
                print("Datei wurde aktualisiert:", filename)
                new_files_found = True
                replace_or_create_file(dist_path, docs_path, 'Ersetzen')
        else:
            # Die Datei existiert noch nicht in `./docs/`. Daher kopieren wir sie dorthin.
            print("Neue Datei gefunden:", filename)
            new_files_found = True
            replace_or_create_file(dist_path, docs_path, 'Kopieren')

# Wenn keine neuen Dateien gefunden wurden, geben wir eine entsprechende Meldung aus und beenden das Programm mit Exit-Code 1.
# Die Fehler-Codes sind standardisiert: Exit-Code 0 bedeutet, dass das Programm erfolgreich beendet wurde. Alle anderen Werte bedeuten, dass ein Fehler aufgetreten ist.
if not new_files_found:
    print("Keine neuen oder aktualisierten Dateien gefunden.")
    exit(1)
else:
    print("Neue oder aktualisierte Dateien gefunden und kopiert.")
    # Wenn neue Dateien gefunden wurden, beendet sich das Programm hier von selbst mit Exit-Code 0.