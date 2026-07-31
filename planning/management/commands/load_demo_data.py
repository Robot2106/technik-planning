from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from planning.models import Role, UserProfile, Event

class Command(BaseCommand):
    help = 'Lädt Demo-Daten zum Testen'

    def handle(self, *args, **options):
        self.stdout.write("📥 Lade Demo-Daten...")
        
        # Erstelle Rollen
        ton_role, _ = Role.objects.get_or_create(
            name='ton',
            defaults={'description': 'Verantwortlich für Audio/Sound'}
        )
        streaming_role, _ = Role.objects.get_or_create(
            name='streaming',
            defaults={'description': 'Verantwortlich für Livestream'}
        )
        self.stdout.write("✓ Rollen erstellt")
        
        # Erstelle Demo-Benutzer
        users_data = [
            {'username': 'anna', 'first_name': 'Anna', 'last_name': 'Müller', 'roles': [ton_role]},
            {'username': 'bob', 'first_name': 'Bob', 'last_name': 'Schmidt', 'roles': [streaming_role]},
            {'username': 'clara', 'first_name': 'Clara', 'last_name': 'Weber', 'roles': [ton_role, streaming_role]},
            {'username': 'david', 'first_name': 'David', 'last_name': 'Fischer', 'roles': [ton_role]},
            {'username': 'eva', 'first_name': 'Eva', 'last_name': 'Meyer', 'roles': [streaming_role]},
        ]
        
        for user_data in users_data:
            username = user_data['username']
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'email': f'{username}@example.com',
                }
            )
            
            if created:
                user.set_password('demo123')
                user.save()
            
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.roles.set(user_data['roles'])
            profile.phone = '+49 123 456789'
            profile.save()
        
        self.stdout.write("✓ Demo-Benutzer erstellt")
        
        # Erstelle Demo-Events
        today = timezone.now().date()
        
        events_data = [
            {
                'title': 'Gottesdienst Sonntag',
                'location': 'Kirche',
                'description': 'Wöchentlicher Gottesdienst mit Musik und Predigt',
                'date': today + timedelta(days=7),
                'start_time': '10:00',
                'end_time': '11:30',
                'status': 'offen',
                'availability_deadline': timezone.now() + timedelta(days=3),
            },
            {
                'title': 'Jungschar-Gottesdienst',
                'location': 'Gemeindesaal',
                'description': 'Familien-orientierter Gottesdienst',
                'date': today + timedelta(days=14),
                'start_time': '09:00',
                'end_time': '10:00',
                'status': 'offen',
                'availability_deadline': timezone.now() + timedelta(days=5),
            },
            {
                'title': 'Gemeindefeier',
                'location': 'Kirche + Gemeindesaal',
                'description': 'Jährliche Gemeindefeier mit Musik und Andacht',
                'date': today + timedelta(days=21),
                'start_time': '19:00',
                'end_time': '21:00',
                'status': 'offen',
                'availability_deadline': timezone.now() + timedelta(days=10),
            },
        ]
        
        for event_data in events_data:
            event, created = Event.objects.get_or_create(
                title=event_data['title'],
                date=event_data['date'],
                start_time=event_data['start_time'],
                defaults={
                    'location': event_data['location'],
                    'description': event_data['description'],
                    'end_time': event_data['end_time'],
                    'status': event_data['status'],
                    'availability_deadline': event_data['availability_deadline'],
                }
            )
        
        self.stdout.write("✓ Demo-Events erstellt")
        
        # Demo-Meldungen hinzufügen
        from planning.models import Availability
        
        anna = User.objects.get(username='anna')
        bob = User.objects.get(username='bob')
        clara = User.objects.get(username='clara')
        
        events = Event.objects.all()
        for event in events:
            # Anna: Ja
            Availability.objects.get_or_create(
                user=anna,
                event=event,
                defaults={'status': 'yes'}
            )
            # Bob: Nein
            Availability.objects.get_or_create(
                user=bob,
                event=event,
                defaults={'status': 'no'}
            )
            # Clara: Vielleicht
            Availability.objects.get_or_create(
                user=clara,
                event=event,
                defaults={'status': 'maybe'}
            )
        
        self.stdout.write("✓ Demo-Verfügbarkeiten erstellt")
        
        self.stdout.write(self.style.SUCCESS("\n✅ Demo-Daten erfolgreich geladen!"))
        self.stdout.write("\n📝 Anmeldedaten für Tests:")
        self.stdout.write("   Admin: admin / admin")
        self.stdout.write("   User: anna / demo123")
        self.stdout.write("   User: bob / demo123")
        self.stdout.write("   User: clara / demo123")
        self.stdout.write("\n💡 Nächste Schritte:")
        self.stdout.write("   1. Admin-Seite öffnen")
        self.stdout.write("   2. Mit Admin anmelden")
        self.stdout.write("   3. Auto-Zuteilung für Events testen")
