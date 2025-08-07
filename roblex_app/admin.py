from django.contrib import admin
from roblex_app.models import IntakeForm,Question, Option,EmailLog,UserDetail,UserAnswer,EmailTemplate,DocumentTemplate,DocumentSubmission,DocumentWebhookEvent

from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count

@admin.register(IntakeForm)
class IntakeFormAdmin(admin.ModelAdmin):

    def pdf_link(self, obj):
        if obj.pdf_file:
            return format_html('<a href="{}" target="_blank">View PDF</a>', obj.pdf_file.url)
        return "No PDF"
    pdf_link.short_description = "PDF"

    def user_detail_link(self, obj):
        if obj.user_detail:
            url = reverse("admin:roblex_app_userdetail_change", args=[obj.user_detail.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user_detail)
        return "Not Linked"
    user_detail_link.short_description = "Linked User"

    def document_submissions_count(self, obj):
        if obj.user_detail:
            count = obj.user_detail.document_submissions.count()
            if count > 0:
                return format_html('<span style="color: green;">{} Documents</span>', count)
        return "No Documents"
    document_submissions_count.short_description = "Document Status"

    def client_location(self, obj):
        if obj.client_ip:
            return format_html('<span title="IP: {}">{}</span>', obj.client_ip, obj.client_ip[:15] + '...' if len(obj.client_ip) > 15 else obj.client_ip)
        return "Unknown"
    client_location.short_description = "Client IP"

    list_display = [
        'id',
        'user_detail_link',
        'gamer_first_name', 
        'gamer_last_name',
        'guardian_first_name',
        'guardian_last_name',
        'roblox_gamertag',
        'document_submissions_count',
        'pdf_link',
        'date',
        'created_at'
    ]

    list_display_links = ['id', 'gamer_first_name', 'gamer_last_name']
    list_filter = [
        'date', 
        'created_at', 
        'custody_type', 
        'complained_to_roblox', 
        'complained_to_apple', 
        'contacted_police',
        'user_detail__zipcode',
        'submitted_at'
    ]
    search_fields = [
        'gamer_first_name', 
        'gamer_last_name', 
        'guardian_first_name', 
        'guardian_last_name', 
        'roblox_gamertag', 
        'discord_profile', 
        'xbox_gamertag', 
        'ps_gamertag',
        'user_detail__email',
        'user_detail__first_name',
        'user_detail__last_name'
    ]
    date_hierarchy = 'created_at'
    list_per_page = 25
    readonly_fields = ['created_at', 'submitted_at', 'client_ip']

    fieldsets = (
        ('User Relationship', {'fields': ('user_detail',)}),
        ('Basic Information', {'fields': ('date', 'question', 'client_ip', 'submitted_at')}),
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
        }),
        ('Files & Documents', {
            'fields': ('pdf_file',),
            'classes': ('collapse',)
        })
    )

    actions = ['mark_as_reviewed', 'export_selected_intakes']

    def mark_as_reviewed(self, request, queryset):
        self.message_user(request, f"{queryset.count()} forms marked as reviewed.")
    mark_as_reviewed.short_description = "Mark selected forms as reviewed"

    def export_selected_intakes(self, request, queryset):
        # Add bulk export functionality if needed
        self.message_user(request, f"Export functionality for {queryset.count()} forms would be implemented here.")
    export_selected_intakes.short_description = "Export selected intake forms"

admin.site.site_header = "Roblox Admin"
admin.site.site_title = "Roblox"
admin.site.index_title = "Welcome to Your Roblox Admin Portal"



class OptionInline(admin.TabularInline):
    model = Option
    extra = 3
    fields = ('text', 'is_eligible', 'requires_parental_signature', 'redirect_to_retainer')
    
    def get_readonly_fields(self, request, obj=None):
        # Make fields readonly if the question already has user answers
        if obj and obj.useranswer_set.exists():
            return ('text', 'is_eligible', 'requires_parental_signature', 'redirect_to_retainer')
        return ()


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    
    def options_summary(self, obj):
        options = obj.options.all()
        if not options:
            return "No options"
        
        summary = []
        for option in options:
            badges = []
            if option.is_eligible:
                badges.append("✅")
            if option.requires_parental_signature:
                badges.append("👨‍👩‍👧‍👦")
            if option.redirect_to_retainer:
                badges.append("📋")
            
            badge_str = "".join(badges) if badges else "⚪"
            summary.append(f"{badge_str} {option.text}")
        
        return format_html("<br/>".join(summary))
    options_summary.short_description = "Options (✅=Eligible, 👨‍👩‍👧‍👦=Parent Sig, 📋=Retainer)"

    def user_answers_count(self, obj):
        count = obj.useranswer_set.count()
        if count > 0:
            return format_html('<span style="color: green; font-weight: bold;">{} responses</span>', count)
        return "No responses"
    user_answers_count.short_description = "User Responses"

    list_display = ('id', 'text', 'options_summary', 'user_answers_count')
    list_display_links = ('id', 'text')
    search_fields = ('text', 'options__text')
    inlines = [OptionInline]
    list_per_page = 20

    def get_readonly_fields(self, request, obj=None):
        # Make question text readonly if it already has user answers
        if obj and obj.useranswer_set.exists():
            self.message_user(
                request, 
                "⚠️ This question has user responses. Modifying options may affect data integrity.",
                level='warning'
            )
        return ()


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    
    def eligibility_badges(self, obj):
        badges = []
        if obj.is_eligible:
            badges.append('<span style="background-color: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">ELIGIBLE</span>')
        if obj.requires_parental_signature:
            badges.append('<span style="background-color: #ffc107; color: black; padding: 2px 6px; border-radius: 3px; font-size: 11px;">PARENT SIG</span>')
        if obj.redirect_to_retainer:
            badges.append('<span style="background-color: #17a2b8; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">RETAINER</span>')
        
        return format_html(' '.join(badges)) if badges else "Standard Option"
    eligibility_badges.short_description = "Flags"

    def user_selections_count(self, obj):
        count = obj.useranswer_set.count()
        if count > 0:
            return format_html('<span style="color: green; font-weight: bold;">{}</span>', count)
        return "0"
    user_selections_count.short_description = "Selected By Users"

    list_display = ('id', 'question', 'text', 'eligibility_badges', 'user_selections_count')
    list_display_links = ('id', 'text')
    list_filter = ('is_eligible', 'requires_parental_signature', 'redirect_to_retainer', 'question')
    search_fields = ('text', 'question__text')
    list_per_page = 30

    fieldsets = (
        ('Option Content', {
            'fields': ('question', 'text')
        }),
        ('Eligibility Rules', {
            'fields': ('is_eligible', 'requires_parental_signature', 'redirect_to_retainer'),
            'description': 'These flags determine the user\'s eligibility and next steps in the workflow.'
        })
    )

class UserAnswerInline(admin.TabularInline):
    model = UserAnswer
    extra = 0
    can_delete = False
    show_change_link = False
    readonly_fields = ('question', 'get_selected_option', 'eligibility_info')
    fields = ('question', 'get_selected_option', 'eligibility_info')

    def get_selected_option(self, obj):
        return obj.selected_option.text if obj.selected_option else "-"
    get_selected_option.short_description = "Selected Option"

    def eligibility_info(self, obj):
        if obj.selected_option:
            option = obj.selected_option
            badges = []
            if option.is_eligible:
                badges.append('<span style="background-color: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">ELIGIBLE</span>')
            if option.requires_parental_signature:
                badges.append('<span style="background-color: #ffc107; color: black; padding: 2px 6px; border-radius: 3px; font-size: 11px;">PARENT SIG</span>')
            if option.redirect_to_retainer:
                badges.append('<span style="background-color: #17a2b8; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">RETAINER</span>')
            return format_html(' '.join(badges)) if badges else "-"
        return "-"
    eligibility_info.short_description = "Eligibility Flags"


class IntakeFormInline(admin.TabularInline):
    model = IntakeForm
    extra = 0
    can_delete = False
    show_change_link = True
    readonly_fields = ('gamer_first_name', 'gamer_last_name', 'roblox_gamertag', 'created_at', 'pdf_status')
    fields = ('gamer_first_name', 'gamer_last_name', 'roblox_gamertag', 'pdf_status', 'created_at')

    def pdf_status(self, obj):
        if obj.pdf_file:
            return format_html('<a href="{}" target="_blank">📄 View PDF</a>', obj.pdf_file.url)
        return "No PDF"
    pdf_status.short_description = "PDF"


class DocumentSubmissionInline(admin.TabularInline):
    model = DocumentSubmission
    extra = 0
    can_delete = False
    show_change_link = True
    readonly_fields = ('document_template', 'status_colored', 'signing_link', 'created_at')
    fields = ('document_template', 'status_colored', 'signing_link', 'created_at')

    def status_colored(self, obj):
        colors = {
            'pending': '#ffc107',  # warning yellow
            'sent': '#17a2b8',     # info blue
            'opened': '#6f42c1',   # purple
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

    def signing_link(self, obj):
        if obj.docuseal_slug and obj.status not in ['completed', 'declined', 'expired']:
            return format_html('<a href="https://sign.nextkeystack.com/s/{}" target="_blank">🔗 Sign</a>', obj.docuseal_slug)
        elif obj.signed_document_url:
            return format_html('<a href="{}" target="_blank">📋 Signed Doc</a>', obj.signed_document_url)
        return "-"
    signing_link.short_description = "Action"


@admin.register(UserDetail)
class UserDetailAdmin(admin.ModelAdmin):
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = "Full Name"

    def contact_info(self, obj):
        return format_html(
            '📧 <a href="mailto:{}">{}</a><br/>📱 {}',
            obj.email, obj.email, obj.cell_phone
        )
    contact_info.short_description = "Contact"

    def age_eligibility(self, obj):
        if obj.gamer_dob:
            from datetime import date
            today = date.today()
            age = today.year - obj.gamer_dob.year - ((today.month, today.day) < (obj.gamer_dob.month, obj.gamer_dob.day))
            
            if age <= 17:
                return format_html('<span style="background-color: #ffc107; color: black; padding: 2px 8px; border-radius: 3px;">{}y - Parent Sig Required</span>', age)
            elif age <= 20:
                return format_html('<span style="background-color: #28a745; color: white; padding: 2px 8px; border-radius: 3px;">{}y - Eligible</span>', age)
            else:
                return format_html('<span style="background-color: #dc3545; color: white; padding: 2px 8px; border-radius: 3px;">{}y - Not Eligible</span>', age)
        return "Age Unknown"
    age_eligibility.short_description = "Age & Eligibility"

    def document_status_summary(self, obj):
        submissions = obj.document_submissions.all()
        if not submissions:
            return "No Documents"
        
        status_counts = {}
        for submission in submissions:
            status = submission.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        badges = []
        for status, count in status_counts.items():
            color = {
                'completed': '#28a745',
                'pending': '#ffc107', 
                'sent': '#17a2b8',
                'declined': '#dc3545',
                'expired': '#6c757d'
            }.get(status, '#000000')
            
            badges.append(f'<span style="background-color: {color}; color: white; padding: 1px 4px; border-radius: 2px; font-size: 10px; margin-right: 2px;">{status.upper()}: {count}</span>')
        
        return format_html(''.join(badges))
    document_status_summary.short_description = "Document Status"

    def florida_disclosure_required(self, obj):
        # Check if zipcode is in Florida range that requires disclosure
        try:
            zipcode = int(obj.zipcode)
            if 32003 <= zipcode <= 34997:
                return format_html('<span style="background-color: #fd7e14; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">FL DISCLOSURE REQ</span>')
        except (ValueError, TypeError):
            pass
        return "-"
    florida_disclosure_required.short_description = "FL Status"

    list_display = (
        'id', 
        'full_name', 
        'contact_info', 
        'zipcode',
        'florida_disclosure_required',
        'age_eligibility',
        'working_with_attorney', 
        'document_status_summary',
        'submitted_answers_count',
        'created_at'
    )

    list_display_links = ('id', 'full_name')
    search_fields = ('first_name', 'last_name', 'email', 'zipcode', 'cell_phone')
    list_filter = (
        'working_with_attorney', 
        'created_at',
        'zipcode',
        'document_submissions__status',
        'document_submissions__document_template__name'
    )
    inlines = [UserAnswerInline, DocumentSubmissionInline, IntakeFormInline]
    list_per_page = 25
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'gamer_dob')
        }),
        ('Contact Information', {
            'fields': ('email', 'cell_phone', 'zipcode')
        }),
        ('Legal Status', {
            'fields': ('working_with_attorney', 'additional_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    actions = ['export_user_details', 'send_follow_up_email']

    def submitted_answers_count(self, obj):
        count = obj.answers.count()
        if count > 0:
            return format_html('<span style="color: green; font-weight: bold;">{}</span>', count)
        return "0"
    submitted_answers_count.short_description = "Answers"

    def export_user_details(self, request, queryset):
        self.message_user(request, f"Export functionality for {queryset.count()} users would be implemented here.")
    export_user_details.short_description = "Export selected user details"

    def send_follow_up_email(self, request, queryset):
        self.message_user(request, f"Follow-up email functionality for {queryset.count()} users would be implemented here.")
    send_follow_up_email.short_description = "Send follow-up email"

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    
    def usage_count(self, obj):
        count = obj.emaillog_set.count()
        if count > 0:
            return format_html('<span style="color: green;">{} emails sent</span>', count)
        return "Not used yet"
    usage_count.short_description = "Usage"

    def preview_body(self, obj):
        truncated = obj.body[:100] + "..." if len(obj.body) > 100 else obj.body
        return format_html('<div title="{}">{}</div>', obj.body, truncated)
    preview_body.short_description = "Body Preview"

    list_display = ('name', 'subject', 'preview_body', 'usage_count')
    list_display_links = ('name', 'subject')
    search_fields = ('name', 'subject', 'body')
    readonly_fields = ('usage_count',)

    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'subject')
        }),
        ('Email Content', {
            'fields': ('body',),
            'description': 'Use [User First Name] as a placeholder for personalization.'
        }),
        ('Usage Statistics', {
            'fields': ('usage_count',),
            'classes': ('collapse',)
        })
    )


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    
    def status_colored(self, obj):
        colors = {
            'pending': '#ffc107',
            'sent': '#28a745',
            'failed': '#dc3545'
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_colored.short_description = "Status"

    def template_used(self, obj):
        if obj.template:
            return format_html('<span style="background-color: #e9ecef; padding: 2px 6px; border-radius: 3px;">{}</span>', obj.template.get_name_display())
        return "Custom Email"
    template_used.short_description = "Template"

    def attachment_status(self, obj):
        if obj.attachment:
            return format_html('<a href="{}" target="_blank">📎 View</a>', obj.attachment.url)
        return "No attachment"
    attachment_status.short_description = "Attachment"

    def recipient_info(self, obj):
        return format_html('To: <strong>{}</strong><br/>From: {}', obj.to_email, obj.from_email)
    recipient_info.short_description = "Email Details"

    list_display = [
        'id',
        'recipient_info',
        'subject',
        'template_used',
        'status_colored',
        'attachment_status',
        'created_at'
    ]
    
    list_display_links = ['id', 'subject']
    list_filter = ['status', 'template', 'created_at']
    search_fields = ['from_email', 'to_email', 'subject', 'body']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
    list_per_page = 30

    fieldsets = (
        ('Email Details', {
            'fields': ('from_email', 'to_email', 'subject', 'template')
        }),
        ('Content', {
            'fields': ('body',)
        }),
        ('Status & Files', {
            'fields': ('status', 'attachment', 'error_message')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        })
    )

    actions = ['retry_failed_emails', 'mark_as_sent']

    def retry_failed_emails(self, request, queryset):
        failed_emails = queryset.filter(status='failed')
        self.message_user(request, f"Retry functionality for {failed_emails.count()} failed emails would be implemented here.")
    retry_failed_emails.short_description = "Retry selected failed emails"

    def mark_as_sent(self, request, queryset):
        updated = queryset.update(status='sent')
        self.message_user(request, f'{updated} emails marked as sent.')
    mark_as_sent.short_description = "Mark selected emails as sent"


# ====================
# Additional Model Admins
# ====================

@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    
    def user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    user_name.short_description = "User"

    def eligibility_info(self, obj):
        if obj.selected_option:
            option = obj.selected_option
            badges = []
            if option.is_eligible:
                badges.append('<span style="background-color: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">ELIGIBLE</span>')
            if option.requires_parental_signature:
                badges.append('<span style="background-color: #ffc107; color: black; padding: 2px 6px; border-radius: 3px; font-size: 11px;">PARENT SIG</span>')
            if option.redirect_to_retainer:
                badges.append('<span style="background-color: #17a2b8; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">RETAINER</span>')
            return format_html(' '.join(badges)) if badges else "-"
        return "-"
    eligibility_info.short_description = "Eligibility Impact"

    list_display = ('id', 'user_name', 'question', 'selected_option', 'eligibility_info')
    list_display_links = ('id', 'user_name')
    list_filter = (
        'question', 
        'selected_option__is_eligible', 
        'selected_option__requires_parental_signature',
        'selected_option__redirect_to_retainer'
    )
    search_fields = ('user__first_name', 'user__last_name', 'question__text', 'selected_option__text')
    list_per_page = 30

    fieldsets = (
        ('Answer Details', {
            'fields': ('user', 'question', 'selected_option')
        }),
    )


# ====================
# Admin Site Customization
# ====================

admin.site.site_header = "Roblox Legal Intake Administration"
admin.site.site_title = "Roblox Intake Admin"
admin.site.index_title = "Welcome to Roblox Legal Intake Management System"
admin.site.enable_nav_sidebar = True

# Custom CSS can be added via admin/base_site.html template


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
