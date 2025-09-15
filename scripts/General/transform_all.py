'''
Master-Skript zur Ausführung aller Transform-Skripte
Verwendung: py ./scripts/General/transform_all.py im LetsMeet-Ordner
'''

import subprocess
import sys
import os

def run_script(script_name):
    """Führt ein Python-Skript aus und gibt den Rückgabecode zurück"""
    script_path = os.path.join('scripts', script_name)
    print(f"\n{'='*60}")
    print(f"AUSFÜHRUNG: {script_name}")
    print(f"{'='*60}")

    try:
        result = subprocess.run([sys.executable, script_path],
                                capture_output=True, text=True, cwd='.')

        print(f"Return Code: {result.returncode}")
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        return result.returncode

    except Exception as e:
        print(f"Fehler beim Ausführen von {script_name}: {e}")
        return 1

def main():
    print("START: Ausführung aller Transform-Skripte")
    print("Reihenfolge: MongoDB → Excel → XML")

    # MongoDB zuerst (weil es Benutzer erstellt)
    return_code1 = run_script('transform_mongodb.py')

    # Dann Excel (aktualisiert Benutzer und fügt Hobbies/Städte hinzu)
    return_code2 = run_script('transform_excel.py')

    # Zuletzt XML (fügt zusätzliche Hobbies hinzu)
    return_code3 = run_script('transform_xml.py')

    print(f"\n{'='*60}")
    print("ZUSAMMENFASSUNG:")
    print(f"{'='*60}")
    print(f"MongoDB Transform: {'ERFOLGREICH' if return_code1 == 0 else 'FEHLGESCHLAGEN'}")
    print(f"Excel Transform:   {'ERFOLGREICH' if return_code2 == 0 else 'FEHLGESCHLAGEN'}")
    print(f"XML Transform:     {'ERFOLGREICH' if return_code3 == 0 else 'FEHLGESCHLAGEN'}")

    total_success = return_code1 + return_code2 + return_code3
    if total_success == 0:
        print("\n✅ ALLE TRANSFORMS ERFOLGREICH ABGESCHLOSSEN")
    else:
        print(f"\n⚠️  EINIGE TRANSFORMS HATTEN FEHLER (Gesamt-Fehlercode: {total_success})")

    return total_success

if __name__ == "__main__":
    sys.exit(main())