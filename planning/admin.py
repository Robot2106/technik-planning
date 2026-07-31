from django.contrib import admin
from django.utils.html import format_html
from .models import Role, UserProfile, Event, Availability, Assignment, NotificationLog


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['get_name', 'get_username', 'is_active', 'get_roles', 'created_at']
    list_filter = ['is_active', 'roles', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__username']
    filter_horizontal = ['roles']
    fieldsets = (
        ('Benutzer', {'fields': ('user',)}),
        ('Verfügbarkeitsstatus', {'fields': ('is_active',)}),
        ('Rollen', {'fields': ('roles',)}),
        ('Kontaktinformation', {'fields': ('phone',)}),
        ('Notizen', {'fields': ('notes',)}),
    )
    
    def get_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_name.short_description = 'Name'
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Benutzername'
    
    def get_roles(self, obj):
        return ', '.join([r.get_name_display() for r in obj.roles.all()])
    get_roles.short_description = 'Rollen'


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'start_time', 'status', 'availability_deadline', 'get_assignment_status']
    list_filter = ['status', 'date', 'is_recurring']
    search_fields = ['title', 'location', 'description']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Grundinformation', {
            'fields': ('title', 'description', 'location', 'status')
        }),
        ('Zeitinformation', {
            'fields': ('date', 'start_time', 'end_time', 'availability_deadline')
        }),
        ('Wiederholung', {
            'fields': ('is_recurring', 'recurrence_pattern', 'recurrence_end_date', 'parent_event'),
            'classes': ('collapse',)
        }),
        ('Notizen', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_assignment_status(self, obj):
        assignments = obj.assignments.count()
        if assignments == 2:
            return format_html('<span style="color: green;">✓ Vollständig</span>')
        elif assignments == 1:
            return format_html('<span style="color: orange;">⚠ Unvollständig</span>')
        else:
            return format_html('<span style="color: red;">✗ Nicht besetzt</span>')
    get_assignment_status.short_description = 'Zuteilungsstatus'


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'get_status_colored', 'created_at']
    list_filter = ['status', 'event__date', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'event__title']
    date_hierarchy = 'event__date'
    readonly_fields = ['created_at', 'updated_at']
    
    def get_status_colored(self, obj):
        colors = {
            'yes': 'green',
            'maybe': 'orange',
            'no': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    get_status_colored.short_description = 'Status'


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'event', 'assignment_type', 'email_sent', 'created_at']
    list_filter = ['assignment_type', 'role', 'event__date', 'email_sent', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'event__title']
    date_hierarchy = 'event__date'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Zuteilung', {
            'fields': ('event', 'user', 'role', 'assignment_type')
        }),
        ('Benachrichtigung', {
            'fields': ('email_sent', 'notes'),
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'notification_type', 'get_success_status', 'sent_at']
    list_filter = ['notification_type', 'success', 'sent_at']
    search_fields = ['recipient__first_name', 'recipient__last_name', 'recipient__email']
    date_hierarchy = 'sent_at'
    readonly_fields = ['sent_at', 'recipient', 'event', 'notification_type', 'subject', 'message', 'error_message']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def get_success_status(self, obj):
        if obj.success:
            return format_html('<span style="color: green;">✓ Erfolgreich</span>')
        else:
            return format_html('<span style="color: red;">✗ Fehler</span>')
    get_success_status.short_description = 'Status'
