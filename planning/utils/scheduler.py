from django.db.models import Count, Q
from django.contrib.auth.models import User
from planning.models import Event, Availability, Assignment, UserProfile, Role
import logging

logger = logging.getLogger(__name__)


def auto_assign_event(event, prefer_yes_only=True):
    """
    Automatische Zuteilung für einen Termin.
    Versucht, Tontechniker und Streaming-Beauftragten fair zu verteilen.
    
    Args:
        event (Event): Das Event, das eingeplant werden soll
        prefer_yes_only (bool): Nur "Ja"-Antworten verwenden wenn möglich
    
    Returns:
        tuple: (success: bool, warnings: list)
    """
    success = True
    warnings = []
    
    # Rollen definieren
    ton_role = Role.objects.get(name='ton')
    streaming_role = Role.objects.get(name='streaming')
    
    # Existierende Auto-Assignments löschen
    Assignment.objects.filter(event=event, assignment_type='auto').delete()
    
    try:
        # Ton-Techniker zuteilen
        ton_user = _find_best_user_for_role(event, ton_role, prefer_yes_only)
        if ton_user:
            Assignment.objects.create(
                event=event,
                user=ton_user,
                role=ton_role,
                assignment_type='auto'
            )
            logger.info(f"Tontechniker {ton_user} zu Event {event} zugeordnet")
        else:
            warnings.append("Kein verfügbarer Tontechniker gefunden")
            success = False
        
        # Streaming-Beauftragter zuteilen
        streaming_user = _find_best_user_for_role(event, streaming_role, prefer_yes_only, exclude_user=ton_user)
        if streaming_user:
            Assignment.objects.create(
                event=event,
                user=streaming_user,
                role=streaming_role,
                assignment_type='auto'
            )
            logger.info(f"Streaming-Beauftragter {streaming_user} zu Event {event} zugeordnet")
        else:
            warnings.append("Kein verfügbarer Streaming-Beauftragter gefunden")
            success = False
    
    except Exception as e:
        logger.error(f"Fehler bei Auto-Zuteilung für Event {event}: {e}")
        success = False
        warnings.append(f"Fehler bei Zuteilung: {str(e)}")
    
    return success, warnings


def _find_best_user_for_role(event, role, prefer_yes_only=True, exclude_user=None):
    """
    Findet den besten Nutzer für eine Rolle bei einem Event.
    
    Priorität:
    1. "Ja"-Antworten (bevorzugt)
    2. "Vielleicht"-Antworten (nur wenn nötig)
    3. Personen mit weniger bisherigen Einteilungen (faire Verteilung)
    
    Args:
        event (Event): Das Event
        role (Role): Die gesuchte Rolle
        prefer_yes_only (bool): Nur "Ja" wenn möglich
        exclude_user (User): Nutzer ausschließen (z.B. wenn bereits Ton zugeordnet)
    
    Returns:
        User or None: Der beste Nutzer oder None
    """
    
    # Nutzer mit dieser Rolle
    users_with_role = UserProfile.objects.filter(
        is_active=True,
        roles=role
    ).values_list('user_id', flat=True)
    
    if exclude_user:
        users_with_role = list(users_with_role)
        users_with_role = [uid for uid in users_with_role if uid != exclude_user.id]
    
    if not users_with_role:
        return None
    
    # Verfügbarkeitsstatistiken
    availability_data = {}
    for user_id in users_with_role:
        try:
            availability = Availability.objects.get(user_id=user_id, event=event)
            availability_data[user_id] = availability.status
        except Availability.DoesNotExist:
            availability_data[user_id] = 'no'  # Keine Antwort = Nein
    
    # Filtere Kandidaten: Nur YES und MAYBE
    yes_candidates = [uid for uid, status in availability_data.items() if status == 'yes']
    maybe_candidates = [uid for uid, status in availability_data.items() if status == 'maybe']
    
    # Wähle beste Kandidaten
    candidates = yes_candidates if yes_candidates else maybe_candidates
    
    if not candidates:
        return None
    
    # Unter Kandidaten: Wähle denjenigen mit wenigsten bisherigen Einteilungen (faire Verteilung)
    best_user_id = None
    min_assignments = float('inf')
    
    for user_id in candidates:
        assignment_count = Assignment.objects.filter(
            user_id=user_id,
            role=role,
            event__status='geplant'
        ).count()
        
        if assignment_count < min_assignments:
            min_assignments = assignment_count
            best_user_id = user_id
    
    return User.objects.get(id=best_user_id) if best_user_id else None


def generate_monthly_schedule(year, month):
    """
    Generiert einen monatlichen Übersichtsplan.
    Nützlich für CSV/PDF-Export.
    
    Args:
        year (int): Jahr
        month (int): Monat (1-12)
    
    Returns:
        dict: Tage mit ihren Events und Zuteilungen
    """
    from datetime import datetime, timedelta
    
    schedule = {}
    
    # Alle Events dieses Monats
    events = Event.objects.filter(
        date__year=year,
        date__month=month
    ).order_by('date', 'start_time')
    
    for event in events:
        day = event.date.day
        
        if day not in schedule:
            schedule[day] = []
        
        assignments = event.assignments.select_related('user', 'role').all()
        schedule[day].append({
            'event': event,
            'assignments': assignments,
        })
    
    return schedule


def validate_schedule(event):
    """
    Validiert einen erstellten Plan auf Konflikte und Lücken.
    
    Args:
        event (Event): Das zu validierende Event
    
    Returns:
        dict: {valid: bool, errors: list, warnings: list}
    """
    result = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    assignments = event.assignments.all()
    
    # Check 1: Alle Rollen besetzt?
    required_roles = ['ton', 'streaming']
    assigned_roles = set(a.role.name for a in assignments)
    
    for role in required_roles:
        if role not in assigned_roles:
            result['valid'] = False
            result['errors'].append(f"Rolle '{role}' nicht besetzt")
    
    # Check 2: Doppelbelegung?
    for assignment in assignments:
        conflicting = Assignment.objects.filter(
            user=assignment.user,
            event__date=event.date,
            event__start_time__lt=event.end_time,
            event__end_time__gt=event.start_time
        ).exclude(event=event)
        
        if conflicting.exists():
            result['errors'].append(
                f"{assignment.user} hat Zeitkonflikt mit anderem Event"
            )
            result['valid'] = False
    
    # Check 3: Hat jeder eine Verfügbarkeitseintragung?
    for assignment in assignments:
        try:
            avail = Availability.objects.get(user=assignment.user, event=event)
            if avail.status == 'no':
                result['warnings'].append(
                    f"{assignment.user} hat 'Nein' gesagt, ist aber eingeplant"
                )
        except Availability.DoesNotExist:
            pass
    
    return result


def get_assignment_statistics():
    """
    Liefert Statistiken zur Fairness der Verteilung.
    
    Returns:
        dict: Statistiken pro Nutzer
    """
    stats = {}
    
    users = UserProfile.objects.filter(is_active=True)
    
    for profile in users:
        user_id = profile.user_id
        
        # Zuteilungen pro Rolle
        ton_assignments = Assignment.objects.filter(
            user_id=user_id,
            role__name='ton',
            event__status='geplant'
        ).count()
        
        streaming_assignments = Assignment.objects.filter(
            user_id=user_id,
            role__name='streaming',
            event__status='geplant'
        ).count()
        
        stats[user_id] = {
            'user': profile.user,
            'ton': ton_assignments,
            'streaming': streaming_assignments,
            'total': ton_assignments + streaming_assignments,
        }
    
    return stats
