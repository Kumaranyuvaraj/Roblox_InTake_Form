from django.contrib import admin
from roblex_app.models import IntakeForm,Question, Option,EmailLog,UserDetail,UserAnswer,EmailTemplate

from django.utils.html import format_html

@admin.register(IntakeForm)
class IntakeFormAdmin(admin.ModelAdmin):

    def pdf_link(self, obj):
        if obj.pdf_file:
            return format_html('<a href="{}" target="_blank">View PDF</a>', obj.pdf_file.url)
        return "No PDF"
    pdf_link.short_description = "PDF"

    list_display = [
        'id',
        'gamer_first_name', 
        'gamer_last_name',
        'guardian_first_name',
        'guardian_last_name',
        'roblox_gamertag',
        'pdf_link',
        'date',
        'created_at'
    ]

    list_display_links = ['id', 'gamer_first_name', 'gamer_last_name']
    list_filter = ['date', 'created_at', 'custody_type', 'complained_to_roblox', 'complained_to_apple', 'contacted_police']
    search_fields = ['gamer_first_name', 'gamer_last_name', 'guardian_first_name', 'guardian_last_name', 'roblox_gamertag', 'discord_profile', 'xbox_gamertag', 'ps_gamertag']
    date_hierarchy = 'created_at'
    list_per_page = 25
    readonly_fields = ['created_at']

    fieldsets = (
        ('Basic Information', {'fields': ('date', 'question')}),
        ('Gamer Information', {'fields': ('gamer_first_name', 'gamer_last_name')}),
        ('Guardian Information', {'fields': ('guardian_first_name', 'guardian_last_name', 'custody_type', 'custody_other_detail')}),
        ('Gaming Profiles', {'fields': ('roblox_gamertag', 'discord_profile', 'xbox_gamertag', 'ps_gamertag'), 'classes': ('collapse',)}),
        ('Incident Details', {'fields': ('description_predators', 'description_medical_psychological', 'description_economic_loss', 'first_contact', 'last_contact')}),
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

    actions = ['mark_as_reviewed']

    def mark_as_reviewed(self, request, queryset):
        self.message_user(request, f"{queryset.count()} forms marked as reviewed.")
    mark_as_reviewed.short_description = "Mark selected forms as reviewed"

admin.site.site_header = "Roblox Admin"
admin.site.site_title = "Roblox"
admin.site.index_title = "Welcome to Your Roblox Admin Portal"



class OptionInline(admin.TabularInline):  # or admin.StackedInline
    model = Option
    extra = 8  # show 8 blank options by default

class QuestionAdmin(admin.ModelAdmin):
    inlines = [OptionInline]

class UserAnswerInline(admin.TabularInline):
    model = UserAnswer
    extra = 0
    can_delete = False
    show_change_link = False
    readonly_fields = ('question', 'get_selected_option')
    fields = ('question', 'get_selected_option')

    def get_selected_option(self, obj):
        return obj.selected_option.text if obj.selected_option else "-"
    get_selected_option.short_description = "Selected Option"


@admin.register(UserDetail)
class UserDetailAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email', 'zipcode', 'submitted_answers_count')
    search_fields = ('first_name', 'last_name', 'email', 'zipcode')
    inlines = [UserAnswerInline]
    list_per_page = 25

    def submitted_answers_count(self, obj):
        return UserAnswer.objects.filter(user=obj).count()
    submitted_answers_count.short_description = "Total Answers"

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject')


admin.site.register(Question, QuestionAdmin)
admin.site.register(Option)
admin.site.register(EmailLog)
# admin.site.register(UserDetail)
admin.site.register(UserAnswer)

# admin.site.register(Question)
# admin.site.register(Option)
