from django import forms
from django.contrib.auth.models import User
from .models import Event, Availability, Assignment, UserProfile


class EventForm(forms.ModelForm):
    """Form für Event-Erstellung und -Bearbeitung"""
    
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'location', 'date', 'start_time', 'end_time',
            'status', 'availability_deadline', 'notes', 'is_recurring',
            'recurrence_pattern', 'recurrence_end_date'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'z.B. Gottesdienst Sonntag'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'availability_deadline': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_recurring': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'recurrence_pattern': forms.Select(attrs={'class': 'form-control'}),
            'recurrence_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'title': 'Titel',
            'description': 'Beschreibung',
            'location': 'Ort',
            'date': 'Datum',
            'start_time': 'Startzeit',
            'end_time': 'Endzeit',
            'status': 'Status',
            'availability_deadline': 'Frist für Verfügbarkeitseintragung',
            'notes': 'Hinweise',
            'is_recurring': 'Wiederkehrend',
            'recurrence_pattern': 'Wiederholungsmuster',
            'recurrence_end_date': 'Enddatum für Wiederholung',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and end_time <= start_time:
            raise forms.ValidationError("Endzeit muss nach Startzeit liegen")
        
        return cleaned_data


class AvailabilityForm(forms.ModelForm):
    """Form für Verfügbarkeitseintragung"""
    
    class Meta:
        model = Availability
        fields = ['status', 'notes']
        widgets = {
            'status': forms.RadioSelect(choices=[
                ('yes', '✓ Ja, ich kann'),
                ('maybe', '~ Ich könnte, aber lieber nicht'),
                ('no', '✗ Nein, ich kann nicht'),
            ]),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Optionale Notizen oder Kommentare'
            }),
        }
        labels = {
            'status': 'Meine Verfügbarkeit',
            'notes': 'Notizen (optional)',
        }


class UserProfileForm(forms.ModelForm):
    """Form für Benutzerprofil-Bearbeitung"""
    
    class Meta:
        model = UserProfile
        fields = ['phone', 'notes']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'z.B. 0123456789'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Besonderheiten oder Anmerkungen'
            }),
        }
        labels = {
            'phone': 'Telefonnummer',
            'notes': 'Notizen',
        }


class AutoAssignmentForm(forms.Form):
    """Form für automatische Zuteilung"""
    
    ALGORITHM_CHOICES = [
        ('fair', 'Fair (Berücksichtigung bisheriger Einteilungen)'),
        ('simple', 'Einfach (Nur Verfügbarkeit)'),
    ]
    
    algorithm = forms.ChoiceField(
        choices=ALGORITHM_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Algorithmus'
    )
    
    prefer_yes_only = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Bevorzuge nur "Ja"-Antworten (keine Maybe wenn möglich)'
    )


class AssignmentForm(forms.ModelForm):
    """Form für manuelle Zuteilung"""
    
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Mitarbeiter'
    )
    
    class Meta:
        model = Assignment
        fields = ['user', 'role', 'notes']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Optionale Notizen'
            }),
        }
        labels = {
            'user': 'Mitarbeiter',
            'role': 'Rolle',
            'notes': 'Notizen',
        }


class AvailabilityFilterForm(forms.Form):
    """Form zum Filtern von Verfügbarkeiten"""
    
    STATUS_CHOICES = [('', 'Alle'), ('yes', 'Ja'), ('maybe', 'Vielleicht'), ('no', 'Nein')]
    
    event = forms.ModelChoiceField(
        queryset=Event.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Termin'
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Status'
    )
    
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Mitarbeiter'
    )
