#!/bin/bash

# 🚀 TECHNIK PLANNING - VOLLAUTOMATISCHES SETUP
# Dieses Script macht ALLES fertig - keine manuelle Arbeit nötig!

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🚀 CHRISTUSGEMEINDE TECHNIKPLANUNG - AUTO SETUP          ║"
echo "║     Alle Schritte werden automatisch durchgeführt         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# 1. VIRTUAL ENVIRONMENT
# ============================================================================

echo "📦 Schritt 1/6: Virtual Environment erstellen..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   ✓ Virtual Environment erstellt"
else
    echo "   ✓ Virtual Environment existiert bereits"
fi

# Aktivieren
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null

echo ""

# ============================================================================
# 2. DEPENDENCIES
# ============================================================================

echo "📚 Schritt 2/6: Python-Abhängigkeiten installieren..."
pip install -q -r requirements.txt
echo "   ✓ Alle Abhängigkeiten installiert"
echo ""

# ============================================================================
# 3. .ENV DATEI
# ============================================================================

echo "⚙️  Schritt 3/6: .env Datei vorbereiten..."

if [ ! -f ".env" ]; then
    # Sichere SECRET_KEY generieren
    SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    
    # .env erstellen mit sicherer SECRET_KEY
    cat > .env << EOF
# Django-Konfiguration
SECRET_KEY=$SECRET_KEY
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
EOF
    echo "   ✓ .env Datei erstellt (mit sicherer SECRET_KEY)"
else
    echo "   ✓ .env Datei existiert bereits"
fi
echo ""

# ============================================================================
# 4. DATENBANK MIGRATIONS
# ============================================================================

echo "🗄️  Schritt 4/6: Datenbank vorbereiten & Migrationen..."
python manage.py migrate --noinput
echo "   ✓ Datenbank migriert"
echo ""

# ============================================================================
# 5. ADMIN-USER
# ============================================================================

echo "👤 Schritt 5/6: Admin-Benutzer erstellen..."

# Prüfe ob Admin bereits existiert
if ! python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.get(username='admin')" 2>/dev/null; then
    # Admin erstellen mit Script
    python manage.py shell << END
from django.contrib.auth.models import User
from planning.models import UserProfile, Role

# Admin-User erstellen
admin = User.objects.create_superuser('admin', 'admin@christusgemeinde.de', 'admin123')
print("✓ Admin-User erstellt")
print("  Username: admin")
print("  Password: admin123")

# Profile für Admin
UserProfile.objects.get_or_create(user=admin)
END
    echo "   ✓ Admin-Benutzer erstellt (admin / admin123)"
else
    echo "   ✓ Admin-Benutzer existiert bereits"
fi
echo ""

# ============================================================================
# 6. DEMO-DATEN
# ============================================================================

echo "🎬 Schritt 6/6: Demo-Daten laden..."

python manage.py shell << END
from planning.models import Event
event_count = Event.objects.count()
print(f"   Vorhandene Events: {event_count}")
END

# Nur laden wenn keine Events existieren
if [ $(python manage.py shell -c "from planning.models import Event; print(Event.objects.count())") -eq 0 ]; then
    python manage.py load_demo_data
    echo "   ✓ Demo-Daten geladen"
else
    echo "   ✓ Demo-Daten existieren bereits"
fi
echo ""

# ============================================================================
# FERTIG!
# ============================================================================

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ✅ SETUP ABGESCHLOSSEN - ALLES IST BEREIT!              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 APP STARTEN:"
echo "   python manage.py runserver"
echo ""
echo "📍 ZUGRIFF:"
echo "   App:        http://localhost:8000"
echo "   Admin:      http://localhost:8000/admin"
echo ""
echo "🔑 STANDARD-ANMELDEDATEN:"
echo "   Admin-User:     admin / admin123"
echo "   Demo-Benutzer:  anna / demo123"
echo "   Demo-Benutzer:  bob / demo123"
echo "   Demo-Benutzer:  clara / demo123"
echo ""
echo "💡 ERSTE SCHRITTE:"
echo "   1. Admin anmelden (admin / admin123)"
echo "   2. Zu 'Termine' gehen"
echo "   3. Demo-Events sehen"
echo "   4. 'Auto-Zuteilung' klicken"
echo "   5. Einsatzplan wird automatisch erstellt! 🎉"
echo ""
echo "📚 DOKUMENTATION:"
echo "   - README.md          (Vollständige Anleitung)"
echo "   - QUICKSTART.md      (Schnelle Übersicht)"
echo "   - PROJEKTSTRUKTUR.md (Technische Details)"
echo ""
