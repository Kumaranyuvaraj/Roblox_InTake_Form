from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Q
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib import messages
from django import forms
from django.forms import PasswordInput
from .models import (
    LawFirm, LawFirmUser, DocumentTemplate, EmailTemplate,
    ExcelUpload, RetainerRecipient, DocumentSubmission, DocumentWebhookEvent
)


class SuperuserOnlyModelAdmin(admin.ModelAdmin):
    """Base admin class that only shows models to superusers"""
    
    def has_module_permission(self, request):
        return request.user.is_superuser
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class LawFirmFilteredModelAdmin(admin.ModelAdmin):
    """Base admin class that filters data by law firm for non-superusers"""
    
    def get_user_law_firm(self, request):
        """Get the law firm associated with the current user"""
        if request.user.is_superuser:
            return None
        
        try:
            # Import here to avoid circular imports
            from roblex_app.models import LawFirmUser as RoblexLawFirmUser
            try:
                law_firm_user = RoblexLawFirmUser.objects.get(user=request.user)
                # Find corresponding retainer app law firm
                retainer_law_firm = LawFirm.objects.get(name=law_firm_user.law_firm.name)
                return retainer_law_firm
            except RoblexLawFirmUser.DoesNotExist:
                # Try retainer app law firm user
                law_firm_user = LawFirmUser.objects.get(user=request.user)
                return law_firm_user.law_firm
        except (LawFirmUser.DoesNotExist, LawFirm.DoesNotExist):
            return None
    
    def get_queryset(self, request):
        """Filter queryset based on user's law firm"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        
        user_law_firm = self.get_user_law_firm(request)
        if user_law_firm:
            law_firm_field = self.get_law_firm_field_name()
            if law_firm_field:
                filter_kwargs = {law_firm_field: user_law_firm}
                return qs.filter(**filter_kwargs)
        
        return qs.none()
    
    def get_law_firm_field_name(self):
        """Override this method to specify the law firm field name for each model"""
        if hasattr(self.model, 'law_firm'):
            return 'law_firm'
        return None
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter foreign key choices based on user's law firm"""
        if request.user.is_superuser:
            return super().formfield_for_foreignkey(db_field, request, **kwargs)
        
        user_law_firm = self.get_user_law_firm(request)
        
        if db_field.name == "law_firm" and user_law_firm:
            kwargs["queryset"] = LawFirm.objects.filter(id=user_law_firm.id)
        
        if db_field.name == "document_template" and user_law_firm:
            kwargs["queryset"] = DocumentTemplate.objects.filter(law_firm=user_law_firm)
            
        if db_field.name == "email_template" and user_law_firm:
            kwargs["queryset"] = EmailTemplate.objects.filter(
                Q(law_firm=user_law_firm) | Q(law_firm__isnull=True)
            )
            
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ====================
# Custom Forms
# ====================

class LawFirmAdminForm(forms.ModelForm):
    """Custom form for LawFirm admin with password field"""
    email_host_password = forms.CharField(
        widget=PasswordInput(render_value=False),
        required=False,
        help_text="SMTP password or app password. Leave blank to keep existing password."
    )
    
    class Meta:
        model = LawFirm
        fields = '__all__'


# ====================
# Law Firm Management
# ====================

@admin.register(LawFirm)
class LawFirmAdmin(SuperuserOnlyModelAdmin):
    form = LawFirmAdminForm
    def users_count(self, obj):
        count = obj.users.count()
        if count > 0:
            return format_html('<span style="color: green; font-weight: bold;">{} users</span>', count)
        return "No users"
    users_count.short_description = "Users"

    def uploads_count(self, obj):
        count = obj.excel_uploads.count()
        if count > 0:
            return format_html('<span style="color: blue; font-weight: bold;">{} uploads</span>', count)
        return "No uploads"
    uploads_count.short_description = "Excel Uploads"

    def templates_count(self, obj):
        count = obj.document_templates.count()
        if count > 0:
            return format_html('<span style="color: purple; font-weight: bold;">{} templates</span>', count)
        return "No templates"
    templates_count.short_description = "Document Templates"

    def email_config_status(self, obj):
        if obj.has_email_config():
            return format_html('<span style="color: green; font-weight: bold;">✓ Configured</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">✗ Incomplete</span>')
    email_config_status.short_description = "Email Config"

    def test_email_action(self, request, queryset):
        """Admin action to test email configuration"""
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one law firm to test email", messages.ERROR)
            return
        
        law_firm = queryset.first()
        if not law_firm.has_email_config():
            self.message_user(request, f"Law firm {law_firm.name} has incomplete email configuration", messages.ERROR)
            return
            
        # Import here to avoid circular import
        from .tasks import test_law_firm_email
        
        # Use a test email - in production, you might want to make this configurable
        test_email = "test@example.com"  # Replace with actual test email
        
        test_law_firm_email.delay(law_firm.id, test_email)
        self.message_user(request, f"Test email queued for {law_firm.name} to {test_email}", messages.SUCCESS)
    
    test_email_action.short_description = "Test email configuration"

    list_display = [
        'name', 'subdomain', 'contact_email', 'email_config_status',
        'users_count', 'uploads_count', 'templates_count', 'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'subdomain', 'contact_email', 'email_host_user']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['test_email_action']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'subdomain', 'contact_email', 'phone_number', 'address', 'is_active')
        }),
        ('Email Configuration', {
            'fields': (
                'email_host', 'email_port', 'email_use_tls', 'email_use_ssl',
                'email_host_user', 'email_host_password',
                'email_from_name', 'email_from_email'
            ),
            'description': 'Configure SMTP settings for sending retainer emails. Leave password field blank to keep existing password.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        # Don't overwrite password if field is left blank on update
        if change and not obj.email_host_password:
            original = LawFirm.objects.get(pk=obj.pk)
            obj.email_host_password = original.email_host_password
        super().save_model(request, obj, form, change)


@admin.register(LawFirmUser)
class LawFirmUserAdmin(SuperuserOnlyModelAdmin):
    def user_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    user_full_name.short_description = "User Name"

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "Email"

    def role_badge(self, obj):
        colors = {
            'super_admin': '#dc3545',
            'law_firm_admin': '#ffc107',
            'law_firm_staff': '#28a745',
            'law_firm_viewer': '#6c757d'
        }
        color = colors.get(obj.role, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_role_display()
        )
    role_badge.short_description = "Role"

    list_display = ['user_full_name', 'user_email', 'law_firm', 'role_badge', 'is_active', 'created_at']
    list_filter = ['role', 'law_firm', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email', 'law_firm__name']


# ====================
# Template Management
# ====================

@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(LawFirmFilteredModelAdmin):
    def template_name_display(self, obj):
        return obj.display_name
    template_name_display.short_description = "Template Name"

    def usage_count(self, obj):
        count = obj.documentsubmission_set.count()
        if count > 0:
            return format_html('<span style="color: green; font-weight: bold;">{} uses</span>', count)
        return "Not used"
    usage_count.short_description = "Usage"

    list_display = ['template_name_display', 'name', 'law_firm', 'nextkeysign_template_id', 'usage_count', 'is_active', 'created_at']
    list_filter = ['name', 'law_firm', 'is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description', 'nextkeysign_template_id', 'law_firm__name']


@admin.register(EmailTemplate)
class EmailTemplateAdmin(LawFirmFilteredModelAdmin):
    def get_law_firm_field_name(self):
        return 'law_firm'
    
    def get_queryset(self, request):
        """Show global templates and law firm specific templates"""
        qs = super(admin.ModelAdmin, self).get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        
        user_law_firm = self.get_user_law_firm(request)
        if user_law_firm:
            return qs.filter(Q(law_firm=user_law_firm) | Q(law_firm__isnull=True))
        
        return qs.none()

    def scope_display(self, obj):
        if obj.law_firm:
            return format_html(
                '<span style="background-color: #007bff; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
                obj.law_firm.name
            )
        return format_html('<span style="background-color: #28a745; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">Global</span>')
    scope_display.short_description = "Scope"

    def preview_body(self, obj):
        truncated = obj.body[:100] + "..." if len(obj.body) > 100 else obj.body
        return format_html('<div title="{}">{}</div>', obj.body, truncated)
    preview_body.short_description = "Body Preview"

    def email_template_display(self, obj):
        return f"{obj.name} ({obj.template_type})"
    email_template_display.short_description = "Email Template"

    list_display = ['email_template_display', 'scope_display', 'subject', 'preview_body', 'created_at']
    list_filter = ['template_type', 'law_firm', 'created_at']
    search_fields = ['name', 'template_type', 'subject', 'body', 'law_firm__name']


# ====================
# Excel Upload Management
# ====================

@admin.register(ExcelUpload)
class ExcelUploadAdmin(LawFirmFilteredModelAdmin):
    def uploaded_by_name(self, obj):
        return obj.uploaded_by.get_full_name() or obj.uploaded_by.username
    uploaded_by_name.short_description = "Uploaded By"

    def status_colored(self, obj):
        colors = {
            'uploaded': '#6c757d',
            'processing': '#ffc107',
            'completed': '#28a745',
            'failed': '#dc3545'
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_colored.short_description = "Status"

    def progress_bar(self, obj):
        if obj.total_rows and obj.total_rows > 0:
            percentage = (obj.processed_rows / obj.total_rows) * 100
            return format_html(
                '<div style="width: 100px; background-color: #e9ecef; border-radius: 3px;">'
                '<div style="width: {}%; height: 20px; background-color: #007bff; border-radius: 3px;"></div>'
                '</div>'
                '<small>{}/{} ({}%)</small>',
                percentage, obj.processed_rows, obj.total_rows, round(percentage, 1)
            )
        return "Not started"
    progress_bar.short_description = "Progress"

    def success_rate(self, obj):
        rate = obj.get_success_rate()
        if rate > 0:
            color = '#28a745' if rate >= 80 else '#ffc107' if rate >= 60 else '#dc3545'
            return format_html('<span style="color: {}; font-weight: bold;">{}%</span>', color, rate)
        return "N/A"
    success_rate.short_description = "Success Rate"

    def trigger_processing(self, request, queryset):
        """Admin action to trigger processing of uploaded files"""
        from .tasks import process_excel_upload
        for upload in queryset.filter(status='uploaded'):
            process_excel_upload.delay(upload.id)
            self.message_user(request, f'Processing triggered for upload {upload.id}', messages.SUCCESS)
    trigger_processing.short_description = "Trigger processing for selected uploads"

    list_display = [
        'id', 'law_firm', 'uploaded_by_name', 'document_template', 
        'status_colored', 'progress_bar', 'success_rate', 'created_at'
    ]
    list_filter = ['status', 'law_firm', 'document_template', 'created_at']
    search_fields = ['uploaded_by__username', 'law_firm__name']
    readonly_fields = [
        'status', 'total_rows', 'processed_rows', 'successful_submissions', 
        'failed_submissions', 'skipped_rows', 'processing_started_at', 'completed_at'
    ]
    actions = ['trigger_processing']

    def save_model(self, request, obj, form, change):
        """Auto-assign law firm and trigger processing"""
        if not change:  # New upload
            if not request.user.is_superuser:
                user_law_firm = self.get_user_law_firm(request)
                if user_law_firm:
                    obj.law_firm = user_law_firm
            obj.uploaded_by = request.user
        
        super().save_model(request, obj, form, change)
        
        # Trigger processing if new upload
        if not change and obj.status == 'uploaded':
            from .tasks import process_excel_upload
            process_excel_upload.delay(obj.id)
            self.message_user(request, f'Processing started for upload {obj.id}', messages.SUCCESS)


# ====================
# Recipient Management
# ====================

class DocumentSubmissionInline(admin.TabularInline):
    model = DocumentSubmission
    extra = 0
    can_delete = False
    readonly_fields = ['nextkeysign_submission_id', 'status', 'signed_document_url', 'created_at']
    fields = ['document_template', 'status', 'nextkeysign_submission_id', 'signed_document_url', 'created_at']


@admin.register(RetainerRecipient)
class RetainerRecipientAdmin(LawFirmFilteredModelAdmin):
    def get_law_firm_field_name(self):
        return 'excel_upload__law_firm'

    def excel_upload_info(self, obj):
        return f"Upload #{obj.excel_upload.id}"
    excel_upload_info.short_description = "Excel Upload"

    def status_colored(self, obj):
        colors = {
            'pending': '#6c757d',
            'submitted': '#17a2b8',
            'completed': '#28a745',
            'failed': '#dc3545',
            'skipped': '#ffc107'
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_colored.short_description = "Status"

    def retry_failed(self, request, queryset):
        """Admin action to retry failed submissions"""
        from .tasks import retry_failed_submission
        failed_recipients = queryset.filter(status='failed')
        for recipient in failed_recipients:
            retry_failed_submission.delay(recipient.id)
        self.message_user(request, f'Retry triggered for {failed_recipients.count()} failed recipients', messages.SUCCESS)
    retry_failed.short_description = "Retry failed submissions"

    list_display = [
        'external_id', 'name', 'email', 'excel_upload_info', 
        'status_colored', 'retry_count', 'created_at'
    ]
    list_filter = ['status', 'excel_upload__law_firm', 'excel_upload', 'created_at']
    search_fields = ['external_id', 'name', 'email', 'excel_upload__id']
    readonly_fields = ['status', 'retry_count', 'error_message', 'last_processed_at']
    actions = ['retry_failed']
    inlines = [DocumentSubmissionInline]


# ====================
# Document Submission Tracking
# ====================

@admin.register(DocumentSubmission)
class DocumentSubmissionAdmin(LawFirmFilteredModelAdmin):
    def get_law_firm_field_name(self):
        return 'recipient__excel_upload__law_firm'

    def recipient_name(self, obj):
        return obj.recipient.name
    recipient_name.short_description = "Recipient"

    def recipient_email(self, obj):
        return obj.recipient.email
    recipient_email.short_description = "Email"

    def status_colored(self, obj):
        colors = {
            'pending': '#6c757d',
            'sent': '#17a2b8',
            'opened': '#6f42c1',
            'completed': '#28a745',
            'declined': '#dc3545',
            'expired': '#ffc107'
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_colored.short_description = "Status"

    def signing_link(self, obj):
        if obj.nextkeysign_slug and obj.status not in ['completed', 'declined', 'expired']:
            url = f"{settings.NEXTKEYSIGN_BASE_URL}/s/{obj.nextkeysign_slug}"
            return format_html('<a href="{}" target="_blank">🔗 Sign Document</a>', url)
        return "N/A"
    signing_link.short_description = "Signing Link"

    def signed_document_link(self, obj):
        if obj.signed_document_url:
            return format_html('<a href="{}" target="_blank">📋 View Signed Document</a>', obj.signed_document_url)
        return "Not signed"
    signed_document_link.short_description = "Signed Document"

    list_display = [
        'recipient_name', 'recipient_email', 'document_template', 
        'status_colored', 'signing_link', 'signed_document_link', 'created_at'
    ]
    list_filter = [
        'status', 'document_template', 'recipient__excel_upload__law_firm', 
        'created_at', 'completed_at'
    ]
    search_fields = [
        'recipient__name', 'recipient__email', 'nextkeysign_submission_id', 'external_id'
    ]
    readonly_fields = [
        'nextkeysign_submission_id', 'nextkeysign_submitter_id', 'nextkeysign_slug', 
        'external_id', 'created_at', 'updated_at', 'sent_at', 'completed_at'
    ]


# ====================
# Webhook Event Tracking
# ====================

@admin.register(DocumentWebhookEvent)
class DocumentWebhookEventAdmin(SuperuserOnlyModelAdmin):
    def submission_info(self, obj):
        return f"{obj.document_submission.recipient.name} - {obj.document_submission.document_template}"
    submission_info.short_description = "Submission"

    def processed_status(self, obj):
        if obj.processed:
            return format_html('<span style="color: green;">✓ Processed</span>')
        else:
            return format_html('<span style="color: red;">✗ Pending</span>')
    processed_status.short_description = "Status"

    list_display = ['event_type', 'submission_info', 'processed_status', 'created_at']
    list_filter = ['event_type', 'processed', 'created_at']
    search_fields = ['document_submission__recipient__name', 'event_type']
    readonly_fields = ['webhook_data', 'created_at']


# ====================
# Admin Site Customization
# ====================

admin.site.site_header = "Retainer Document Management"
admin.site.site_title = "Retainer Admin"
admin.site.index_title = "Welcome to Retainer Document Management System"
