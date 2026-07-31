from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from planning.models import Event, NotificationLog, Assignment
from django.conf import settings
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def send_availability_invitation(user, event):
    """
    Versendet Einladung zur Verfügbarkeitseintragung
    
    Args:
        user (User): Empfänger
        event (Event): Das Event
    """
    if not user.email:
        logger.warning(f"Benutzer {user} hat keine E-Mail-Adresse")
        return False
    
    subject = f"Verfügbarkeit erforderlich: {event.title}"
    
    context = {
        'user': user,
        'event': event,
        'deadline': event.availability_deadline,
        'link': f"{settings.SITE_URL}/my-availabilities/",
    }
    
    # HTML Email
    html_message = render_to_string('planning/emails/availability_invitation.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        # Log erfolgreicher Versand
        NotificationLog.objects.create(
            recipient=user,
            event=event,
            notification_type='availability_invite',
            subject=subject,
            message=plain_message,
            success=True,
        )
        
        logger.info(f"Verfügbarkeitseinladung an {user.email} für Event {event} versendet")
        return True
    
    except Exception as e:
        logger.error(f"Fehler beim E-Mail-Versand an {user.email}: {e}")
        
        NotificationLog.objects.create(
            recipient=user,
            event=event,
            notification_type='availability_invite',
            subject=subject,
            message=plain_message,
            success=False,
            error_message=str(e),
        )
        
        return False


def send_assignment_notification(assignment):
    """
    Versendet Benachrichtigung über Zuteilung
    
    Args:
        assignment (Assignment): Die Zuteilung
    """
    user = assignment.user
    event = assignment.event
    role = assignment.role
    
    if not user.email:
        logger.warning(f"Benutzer {user} hat keine E-Mail-Adresse")
        return False
    
    subject = f"Einsatzplan: {event.title} - {role.get_name_display()}"
    
    context = {
        'user': user,
        'event': event,
        'role': role.get_name_display(),
        'assignment_type': assignment.get_assignment_type_display(),
        'link': f"{settings.SITE_URL}/my-schedule/",
    }
    
    html_message = render_to_string('planning/emails/assignment_notification.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        assignment.email_sent = True
        assignment.save()
        
        NotificationLog.objects.create(
            recipient=user,
            event=event,
            notification_type='assignment',
            subject=subject,
            message=plain_message,
            success=True,
        )
        
        logger.info(f"Zuteilungsbenachrichtigung an {user.email} versendet")
        return True
    
    except Exception as e:
        logger.error(f"Fehler beim E-Mail-Versand an {user.email}: {e}")
        
        NotificationLog.objects.create(
            recipient=user,
            event=event,
            notification_type='assignment',
            subject=subject,
            message=plain_message,
            success=False,
            error_message=str(e),
        )
        
        return False


def send_reminder_notification(event, days_before=1):
    """
    Versendet Erinnerungsmails vor einem Event
    
    Args:
        event (Event): Das Event
        days_before (int): Tage vor dem Event
    """
    # Nur für geplante Events
    if event.status != 'geplant':
        return
    
    # Alle, die eingeplant sind
    assignments = event.assignments.select_related('user').all()
    
    subject = f"Erinnerung: {event.title} findet in {days_before} Tag(en) statt"
    
    sent_count = 0
    for assignment in assignments:
        user = assignment.user
        
        if not user.email:
            continue
        
        context = {
            'user': user,
            'event': event,
            'role': assignment.role.get_name_display(),
            'days_before': days_before,
        }
        
        html_message = render_to_string('planning/emails/reminder_notification.html', context)
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            NotificationLog.objects.create(
                recipient=user,
                event=event,
                notification_type='reminder',
                subject=subject,
                message=plain_message,
                success=True,
            )
            
            sent_count += 1
        
        except Exception as e:
            logger.error(f"Fehler beim Erinnerungsmail an {user.email}: {e}")
            NotificationLog.objects.create(
                recipient=user,
                event=event,
                notification_type='reminder',
                subject=subject,
                message=plain_message,
                success=False,
                error_message=str(e),
            )
    
    logger.info(f"Erinnerungsmails für Event {event} versendet an {sent_count} Personen")


def send_bulk_availability_invitations(events=None):
    """
    Versendet Verfügbarkeitseinladungen für mehrere Events
    
    Args:
        events (QuerySet): Events (Standard: alle offenen Events)
    """
    if events is None:
        events = Event.objects.filter(status='offen')
    
    from planning.models import UserProfile
    active_users = UserProfile.objects.filter(is_active=True)
    
    total_sent = 0
    
    for event in events:
        for profile in active_users:
            if send_availability_invitation(profile.user, event):
                total_sent += 1
    
    logger.info(f"Bulk Verfügbarkeitseinladungen versendet: {total_sent}")
    return total_sent


def send_assignment_notifications_for_event(event):
    """
    Versendet Zuteilungsbenachrichtigungen für alle Zuordnungen eines Events
    
    Args:
        event (Event): Das Event
    """
    assignments = event.assignments.select_related('user').all()
    
    sent_count = 0
    for assignment in assignments:
        if send_assignment_notification(assignment):
            sent_count += 1
    
    logger.info(f"Zuteilungsbenachrichtigungen für Event {event} versendet: {sent_count}")
    return sent_count


def schedule_reminder_mails():
    """
    Versendet automatisch Erinnerungsmails 1 Tag vor Events
    Sollte als periodische Task (Celery/APScheduler) laufen
    """
    tomorrow = datetime.now().date() + timedelta(days=1)
    
    events = Event.objects.filter(
        date=tomorrow,
        status='geplant'
    )
    
    for event in events:
        send_reminder_notification(event, days_before=1)
    
    return len(events)
