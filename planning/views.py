from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count
from datetime import timedelta, datetime
import csv
import logging

from .models import Event, Availability, Assignment, UserProfile, Role, NotificationLog
from .forms import AvailabilityForm, EventForm, UserProfileForm, AutoAssignmentForm
from .utils.scheduler import auto_assign_event, generate_assignments
from .utils.email_service import send_availability_invitation, send_assignment_notification

logger = logging.getLogger(__name__)


def is_admin(user):
    """Prüft, ob Nutzer Admin ist"""
    return user.is_staff


def is_active_member(user):
    """Prüft, ob Nutzer ein aktives Mitglied ist"""
    return hasattr(user, 'profile') and user.profile.is_active


# ============================================================================
# AUTH VIEWS
# ============================================================================

def login_view(request):
    """Anmeldungsseite"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"Willkommen, {user.get_full_name() or user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Benutzername oder Passwort ist falsch")
    
    return render(request, 'planning/login.html')


def logout_view(request):
    """Abmeldung"""
    logout(request)
    messages.success(request, "Sie wurden abgemeldet")
    return redirect('login')


# ============================================================================
# MITARBEITER VIEWS
# ============================================================================

@login_required(login_url='login')
def dashboard(request):
    """Haupt-Dashboard für Mitarbeiter"""
    profile = get_object_or_404(UserProfile, user=request.user)
    
    # Kommende Events
    upcoming_events = Event.objects.filter(
        date__gte=timezone.now().date(),
        status__in=['offen', 'geplant']
    ).order_by('date', 'start_time')[:5]
    
    # Persönliche Zuteilungen
    my_assignments = Assignment.objects.filter(
        user=request.user,
        event__date__gte=timezone.now().date()
    ).select_related('event', 'role').order_by('event__date')[:5]
    
    # Offene Verfügbarkeitseintragungen
    open_availabilities = Event.objects.filter(
        date__gte=timezone.now().date(),
        status='offen',
        availability_deadline__gt=timezone.now()
    ).exclude(
        availabilities__user=request.user
    ).count()
    
    context = {
        'upcoming_events': upcoming_events,
        'my_assignments': my_assignments,
        'open_availabilities': open_availabilities,
        'profile': profile,
    }
    return render(request, 'planning/dashboard.html', context)


@login_required(login_url='login')
def my_profile(request):
    """Profilseite des Mitarbeiters"""
    profile = get_object_or_404(UserProfile, user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil aktualisiert")
            return redirect('my_profile')
    else:
        form = UserProfileForm(instance=profile)
    
    context = {
        'form': form,
        'profile': profile,
    }
    return render(request, 'planning/my_profile.html', context)


@login_required(login_url='login')
def my_availabilities(request):
    """Verfügbarkeitseintragung für Mitarbeiter"""
    profile = get_object_or_404(UserProfile, user=request.user)
    
    # Nur freigegebene Events
    open_events = Event.objects.filter(
        status='offen',
        availability_deadline__gt=timezone.now()
    ).order_by('date', 'start_time')
    
    availabilities = {}
    for event in open_events:
        try:
            avail = Availability.objects.get(user=request.user, event=event)
            availabilities[event.id] = avail.status
        except Availability.DoesNotExist:
            availabilities[event.id] = None
    
    if request.method == 'POST':
        event_id = request.POST.get('event_id')
        status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        event = get_object_or_404(Event, id=event_id, status='offen')
        
        if not event.is_availability_open():
            messages.error(request, "Frist für diese Eintragung ist abgelaufen")
            return redirect('my_availabilities')
        
        availability, created = Availability.objects.update_or_create(
            user=request.user,
            event=event,
            defaults={'status': status, 'notes': notes}
        )
        
        msg = "erstellt" if created else "aktualisiert"
        messages.success(request, f"Verfügbarkeit {msg}")
        return redirect('my_availabilities')
    
    context = {
        'open_events': open_events,
        'availabilities': availabilities,
        'profile': profile,
    }
    return render(request, 'planning/my_availabilities.html', context)


@login_required(login_url='login')
def my_schedule(request):
    """Persönlicher Einsatzplan"""
    profile = get_object_or_404(UserProfile, user=request.user)
    
    assignments = Assignment.objects.filter(
        user=request.user
    ).select_related('event', 'role').order_by('event__date', 'event__start_time')
    
    # Filter nach Monat
    month_filter = request.GET.get('month')
    if month_filter:
        try:
            year, month = map(int, month_filter.split('-'))
            assignments = assignments.filter(event__date__year=year, event__date__month=month)
        except (ValueError, TypeError):
            pass
    
    context = {
        'assignments': assignments,
        'profile': profile,
    }
    return render(request, 'planning/my_schedule.html', context)


# ============================================================================
# ADMIN VIEWS
# ============================================================================

@login_required(login_url='login')
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin-Dashboard"""
    upcoming_events = Event.objects.filter(
        date__gte=timezone.now().date()
    ).order_by('date', 'start_time')[:10]
    
    unassigned_events = Event.objects.filter(
        status__in=['offen', 'geplant']
    ).annotate(
        assignment_count=Count('assignments')
    ).filter(assignment_count__lt=2)
    
    total_users = UserProfile.objects.filter(is_active=True).count()
    total_events = Event.objects.count()
    
    context = {
        'upcoming_events': upcoming_events,
        'unassigned_events': unassigned_events,
        'total_users': total_users,
        'total_events': total_events,
    }
    return render(request, 'planning/admin/dashboard.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def event_list(request):
    """Liste aller Termine (Admin)"""
    events = Event.objects.all().order_by('-date')
    
    # Filter
    status = request.GET.get('status')
    if status:
        events = events.filter(status=status)
    
    context = {'events': events}
    return render(request, 'planning/admin/event_list.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def event_create(request):
    """Neuen Termin erstellen"""
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save()
            messages.success(request, f"Termin '{event.title}' erstellt")
            return redirect('event_detail', pk=event.pk)
    else:
        form = EventForm()
    
    context = {'form': form, 'title': 'Neuen Termin erstellen'}
    return render(request, 'planning/admin/event_form.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def event_detail(request, pk):
    """Termin-Details (Admin)"""
    event = get_object_or_404(Event, pk=pk)
    availabilities = Availability.objects.filter(event=event)
    assignments = Assignment.objects.filter(event=event).select_related('user', 'role')
    
    context = {
        'event': event,
        'availabilities': availabilities,
        'assignments': assignments,
    }
    return render(request, 'planning/admin/event_detail.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def event_update(request, pk):
    """Termin bearbeiten"""
    event = get_object_or_404(Event, pk=pk)
    
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, "Termin aktualisiert")
            return redirect('event_detail', pk=event.pk)
    else:
        form = EventForm(instance=event)
    
    context = {'form': form, 'event': event, 'title': 'Termin bearbeiten'}
    return render(request, 'planning/admin/event_form.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def event_delete(request, pk):
    """Termin löschen"""
    event = get_object_or_404(Event, pk=pk)
    
    if request.method == 'POST':
        title = event.title
        event.delete()
        messages.success(request, f"Termin '{title}' gelöscht")
        return redirect('event_list')
    
    context = {'event': event}
    return render(request, 'planning/admin/event_confirm_delete.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def release_event_for_signup(request, pk):
    """Event zur Verfügbarkeitseintragung freigeben"""
    event = get_object_or_404(Event, pk=pk)
    
    if event.status != 'offen':
        event.status = 'offen'
        event.save()
        
        # E-Mails versenden
        active_users = UserProfile.objects.filter(is_active=True)
        for profile in active_users:
            try:
                send_availability_invitation(profile.user, event)
            except Exception as e:
                logger.error(f"E-Mail an {profile.user} konnte nicht versendet werden: {e}")
        
        messages.success(request, f"Event freigegeben. E-Mails versendet.")
    
    return redirect('event_detail', pk=event.pk)


@login_required(login_url='login')
@user_passes_test(is_admin)
def auto_assign(request, pk):
    """Automatische Zuteilung starten"""
    event = get_object_or_404(Event, pk=pk)
    
    # Löschen von bestehenden Auto-Zuteilungen
    existing_auto = Assignment.objects.filter(event=event, assignment_type='auto')
    existing_auto.delete()
    
    # Auto-Zuteilung
    success, warnings = auto_assign_event(event)
    
    if success:
        messages.success(request, "Automatische Zuteilung abgeschlossen")
        if warnings:
            for warning in warnings:
                messages.warning(request, warning)
    else:
        messages.error(request, "Automatische Zuteilung konnte nicht durchgeführt werden")
    
    return redirect('event_detail', pk=event.pk)


@login_required(login_url='login')
@user_passes_test(is_admin)
def event_export_csv(request):
    """Export aller Termine als CSV"""
    events = Event.objects.all().order_by('date')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="termine.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Titel', 'Datum', 'Startzeit', 'Endzeit', 'Ort', 'Status'])
    
    for event in events:
        writer.writerow([
            event.title,
            event.date,
            event.start_time,
            event.end_time,
            event.location,
            event.get_status_display(),
        ])
    
    return response


@login_required(login_url='login')
@user_passes_test(is_admin)
def user_management(request):
    """Benutzerverwaltung (Admin)"""
    users = UserProfile.objects.all()
    
    context = {'users': users}
    return render(request, 'planning/admin/user_management.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def statistics(request):
    """Statistiken zur fairen Verteilung"""
    all_users = UserProfile.objects.filter(is_active=True)
    
    stats = []
    for profile in all_users:
        ton_count = profile.get_assignments_count(role=None)
        streaming_count = Assignment.objects.filter(
            user=profile.user,
            role__name='streaming',
            event__status='geplant'
        ).count()
        
        stats.append({
            'user': profile,
            'total': ton_count + streaming_count,
            'ton': ton_count,
            'streaming': streaming_count,
        })
    
    stats.sort(key=lambda x: x['total'])
    
    context = {'stats': stats}
    return render(request, 'planning/admin/statistics.html', context)
