#!/usr/bin/env python
"""
🚀 TECHNIK PLANNING - UNIVERSALES SETUP SCRIPT
Funktioniert auf Windows, Linux und macOS!
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(cmd, description):
    """Führt einen Shell-Befehl aus"""
    print(f"   {description}...", end=" ", flush=True)
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode == 0:
            print("✓")
            return True
        else:
            print(f"✗\n      {result.stderr}")
            return False
    except Exception as e:
        print(f"✗\n      {e}")
        return False

def main():
    print("\n" + "="*70)
    print("║  🚀 CHRISTUSGEMEINDE TECHNIKPLANUNG - AUTO SETUP          ")
    print("║     Alle Schritte werden automatisch durchgeführt         ")
    print("="*70)
    print()
    
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # ============================================================================
    # 1. VIRTUAL ENVIRONMENT
    # ============================================================================
    
    print("📦 Schritt 1/6: Virtual Environment")
    
    venv_path = "venv"
    if not os.path.exists(venv_path):
        run_command(f"{sys.executable} -m venv venv", "Erstelle Virtual Environment")
    else:
        print("   ✓ Virtual Environment existiert bereits")
    
    print()
    
    # Bestimme Python-Interpreter im venv
    if platform.system() == "Windows":
        python_exe = os.path.join(venv_path, "Scripts", "python.exe")
        pip_exe = os.path.join(venv_path, "Scripts", "pip.exe")
    else:
        python_exe = os.path.join(venv_path, "bin", "python")
        pip_exe = os.path.join(venv_path, "bin", "pip")
    
    # ============================================================================
    # 2. DEPENDENCIES
    # ============================================================================
    
    print("📚 Schritt 2/6: Python-Abhängigkeiten")
    run_command(f"{pip_exe} install -q -r requirements.txt", "Installiere Abhängigkeiten")
    print()
    
    # ============================================================================
    # 3. .ENV DATEI
    # ============================================================================
    
    print("⚙️  Schritt 3/6: .env Datei")
    
    if not os.path.exists(".env"):
        # Sichere SECRET_KEY generieren
        result = subprocess.run(
            f"{python_exe} -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\"",
            shell=True,
            capture_output=True,
            text=True
        )
        secret_key = result.stdout.strip()
        
        env_content = f"""# Django-Konfiguration
SECRET_KEY={secret_key}
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Datenbank
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# E-Mail (Console für Entwicklung)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@christusgemeinde.de

# Website
SITE_URL=http://localhost:8000
"""
        
        with open(".env", "w") as f:
            f.write(env_content)
        
        print("   ✓ .env Datei erstellt (mit sicherer SECRET_KEY)")
    else:
        print("   ✓ .env Datei existiert bereits")
    
    print()
    
    # ============================================================================
    # 4. DATENBANK MIGRATIONS
    # ============================================================================
    
    print("🗄️  Schritt 4/6: Datenbank & Migrationen")
    run_command(f"{python_exe} manage.py migrate --noinput", "Führe Migrationen durch")
    print()
    
    # ============================================================================
    # 5. ADMIN-USER
    # ============================================================================
    
    print("👤 Schritt 5/6: Admin-Benutzer")
    
    # Prüfe ob Admin existiert
    check_cmd = f"{python_exe} manage.py shell -c \"from django.contrib.auth.models import User; print('exists' if User.objects.filter(username='admin').exists() else 'not_exists')\""
    result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
    
    if "not_exists" in result.stdout:
        create_admin_script = f"""
from django.contrib.auth.models import User
from planning.models import UserProfile

admin = User.objects.create_superuser('admin', 'admin@christusgemeinde.de', 'admin123')
UserProfile.objects.get_or_create(user=admin)
print("Admin-User erstellt: admin / admin123")
"""
        
        result = subprocess.run(
            f"{python_exe} manage.py shell",
            shell=True,
            input=create_admin_script,
            capture_output=True,
            text=True
        )
        
        print("   ✓ Admin-Benutzer erstellt (admin / admin123)")
    else:
        print("   ✓ Admin-Benutzer existiert bereits")
    
    print()
    
    # ============================================================================
    # 6. DEMO-DATEN
    # ============================================================================
    
    print("🎬 Schritt 6/6: Demo-Daten")
    
    # Prüfe ob Events existieren
    check_cmd = f"{python_exe} manage.py shell -c \"from planning.models import Event; print(Event.objects.count())\""
    result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout.strip() == "0":
        run_command(f"{python_exe} manage.py load_demo_data", "Laden Demo-Daten")
    else:
        print("   ✓ Demo-Daten existieren bereits")
    
    print()
    
    # ============================================================================
    # FERTIG!
    # ============================================================================
    
    print("="*70)
    print("║  ✅ SETUP ABGESCHLOSSEN - ALLES IST BEREIT!              ")
    print("="*70)
    print()
    print("🚀 APP STARTEN:")
    print(f"   {python_exe} manage.py runserver")
    print()
    print("📍 ZUGRIFF:")
    print("   App:        http://localhost:8000")
    print("   Admin:      http://localhost:8000/admin")
    print()
    print("🔑 STANDARD-ANMELDEDATEN:")
    print("   Admin-User:     admin / admin123")
    print("   Demo-Benutzer:  anna / demo123")
    print("   Demo-Benutzer:  bob / demo123")
    print("   Demo-Benutzer:  clara / demo123")
    print()
    print("💡 ERSTE SCHRITTE:")
    print("   1. Admin anmelden (admin / admin123)")
    print("   2. Zu 'Termine' gehen")
    print("   3. Demo-Events sehen")
    print("   4. 'Auto-Zuteilung' klicken")
    print("   5. Einsatzplan wird automatisch erstellt! 🎉")
    print()

if __name__ == "__main__":
    main()
