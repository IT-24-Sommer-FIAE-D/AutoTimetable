import os
import re

### Konfiguration ###

base_dir = os.path.dirname(os.path.abspath(__file__)) # Basisverzeichnis des Skripts
dist_dir = f'{base_dir}/../dist/'                     # Die Stundenpläne befinden sich im dist-Ordner
output_md = f'{base_dir}/../dist/index.md'            # Speicherort und Name der generierten Markdown-Datei

# Muster: US_IT_2024_Sommer_FIAE_[D|E]_2024_abKW[xx](_[revision]).pdf
filename_pattern = re.compile(
    r'US_IT_\d{4}_Sommer_FIAE_([DE])_(\d{4})_abKW(\d{2})(?:_(\d+))?\.pdf'
)
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

# Funktion zur Extraktion des Kurses, des Jahres, der KW und der Revisionen
def extract_file_info(files):
    # Struktur: {year: {'D': {kw: [(rev, file), ...]}, 'E': {...}}}
    file_structure = {}

    for file in files:
        match = filename_pattern.match(file)
        if match:
            course = match.group(1)    # D oder E
            year = match.group(2)      # Jahr (YYYY)
            kw = match.group(3)        # Kalenderwoche (2-stellig)
            revision = match.group(4) or '100'  # Revision (falls keine vorhanden, setze '100' für "Aktuell")

            if year not in file_structure:
                file_structure[year] = {'D': {}, 'E': {}}

            # Falls die KW noch nicht existiert, füge sie hinzu
            if kw not in file_structure[year][course]:
                file_structure[year][course][kw] = []

            # Füge die Datei mit ihrer Revision hinzu
            file_structure[year][course][kw].append((int(revision), file))

    # Sortiere Dateien innerhalb jeder (year, course, kw)
    for year in file_structure:
        for course in file_structure[year]:
            for kw in file_structure[year][course]:
                file_structure[year][course][kw].sort(reverse=True)

                total_files = len(file_structure[year][course][kw])
                counter = total_files - 1
                for i, (rev, file) in enumerate(file_structure[year][course][kw]):
                    if rev == 100:
                        file_structure[year][course][kw][i] = (counter, file)
                    counter -= 1

            # KWs absteigend sortieren (wie vorher)
            file_structure[year][course] = dict(
                sorted(file_structure[year][course].items(), key=lambda x: int(x[0]), reverse=True)
            )

    # Jahre absteigend sortieren
    file_structure = dict(sorted(file_structure.items(), key=lambda x: int(x[0]), reverse=True))

    return file_structure

# Funktion zur Erstellung der Markdown-Datei
def generate_markdown(file_structure):
    with open(output_md, 'w', encoding='utf-8') as md_file:
        # Überschrift
        md_file.write("# Stundenpläne\n\n")

        # Finde das aktuellste Jahr
        latest_year = next(iter(file_structure), None)

        for year, courses in file_structure.items():
            md_file.write(f"## Jahr {year}\n\n")

            # Verweise auf die aktuellsten Stundenpläne (pro Kurs innerhalb des aktuellsten Jahres)
            if year == latest_year:
                for course, kws in courses.items():
                    if not kws:
                        continue
                    latest_kw = next(iter(kws))
                    latest_file = kws[latest_kw][0][1]
                    md_file.write(f"### [Aktuellster Plan Kurs {course} (KW {latest_kw})](./{latest_file})\n")
                    md_file.write("\n---\n")

            # Historie der Stundenpläne
            md_file.write("\n### Historie der Stundenpläne\n\n")
            for course, kws in courses.items():
                md_file.write(f"#### Kurs {course}:\n")
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

    # Extrahiere Kurs, Jahr, KW und Revisionen
    file_structure = extract_file_info(files)

    # Generiere die Markdown-Datei
    generate_markdown(file_structure)

    print(f"Die Markdown-Datei wurde unter {output_md} erstellt.")
