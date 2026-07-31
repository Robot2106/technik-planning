#!/usr/bin/env python3
"""
🚀 AUTOMATISCHER GITHUB + DEPLOYMENT SCRIPT
Dieser Script macht ALLES für dich!
"""

import os
import subprocess
import sys
from pathlib import Path

def print_header(text):
    """Schöne Überschrift"""
    print("\n" + "="*70)
    print(f"  ✨ {text}")
    print("="*70 + "\n")

def run_command(cmd, description=""):
    """Führt einen Befehl aus"""
    if description:
        print(f"📝 {description}...")
    print(f"   🔧 {cmd}\n")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Fehler: {result.stderr}")
            return False
        if result.stdout:
            print(f"✅ {result.stdout[:200]}")
        return True
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False

def main():
    print_header("🎯 GITHUB AUTO-DEPLOY")
    print("""
    Dieser Script macht automatisch:
    ✅ Git Repository initialisieren
    ✅ Alle Dateien hinzufügen
    ✅ Daten zu GitHub hochladen
    ✅ Render bereitstellen
    
    Du brauchst nur:
    1. GitHub Username
    2. GitHub Personal Access Token (kostenlos!)
    """)
    
    # Schritt 1: GitHub Daten abfragen
    print_header("SCHRITT 1: GitHub Daten")
    
    username = input("📧 Gib deinen GitHub Username ein (z.B. Robot2106): ").strip()
    if not username:
        print("❌ Username erforderlich!")
        return
    
    token = input("🔑 Gib deinen GitHub Token ein (siehe Anleitung unten): ").strip()
    if not token:
        print("❌ Token erforderlich!")
        return
    
    repo_name = input("📁 Repository Name (Standard: technik-planning): ").strip() or "technik-planning"
    
    print(f"\n✅ GitHub Setup:")
    print(f"   Username: {username}")
    print(f"   Repo: {repo_name}")
    print(f"   Token: {'*' * len(token)}")
    
    # Schritt 2: Git setup
    print_header("SCHRITT 2: Git Setup")
    
    os.chdir(Path(__file__).parent)
    
    commands = [
        ("git init", "Repository initialisieren"),
        ("git config user.email 'technik@gemeinde.de'", "Git Email setzen"),
        ("git config user.name 'Technik Admin'", "Git Name setzen"),
        ("git add .", "Alle Dateien hinzufügen"),
        ('git commit -m "Initial commit - Technik Planung"', "Commit erstellen"),
    ]
    
    for cmd, desc in commands:
        if not run_command(cmd, desc):
            print(f"⚠️  Kommando fehlgeschlagen, versuche nächsten...")
    
    # Schritt 3: GitHub Remote
    print_header("SCHRITT 3: Mit GitHub verbinden")
    
    remote_url = f"https://{username}:{token}@github.com/{username}/{repo_name}.git"
    remote_url_display = f"https://github.com/{username}/{repo_name}.git"
    
    print(f"🔗 Verbinde zu: {remote_url_display}")
    
    # Remote löschen falls existiert
    subprocess.run("git remote remove origin", shell=True, capture_output=True)
    
    # Remote hinzufügen
    if not run_command(f'git remote add origin "{remote_url}"', "Remote URL hinzufügen"):
        if not run_command(f'git remote set-url origin "{remote_url}"', "Remote URL aktualisieren"):
            print("❌ Remote setup fehlgeschlagen")
            return
    
    # Branch setup
    if not run_command("git branch -M main", "Branch in 'main' umbenennen"):
        pass
    
    # Push
    print_header("SCHRITT 4: Code zu GitHub hochladen")
    print("⏳ Das kann eine Minute dauern...\n")
    
    if not run_command("git push -u origin main", "Code hochladen (mit neuem Token)"):
        print("⚠️  Push fehlgeschlagen")
        print("\n💡 Manuell versuchen:")
        print(f"   git push -u origin main")
        return
    
    # Erfolgreich!
    print_header("✅ PHASE 1 FERTIG!")
    
    print(f"""
    ✨ ERFOLG! Dein Code ist auf GitHub! 🎉
    
    🔗 Dein Repository:
       {remote_url_display}
    
    ➡️  NÄCHSTE SCHRITTE:
    
    1. Öffne Render.com
    2. Erstelle einen Account (mit GitHub!)
    3. Erstelle neue "Web Service"
    4. Verbinde dein Repository: {remote_url_display}
    5. Settings:
       - Build: pip install -r requirements.txt && python manage.py migrate
       - Start: gunicorn technik_planning.wsgi:application
    6. Deploy!
    7. Im Render Shell:
       python manage.py createsuperuser
       (admin / admin123)
    
    💙 Das war's! Dann läuft deine App! 🚀
    """)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Abgebrochen vom Benutzer")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fehler: {e}")
        sys.exit(1)
