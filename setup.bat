@echo off
REM 🚀 TECHNIK PLANNING - WINDOWS SETUP SCRIPT

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  🚀 CHRISTUSGEMEINDE TECHNIKPLANUNG - AUTO SETUP          ║
echo ║     Alle Schritte werden automatisch durchgeführt         ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM ============================================================================
REM 1. VIRTUAL ENVIRONMENT
REM ============================================================================

echo 📦 Schritt 1/6: Virtual Environment erstellen...

if not exist "venv" (
    python -m venv venv
    echo    ✓ Virtual Environment erstellt
) else (
    echo    ✓ Virtual Environment existiert bereits
)

call venv\Scripts\activate.bat
echo.

REM ============================================================================
REM 2. DEPENDENCIES
REM ============================================================================

echo 📚 Schritt 2/6: Python-Abhängigkeiten installieren...
pip install -q -r requirements.txt
echo    ✓ Alle Abhängigkeiten installiert
echo.

REM ============================================================================
REM 3. .ENV DATEI
REM ============================================================================

echo ⚙️  Schritt 3/6: .env Datei vorbereiten...

if not exist ".env" (
    python -c "from django.core.management.utils import get_random_secret_key; print('SECRET_KEY=' + get_random_secret_key())" > temp_key.txt
    
    (
        echo # Django-Konfiguration
        for /f "delims=" %%i in (temp_key.txt) do echo %%i
        echo DEBUG=True
        echo ALLOWED_HOSTS=localhost,127.0.0.1
        echo.
        echo # Datenbank
        echo DB_ENGINE=django.db.backends.sqlite3
        echo DB_NAME=db.sqlite3
        echo.
        echo # E-Mail (Console für Entwicklung)
        echo EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
        echo EMAIL_HOST=smtp.gmail.com
        echo EMAIL_PORT=587
        echo EMAIL_USE_TLS=True
        echo EMAIL_HOST_USER=your-email@gmail.com
        echo EMAIL_HOST_PASSWORD=your-app-password
        echo DEFAULT_FROM_EMAIL=noreply@christusgemeinde.de
        echo.
        echo # Website
        echo SITE_URL=http://localhost:8000
    ) > .env
    
    del temp_key.txt
    echo    ✓ .env Datei erstellt (mit sicherer SECRET_KEY)
) else (
    echo    ✓ .env Datei existiert bereits
)
echo.

REM ============================================================================
REM 4. DATENBANK MIGRATIONS
REM ============================================================================

echo 🗄️  Schritt 4/6: Datenbank vorbereiten & Migrationen...
python manage.py migrate --noinput
echo    ✓ Datenbank migriert
echo.

REM ============================================================================
REM 5. ADMIN-USER
REM ============================================================================

echo 👤 Schritt 5/6: Admin-Benutzer erstellen...

python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print('exists' if User.objects.filter(username='admin').exists() else 'not_exists')" > admin_check.txt
set /p ADMIN_EXISTS=<admin_check.txt
del admin_check.txt

if "%ADMIN_EXISTS%"=="not_exists" (
    python manage.py shell << END
from django.contrib.auth.models import User
from planning.models import UserProfile

admin = User.objects.create_superuser('admin', 'admin@christusgemeinde.de', 'admin123')
UserProfile.objects.get_or_create(user=admin)
print("Admin-User erstellt: admin / admin123")
END
    echo    ✓ Admin-Benutzer erstellt (admin / admin123)
) else (
    echo    ✓ Admin-Benutzer existiert bereits
)
echo.

REM ============================================================================
REM 6. DEMO-DATEN
REM ============================================================================

echo 🎬 Schritt 6/6: Demo-Daten laden...

python manage.py shell -c "from planning.models import Event; print(Event.objects.count())" > event_check.txt
set /p EVENT_COUNT=<event_check.txt
del event_check.txt

if "%EVENT_COUNT%"=="0" (
    python manage.py load_demo_data
    echo    ✓ Demo-Daten geladen
) else (
    echo    ✓ Demo-Daten existieren bereits
)
echo.

REM ============================================================================
REM FERTIG!
REM ============================================================================

echo ╔════════════════════════════════════════════════════════════╗
echo ║  ✅ SETUP ABGESCHLOSSEN - ALLES IST BEREIT!              ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 🚀 APP STARTEN:
echo    python manage.py runserver
echo.
echo 📍 ZUGRIFF:
echo    App:        http://localhost:8000
echo    Admin:      http://localhost:8000/admin
echo.
echo 🔑 STANDARD-ANMELDEDATEN:
echo    Admin-User:     admin / admin123
echo    Demo-Benutzer:  anna / demo123
echo    Demo-Benutzer:  bob / demo123
echo    Demo-Benutzer:  clara / demo123
echo.
echo 💡 ERSTE SCHRITTE:
echo    1. Admin anmelden (admin / admin123)
echo    2. Zu 'Termine' gehen
echo    3. Demo-Events sehen
echo    4. 'Auto-Zuteilung' klicken
echo    5. Einsatzplan wird automatisch erstellt!
echo.
echo    ODER: Starten Sie jetzt: python manage.py runserver
echo.
pause
