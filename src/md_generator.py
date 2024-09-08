import os
import re

### Konfiguration ###

base_dir = os.path.dirname(os.path.abspath(__file__)) # Basisverzeichnis des Skripts
dist_dir = f'{base_dir}/../dist/'                     # Die Stundenpläne befinden sich im dist-Ordner
output_md = f'{base_dir}/../dist/index.md'            # Speicherort und Name der generierten Markdown-Datei
filename_pattern = re.compile(r'US_IT_2024_Sommer_FIAE_([DE])_2024_abKW(\d{2})(?:_(\d+))?.pdf') # Muster: US_IT_2024_Sommer_FIAE_[D|E]_2024_abKW[xx](_[revision]).pdf
#####################

########################## Funktionen ##########################

# Funktion zum Auflisten der Dateien im dist-Ordner
def list_dist_files():
    # Überprüfen, ob der dist-Ordner existiert
    if not os.path.exists(dist_dir):
        print(f"Der Ordner {dist_dir} existiert nicht.")
        return []

    # Dateien im dist-Ordner auflisten
    files = os.listdir(dist_dir)

    if not files:
        print(f"Der Ordner {dist_dir} ist leer.")
    else:
        print(f"Dateien im Ordner {dist_dir}:")
        for file in files:
            print(file)

    return files

# Funktion zur Extraktion des Kurses, der KW und der Revisionen
def extract_file_info(files):
    file_structure = {'D': {}, 'E': {}}

    for file in files:
        match = filename_pattern.match(file)
        if match:
            course = match.group(1)  # D oder E
            kw = match.group(2)      # Kalenderwoche
            revision = match.group(3) or '100'  # Revision (falls keine vorhanden, setze '100' für "Aktuell")

            # Falls die KW noch nicht existiert, füge sie hinzu
            if kw not in file_structure[course]:
                file_structure[course][kw] = []

            # Füge die Datei mit ihrer Revision hinzu
            file_structure[course][kw].append((int(revision), file))

    # Sortiere die Dateien nach Revision absteigend (größte Revision zuerst, "Aktuell" = 100 an erster Stelle)
    for course in file_structure:
        for kw in file_structure[course]:
            # Sortiere die Dateien innerhalb jeder KW nach Revision absteigend
            file_structure[course][kw].sort(reverse=True)
            
            # Zähle die Anzahl der Dateien pro KW und ersetze die Revision 100 durch die entsprechende Zahl
            total_files = len(file_structure[course][kw])
            counter = total_files - 1  # Zähle von der höchsten Revisionsnummer abwärts

            for i, (rev, file) in enumerate(file_structure[course][kw]):
                if rev == 100:
                    file_structure[course][kw][i] = (counter, file)  # Setze auf die nächste Revision
                counter -= 1  # Für jede Datei die Revision verringern

    # Sortiere die Kurse nach KW absteigend
    for course in file_structure:
        file_structure[course] = dict(sorted(file_structure[course].items(), key=lambda x: int(x[0]), reverse=True))

    return file_structure

# Funktion zur Erstellung der Markdown-Datei
def generate_markdown(file_structure):
    with open(output_md, 'w', encoding='utf-8') as md_file:
        # Überschrift
        md_file.write("# Stundenpläne\n\n")

        # Verweise auf die aktuellsten Stundenpläne
        for course, kws in file_structure.items():
            latest_kw = next(iter(kws))  # Die KW der neuesten Stunde
            latest_file = kws[latest_kw][0][1]  # Die erste Datei in der neuesten KW (Aktuell)
            md_file.write(f"### [Aktuellster Plan Kurs {course} (KW {latest_kw})](./{latest_file})\n")
        
        # Historie der Stundenpläne
        md_file.write("\n---\n")
        md_file.write("\n# Historie der Stundenpläne\n\n")
        for course, kws in file_structure.items():
            md_file.write(f"## Kurs {course}:\n")
            for kw, files in kws.items():
                md_file.write(f"- **KW {kw}**:\n")
                for rev, file in files:
                    md_file.write(f"  - [Revision {rev}](./{file})\n")
            md_file.write("\n")

################################################################################

### Hauptprogramm ###

if __name__ == "__main__":
    # Listet die Dateien auf
    files = list_dist_files()

    # Extrahiere Kurs, KW und Revisionen
    file_structure = extract_file_info(files)

    # Generiere die Markdown-Datei
    generate_markdown(file_structure)

    print(f"Die Markdown-Datei wurde unter {output_md} erstellt.")
