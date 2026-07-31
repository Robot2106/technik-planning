from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class Role(models.Model):
    """Rollen für Technikdienste"""
    ROLE_CHOICES = [
        ('ton', 'Tontechniker'),
        ('streaming', 'Streaming-Beauftragter'),
    ]
    
    name = models.CharField(max_length=50, unique=True, choices=ROLE_CHOICES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Rolle"
        verbose_name_plural = "Rollen"
        ordering = ['name']
    
    def __str__(self):
        return self.get_name_display()


class UserProfile(models.Model):
    """Benutzer-Profil mit Rollenzuordnung"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    roles = models.ManyToManyField(Role, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Benutzerprofil"
        verbose_name_plural = "Benutzerprofile"
        ordering = ['user__first_name', 'user__last_name']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"
    
    def has_role(self, role_name):
        """Prüft, ob der Nutzer eine bestimmte Rolle hat"""
        return self.roles.filter(name=role_name).exists()
    
    def get_assignments_count(self, role=None):
        """Zählt die Zuteilungen des Nutzers (für faire Verteilung)"""
        query = Assignment.objects.filter(
            user=self.user,
            event__status='geplant'
        )
        if role:
            query = query.filter(role=role)
        return query.count()


class Event(models.Model):
    """Termine/Events für Technikdienste"""
    STATUS_CHOICES = [
        ('entwurf', 'Entwurf'),
        ('offen', 'Zur Eintragung freigegeben'),
        ('geplant', 'Geplant'),
        ('abgeschlossen', 'Abgeschlossen'),
        ('abgesagt', 'Abgesagt'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='entwurf')
    availability_deadline = models.DateTimeField(help_text="Frist für Verfügbarkeitseintragung")
    notes = models.TextField(blank=True)
    
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(
        max_length=50, blank=True,
        help_text="z.B. 'weekly', 'monthly' oder leer für einmalig"
    )
    recurrence_end_date = models.DateField(null=True, blank=True)
    parent_event = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.CASCADE,
        related_name='recurring_events'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Termin"
        verbose_name_plural = "Termine"
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"{self.title} ({self.date} {self.start_time})"
    
    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("Endzeit muss nach Startzeit liegen")
        if self.availability_deadline > timezone.now() + timedelta(days=365):
            raise ValidationError("Frist sollte nicht mehr als ein Jahr in der Zukunft liegen")
    
    def is_availability_open(self):
        """Prüft, ob Verfügbarkeitseintragung noch offen ist"""
        return timezone.now() < self.availability_deadline and self.status == 'offen'
    
    def is_fully_assigned(self):
        """Prüft, ob alle Rollen besetzt sind"""
        ton_assigned = self.assignments.filter(role__name='ton').exists()
        streaming_assigned = self.assignments.filter(role__name='streaming').exists()
        return ton_assigned and streaming_assigned
    
    def get_available_users_for_role(self, role_name):
        """Gibt Nutzer zurück, die für eine Rolle verfügbar sind"""
        users_with_role = UserProfile.objects.filter(
            is_active=True,
            roles__name=role_name
        ).values_list('user_id', flat=True)
        
        # Nutzer, die verfügbar sind (YES oder MAYBE)
        available = Availability.objects.filter(
            event=self,
            user_id__in=users_with_role,
            status__in=['yes', 'maybe']
        ).values_list('user_id', flat=True)
        
        return User.objects.filter(id__in=available)


class Availability(models.Model):
    """Verfügbarkeitseintragung eines Nutzers für einen Termin"""
    STATUS_CHOICES = [
        ('yes', 'Ja, ich kann'),
        ('maybe', 'Ich könnte, aber lieber nicht'),
        ('no', 'Nein, ich kann nicht'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='availabilities')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='availabilities')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Verfügbarkeit"
        verbose_name_plural = "Verfügbarkeiten"
        unique_together = ('user', 'event')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user} - {self.event} ({self.get_status_display()})"


class Assignment(models.Model):
    """Zuteilung eines Nutzers zu einer Rolle für einen Termin"""
    ASSIGNMENT_TYPE = [
        ('auto', 'Automatisch'),
        ('manual', 'Manuell'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='assignments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments')
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    assignment_type = models.CharField(max_length=10, choices=ASSIGNMENT_TYPE, default='auto')
    notes = models.TextField(blank=True)
    email_sent = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Zuteilung"
        verbose_name_plural = "Zuteilungen"
        unique_together = ('event', 'role')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user} ({self.role}) - {self.event}"
    
    def clean(self):
        # Prüfe, dass User diese Rolle hat
        if not self.user.profile.has_role(self.role.name):
            raise ValidationError(f"Benutzer hat die Rolle '{self.role}' nicht")
        
        # Prüfe, ob User zur gleichen Zeit nicht doppelt eingeplant ist
        conflicting = Assignment.objects.filter(
            user=self.user,
            event__date=self.event.date,
            event__start_time__lt=self.event.end_time,
            event__end_time__gt=self.event.start_time
        ).exclude(event=self.event)
        
        if conflicting.exists():
            raise ValidationError("Benutzer ist zu dieser Zeit bereits eingeplant")


class NotificationLog(models.Model):
    """Log für versendete Benachrichtigungen"""
    NOTIFICATION_TYPE = [
        ('availability_invite', 'Einladung zur Verfügbarkeitseintragung'),
        ('assignment', 'Zuteilungsbenachrichtigung'),
        ('reminder', 'Erinnerung'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True)
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Benachrichtigungslog"
        verbose_name_plural = "Benachrichtigungslogs"
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.recipient} - {self.get_notification_type_display()}"
