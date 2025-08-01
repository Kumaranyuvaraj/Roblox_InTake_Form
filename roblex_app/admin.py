from django.contrib import admin
from roblex_app.models import IntakeForm,Question, Option,EmailLog,UserDetail,UserAnswer,EmailTemplate,DocumentTemplate,DocumentSubmission,DocumentWebhookEvent

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


# ====================
# DocuSeal Document Signing Admin
# ====================

@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'docuseal_template_id', 
        'description',
        'is_active',
        'created_at'
    ]
    list_filter = ['name', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'docuseal_template_id']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'docuseal_template_id', 'description')
        }),
        ('Configuration', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )


@admin.register(DocumentSubmission)
class DocumentSubmissionAdmin(admin.ModelAdmin):
    
    def user_name(self, obj):
        return f"{obj.user_detail.first_name} {obj.user_detail.last_name}"
    user_name.short_description = "User Name"
    
    def user_email(self, obj):
        return obj.user_detail.email
    user_email.short_description = "Email"
    
    def signing_link(self, obj):
        if obj.signed_document_url:
            return format_html('<a href="https://sign.nextkeystack.com/s/{}" target="_blank">Open Signing Link</a>', obj.docuseal_slug)
        return "No URL"
    signing_link.short_description = "Signing Link"
    
    def signed_document_link(self, obj):
        if obj.signed_document_url:
            return format_html('<a href="{}" target="_blank">View Signed Document</a>', obj.signed_document_url)
        return "Not signed"
    signed_document_link.short_description = "Signed Document"
    
    def status_colored(self, obj):
        colors = {
            'created': '#ffc107',  # warning yellow
            'sent': '#17a2b8',     # info blue
            'viewed': '#6f42c1',   # purple
            'completed': '#28a745', # success green
            'declined': '#dc3545',  # danger red
            'expired': '#6c757d'    # secondary gray
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_colored.short_description = "Status"

    list_display = [
        'id',
        'user_name',
        'user_email',
        'document_template',
        'status_colored',
        'signing_link',
        'signed_document_link',
        'created_at',
        'completed_at'
    ]
    
    list_display_links = ['id', 'user_name']
    list_filter = ['status', 'document_template', 'created_at', 'completed_at']
    search_fields = [
        'user_detail__first_name', 
        'user_detail__last_name', 
        'user_detail__email',
        'docuseal_submission_id',
        'external_id'
    ]
    date_hierarchy = 'created_at'
    readonly_fields = ['docuseal_submission_id', 'docuseal_submitter_id', 'docuseal_slug', 'external_id', 'created_at', 'updated_at']
    list_per_page = 25
    
    fieldsets = (
        ('Submission Information', {
            'fields': ('user_detail', 'document_template', 'intake_form')
        }),
        ('Status & URLs', {
            'fields': ('status', 'signed_document_url', 'audit_log_url', 'decline_reason')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at', 'sent_at', 'opened_at', 'declined_at')
        }),
        ('DocuSeal Data', {
            'fields': ('docuseal_submission_id', 'docuseal_submitter_id', 'docuseal_slug', 'external_id'),
            'classes': ('collapse',)
        })
    )
    
    # Bulk actions
    actions = ['mark_as_completed', 'mark_as_expired']
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} submissions marked as completed.')
    mark_as_completed.short_description = "Mark selected submissions as completed"
    
    def mark_as_expired(self, request, queryset):
        updated = queryset.update(status='expired')
        self.message_user(request, f'{updated} submissions marked as expired.')
    mark_as_expired.short_description = "Mark selected submissions as expired"


@admin.register(DocumentWebhookEvent)
class DocumentWebhookEventAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'event_type',
        'document_submission',
        'processed',
        'created_at'
    ]
    list_filter = ['event_type', 'processed', 'created_at']
    search_fields = ['document_submission__docuseal_submission_id', 'event_type']
    readonly_fields = ['created_at', 'webhook_data']
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'document_submission', 'processed')
        }),
        ('Webhook Data', {
            'fields': ('webhook_data',),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        })
    )
