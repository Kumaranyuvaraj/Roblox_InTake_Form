from django.contrib import admin
from roblex_app.models import IntakeForm,Question, Option

@admin.register(IntakeForm)
class IntakeFormAdmin(admin.ModelAdmin):
    # Display these fields in the list view
    list_display = [
        'id',
        'gamer_first_name', 
        'gamer_last_name',
        'guardian_first_name',
        'guardian_last_name',
        'roblox_gamertag',
        'date',
        'created_at'
    ]
    
    # Add filters in the right sidebar
    list_filter = [
        'date',
        'created_at',
        'custody_type',
        'complained_to_roblox',
        'complained_to_apple',
        'contacted_police'
    ]
    
    # Add search functionality
    search_fields = [
        'gamer_first_name',
        'gamer_last_name', 
        'guardian_first_name',
        'guardian_last_name',
        'roblox_gamertag',
        'discord_profile',
        'xbox_gamertag',
        'ps_gamertag'
    ]
    
    # Make the list clickable on these fields
    list_display_links = ['id', 'gamer_first_name', 'gamer_last_name']
    
    # Add date hierarchy navigation
    date_hierarchy = 'created_at'
    
    # Set how many items to show per page
    list_per_page = 25
    
    # Organize the form fields into logical sections
    fieldsets = (
        ('Basic Information', {
            'fields': ('date', 'question')
        }),
        ('Gamer Information', {
            'fields': ('gamer_first_name', 'gamer_last_name')
        }),
        ('Guardian Information', {
            'fields': ('guardian_first_name', 'guardian_last_name', 'custody_type', 'custody_other_detail')
        }),
        ('Gaming Profiles', {
            'fields': ('roblox_gamertag', 'discord_profile', 'xbox_gamertag', 'ps_gamertag'),
            'classes': ('collapse',)  # Make this section collapsible
        }),
        ('Incident Details', {
            'fields': ('description_predators', 'description_medical_psychological', 'description_economic_loss', 'first_contact', 'last_contact')
        }),
        ('Complaints Filed', {
            'fields': (
                'complained_to_roblox', 'emails_to_roblox',
                'complained_to_apple', 'emails_to_apple', 
                'complained_to_cc', 'emails_to_cc', 'cc_names',
                'contacted_police', 'emails_to_police', 'police_details',
                'other_complaints'
            ),
            'classes': ('collapse',)
        }),
        ('Predator Behavior', {
            'fields': (
                'asked_for_photos', 'minor_sent_photos',
                'predator_distributed', 'predator_threatened',
                'in_person_meeting'
            ),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('additional_info', 'discovery_info'),
            'classes': ('collapse',)
        })
    )
    
    # Make some fields read-only
    readonly_fields = ['created_at']
    
    # Add actions
    actions = ['mark_as_reviewed']
    
    def mark_as_reviewed(self, request, queryset):
        # Custom action - you can extend this as needed
        self.message_user(request, f"{queryset.count()} forms marked as reviewed.")
    mark_as_reviewed.short_description = "Mark selected forms as reviewed"

class OptionInline(admin.TabularInline):  # or admin.StackedInline
    model = Option
    extra = 8  # show 8 blank options by default

class QuestionAdmin(admin.ModelAdmin):
    inlines = [OptionInline]

admin.site.register(Question, QuestionAdmin)
admin.site.register(Option)

# admin.site.register(Question)
# admin.site.register(Option)
