#!/usr/bin/env python3
"""
🚀 GITHUB FIX - Wenn der erste Script nicht funktioniert hat
"""

import os
import subprocess
import sys

def run_cmd(cmd):
    """Führt Befehl aus"""
    print(f"🔧 {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Fehler: {result.stderr}")
        return False
    print(f"✅ OK\n")
    return True

print("\n" + "="*70)
print("  🚀 GITHUB FIX - Dateien hochladen")
print("="*70 + "\n")

# Abfrage
username = input("GitHub Username (z.B. Robot2106): ").strip()
repo = input("Repository Name (z.B. technik-planning): ").strip()
token = input("GitHub Token (ghp_...): ").strip()

if not all([username, repo, token]):
    print("❌ Alle Felder erforderlich!")
    sys.exit(1)

print(f"\n✓ Username: {username}")
print(f"✓ Repo: {repo}")
print(f"✓ Token: {'*' * len(token)}\n")

# Git init
print("1️⃣  Git initialisieren...")
run_cmd("git init")
run_cmd("git config user.email 'admin@gemeinde.de'")
run_cmd("git config user.name 'Admin'")

# Add und Commit
print("2️⃣  Dateien hinzufügen...")
run_cmd("git add .")
run_cmd('git commit -m "Technik Planung - Initial"')

# Remote
print("3️⃣  Mit GitHub verbinden...")
url = f"https://{username}:{token}@github.com/{username}/{repo}.git"
subprocess.run("git remote remove origin", shell=True, capture_output=True)
run_cmd(f'git remote add origin "{url}"')

# Push
print("4️⃣  Zu GitHub hochladen...")
run_cmd("git branch -M main")
if not run_cmd("git push -u origin main"):
    print("⚠️  Push fehlgeschlagen")
    print("\nVersuche mit --force...")
    run_cmd("git push -u origin main --force")

print("\n" + "="*70)
print("  ✨ FERTIG!")
print("="*70)
print(f"""
✅ Dein Code ist auf GitHub!

🔗 Schau hier nach:
   https://github.com/{username}/{repo}

➡️  NÄCHSTER SCHRITT:
   1. Öffne: https://render.com
   2. Sign up (mit GitHub)
   3. Neue Web Service
   4. Repository verbinden: {repo}
   5. Deploy!

💙 Alles Gute!
""")
