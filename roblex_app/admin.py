from django.contrib import admin
from roblex_app.models import (
    IntakeForm, Question, Option, EmailLog, UserDetail, UserAnswer, 
    EmailTemplate, DocumentTemplate, DocumentSubmission, DocumentWebhookEvent,
    LawFirm, LawFirmUser
)

from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Q
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.admin import AdminSite


class SuperuserOnlyModelAdmin(admin.ModelAdmin):
    """Base admin class that only shows models to superusers"""
    
    def has_module_permission(self, request):
        """Only show this model section to superusers"""
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
            return None  # Superusers see all data
        
        try:
            from roblex_app.models import LawFirmUser
            law_firm_user = LawFirmUser.objects.get(user=request.user)
            return law_firm_user.law_firm
        except LawFirmUser.DoesNotExist:
            return None
    
    def get_queryset(self, request):
        """Filter queryset based on user's law firm"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs  # Superusers see everything
        
        user_law_firm = self.get_user_law_firm(request)
        if user_law_firm:
            # Different models have different field names for law firm relationship
            law_firm_field = self.get_law_firm_field_name()
            if law_firm_field:
                filter_kwargs = {law_firm_field: user_law_firm}
                return qs.filter(**filter_kwargs)
        
        # If no law firm found, return empty queryset
        return qs.none()
    
    def get_law_firm_field_name(self):
        """Override this method to specify the law firm field name for each model"""
        # Default common field names
        model = self.model
        if hasattr(model, 'law_firm'):
            return 'law_firm'
        elif hasattr(model, 'user_detail__law_firm'):
            return 'user_detail__law_firm'
        return None
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter foreign key choices based on user's law firm"""
        if request.user.is_superuser:
            return super().formfield_for_foreignkey(db_field, request, **kwargs)
        
        user_law_firm = self.get_user_law_firm(request)
        
        # Filter law firm choices
        if db_field.name == "law_firm" and user_law_firm:
            kwargs["queryset"] = LawFirm.objects.filter(id=user_law_firm.id)
        
        # Filter user detail choices to only show users from the same law firm
        if db_field.name == "user_detail" and user_law_firm:
            from roblex_app.models import UserDetail
            kwargs["queryset"] = UserDetail.objects.filter(law_firm=user_law_firm)
            
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ====================
# Law Firm Multi-Tenant Administration
# ====================

class LawFirmUserInline(admin.TabularInline):
    model = LawFirmUser
    extra = 0
    can_delete = False
    fields = ('user', 'role', 'is_active')
    readonly_fields = ('user',)

@admin.register(LawFirm)
class LawFirmAdmin(SuperuserOnlyModelAdmin):
    def users_count(self, obj):
        count = obj.users.count()
        if count > 0:
            return format_html('<span style="color: green; font-weight: bold;">{} users</span>', count)
        return "No users"
    users_count.short_description = "Users"

    def leads_count(self, obj):
        count = obj.get_leads_count()
        if count > 0:
            return format_html('<span style="color: blue; font-weight: bold;">{} leads</span>', count)
        return "No leads"
    leads_count.short_description = "Total Leads"

    def active_leads_count(self, obj):
        count = obj.get_active_leads_count()
        if count > 0:
            return format_html('<span style="color: green; font-weight: bold;">{} active</span>', count)
        return "No active leads"
    active_leads_count.short_description = "Active Leads"

    def full_domain_link(self, obj):
        if obj.subdomain != 'default':
            return format_html('<a href="https://{}" target="_blank">{}</a>', obj.full_domain, obj.full_domain)
        return "Default (localhost)"
    full_domain_link.short_description = "Domain"

    list_display = [
        'name',
        'subdomain', 
        'full_domain_link',
        'contact_email',
        'phone_number',
        'users_count',
        'leads_count',
        'active_leads_count',
        'is_active',
        'created_at'
    ]
    
    list_display_links = ['name', 'subdomain']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'subdomain', 'contact_email']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'subdomain', 'is_active')
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'phone_number', 'address')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [LawFirmUserInline]
    
    actions = ['activate_law_firms', 'deactivate_law_firms']
    
    def activate_law_firms(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} law firms activated.')
    activate_law_firms.short_description = "Activate selected law firms"
    
    def deactivate_law_firms(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} law firms deactivated.')
    deactivate_law_firms.short_description = "Deactivate selected law firms"


@admin.register(LawFirmUser)
class LawFirmUserAdmin(SuperuserOnlyModelAdmin):
    def user_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    user_full_name.short_description = "User Name"

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "Email"

    def law_firm_name(self, obj):
        return obj.law_firm.name if obj.law_firm else "Super Admin"
    law_firm_name.short_description = "Law Firm"

    def role_badge(self, obj):
        colors = {
            'super_admin': '#dc3545',  # danger red
            'law_firm_admin': '#ffc107',  # warning yellow
            'law_firm_staff': '#28a745',  # success green
            'law_firm_viewer': '#6c757d'  # secondary gray
        }
        color = colors.get(obj.role, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_role_display()
        )
    role_badge.short_description = "Role"

    def permissions_summary(self, obj):
        permissions = []
        if obj.can_manage_users():
            permissions.append("👥 Manage Users")
        if obj.can_edit_data():
            permissions.append("✏️ Edit Data")
        if obj.is_super_admin():
            permissions.append("🔑 Super Admin")
        return " | ".join(permissions) if permissions else "View Only"
    permissions_summary.short_description = "Permissions"

    list_display = [
        'user_full_name',
        'user_email',
        'law_firm_name',
        'role_badge',
        'permissions_summary',
        'is_active',
        'created_at'
    ]
    
    list_display_links = ['user_full_name']
    list_filter = ['role', 'law_firm', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email', 'law_firm__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('User Assignment', {
            'fields': ('user', 'law_firm')
        }),
        ('Access Control', {
            'fields': ('role', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    actions = ['activate_users', 'deactivate_users']
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users activated.')
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users deactivated.')
    deactivate_users.short_description = "Deactivate selected users"


@admin.register(IntakeForm)
class IntakeFormAdmin(LawFirmFilteredModelAdmin):

    def get_law_firm_field_name(self):
        """IntakeForm uses 'law_firm' field directly"""
        return 'law_firm'
    
    def get_queryset(self, request):
        """Custom filtering for IntakeForm - handle both direct law_firm and user_detail.law_firm"""
        qs = super(admin.ModelAdmin, self).get_queryset(request)  # Skip LawFirmFilteredModelAdmin's get_queryset
        
        if request.user.is_superuser:
            return qs  # Superusers see everything
        
        user_law_firm = self.get_user_law_firm(request)
        if user_law_firm:
            # Filter by either direct law_firm field OR user_detail.law_firm
            return qs.filter(
                Q(law_firm=user_law_firm) | 
                Q(user_detail__law_firm=user_law_firm)
            )
        
        # If no law firm found, return empty queryset
        return qs.none()
    
    def save_model(self, request, obj, form, change):
        """Ensure law_firm is set from user_detail if missing"""
        if obj.user_detail and obj.user_detail.law_firm and not obj.law_firm:
            obj.law_firm = obj.user_detail.law_firm
        super().save_model(request, obj, form, change)

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

    def law_firm_name(self, obj):
        if obj.law_firm:
            return format_html('<span style="background-color: #007bff; color: white; padding: 2px 6px; border-radius: 3px;" title="Direct law_firm field">{}</span>', obj.law_firm.name)
        elif obj.user_detail and obj.user_detail.law_firm:
            return format_html('<span style="background-color: #dc3545; color: white; padding: 2px 6px; border-radius: 3px;" title="From user_detail.law_firm">{} (from user)</span>', obj.user_detail.law_firm.name)
        return format_html('<span style="background-color: #6c757d; color: white; padding: 2px 6px; border-radius: 3px;">No Law Firm</span>')
    law_firm_name.short_description = "Law Firm"

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
        'law_firm_name',
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
        'law_firm',
        'user_detail__law_firm',
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
        'user_detail__last_name',
        'law_firm__name'
    ]
    date_hierarchy = 'created_at'
    list_per_page = 25
    readonly_fields = ['created_at', 'submitted_at', 'client_ip', 'law_firm']

    fieldsets = (
        ('Law Firm & User Relationship', {'fields': ('law_firm', 'user_detail')}),
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
class QuestionAdmin(SuperuserOnlyModelAdmin):
    
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
class OptionAdmin(SuperuserOnlyModelAdmin):
    
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
        if obj.nextkeysign_slug and obj.status not in ['completed', 'declined', 'expired']:
            return format_html('<a href="https://sign.nextkeystack.com/s/{}" target="_blank">🔗 Sign</a>', obj.nextkeysign_slug)
        elif obj.signed_document_url:
            return format_html('<a href="{}" target="_blank">📋 Signed Doc</a>', obj.signed_document_url)
        return "-"
    signing_link.short_description = "Action"


@admin.register(UserDetail)
class UserDetailAdmin(LawFirmFilteredModelAdmin):
    
    def get_law_firm_field_name(self):
        """UserDetail uses 'law_firm' field directly"""
        return 'law_firm'
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = "Full Name"

    def law_firm_badge(self, obj):
        if obj.law_firm:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
                obj.law_firm.name
            )
        return format_html('<span style="background-color: #dc3545; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">No Law Firm</span>')
    law_firm_badge.short_description = "Law Firm"

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
        'law_firm_badge',
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
    search_fields = ('first_name', 'last_name', 'email', 'zipcode', 'cell_phone', 'law_firm__name')
    list_filter = (
        'law_firm',
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
        ('Law Firm Assignment', {
            'fields': ('law_firm',),
            'description': 'This field is automatically set based on the subdomain when the user is created.'
        }),
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
class EmailTemplateAdmin(SuperuserOnlyModelAdmin):
    
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
class EmailLogAdmin(LawFirmFilteredModelAdmin):
    
    def get_law_firm_field_name(self):
        """EmailLog doesn't have direct law firm relationship, so we need custom filtering"""
        return None  # Will be handled in get_queryset override
    
    def get_queryset(self, request):
        """Custom filtering for EmailLog based on recipient email matching UserDetail law firm"""
        qs = super(admin.ModelAdmin, self).get_queryset(request)  # Skip LawFirmFilteredModelAdmin's get_queryset
        
        if request.user.is_superuser:
            return qs
        
        user_law_firm = self.get_user_law_firm(request)
        if user_law_firm:
            # Filter by emails sent to users in the same law firm
            from roblex_app.models import UserDetail
            law_firm_emails = UserDetail.objects.filter(law_firm=user_law_firm).values_list('email', flat=True)
            return qs.filter(to_email__in=law_firm_emails)
        
        return qs.none()
    
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
class UserAnswerAdmin(SuperuserOnlyModelAdmin):
    
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
admin.site.site_title = "Roblox Multi-Tenant Admin"
admin.site.index_title = "Welcome to Roblox Legal Intake Management System"
admin.site.enable_nav_sidebar = True

# Custom CSS can be added via admin/base_site.html template


# ====================
# NextKeySign Document Signing Admin
# ====================

@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(SuperuserOnlyModelAdmin):
    def law_firm_scope(self, obj):
        if obj.law_firm:
            return format_html(
                '<span style="background-color: #007bff; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
                obj.law_firm.name
            )
        return format_html('<span style="background-color: #28a745; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">Global</span>')
    law_firm_scope.short_description = "Scope"

    def template_usage_count(self, obj):
        count = obj.documentsubmission_set.count()
        if count > 0:
            return format_html('<span style="color: green; font-weight: bold;">{} uses</span>', count)
        return "Not used"
    template_usage_count.short_description = "Usage"

    def template_type_display(self, obj):
        return obj.get_name_display()
    template_type_display.short_description = "Template Type"

    list_display = [
        'template_type_display',
        'law_firm_scope',
        'nextkeysign_template_id', 
        'template_usage_count',
        'is_active',
        'created_at'
    ]
    list_filter = ['name', 'law_firm', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'nextkeysign_template_id', 'law_firm__name']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    list_per_page = 20
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'law_firm', 'nextkeysign_template_id', 'description')
        }),
        ('Configuration', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    def get_queryset(self, request):
        """Filter templates based on user's law firm association if needed"""
        qs = super().get_queryset(request)
        # For now, show all templates to admins
        # In future, could filter based on user's law firm association
        return qs

    actions = ['duplicate_as_law_firm_specific', 'activate_templates', 'deactivate_templates']
    
    def duplicate_as_law_firm_specific(self, request, queryset):
        # This would open a form to create law firm-specific copies
        self.message_user(request, f"Duplication functionality for {queryset.count()} templates would be implemented here.")
    duplicate_as_law_firm_specific.short_description = "Create law firm-specific copies"
    
    def activate_templates(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} templates activated.')
    activate_templates.short_description = "Activate selected templates"
    
    def deactivate_templates(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} templates deactivated.')
    deactivate_templates.short_description = "Deactivate selected templates"


@admin.register(DocumentSubmission)
class DocumentSubmissionAdmin(LawFirmFilteredModelAdmin):
    
    def get_law_firm_field_name(self):
        """DocumentSubmission uses 'user_detail__law_firm' relationship"""
        return 'user_detail__law_firm'
    
    def user_name(self, obj):
        return f"{obj.user_detail.first_name} {obj.user_detail.last_name}"
    user_name.short_description = "User Name"
    
    def user_email(self, obj):
        return obj.user_detail.email
    user_email.short_description = "Email"

    def law_firm_name(self, obj):
        if obj.law_firm:
            return format_html(
                '<span style="background-color: #007bff; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
                obj.law_firm.name
            )
        return "No Law Firm"
    law_firm_name.short_description = "Law Firm"

    def template_scope(self, obj):
        if obj.document_template.law_firm:
            return format_html(
                '<span style="background-color: #17a2b8; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">Law Firm Specific</span>'
            )
        return format_html(
            '<span style="background-color: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">Global Template</span>'
        )
    template_scope.short_description = "Template Scope"
    
    def signing_link(self, obj):
        if obj.nextkeysign_slug and obj.status not in ['completed', 'declined', 'expired']:
            return format_html('<a href="{}/s/{}" target="_blank">🔗 Sign</a>', settings.NEXTKEYSIGN_BASE_URL or 'https://sign.nextkeystack.com', obj.nextkeysign_slug)
        return "No URL"
    signing_link.short_description = "Signing Link"
    
    def signed_document_link(self, obj):
        if obj.signed_document_url:
            return format_html('<a href="{}" target="_blank">📋 View Signed Document</a>', obj.signed_document_url)
        return "Not signed"
    signed_document_link.short_description = "Signed Document"
    
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

    list_display = [
        'id',
        'user_name',
        'user_email',
        'law_firm_name',
        'document_template',
        'template_scope',
        'status_colored',
        'signing_link',
        'signed_document_link',
        'created_at',
        'completed_at'
    ]
    
    list_display_links = ['id', 'user_name']
    list_filter = [
        'status', 
        'document_template',
        'document_template__law_firm',
        'user_detail__law_firm',
        'created_at', 
        'completed_at'
    ]
    search_fields = [
        'user_detail__first_name', 
        'user_detail__last_name', 
        'user_detail__email',
        'user_detail__law_firm__name',
        'nextkeysign_submission_id',
        'external_id'
    ]
    date_hierarchy = 'created_at'
    readonly_fields = ['nextkeysign_submission_id', 'nextkeysign_submitter_id', 'nextkeysign_slug', 'external_id', 'created_at', 'updated_at']
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
        ('NextKeySign Data', {
            'fields': ('nextkeysign_submission_id', 'nextkeysign_submitter_id', 'nextkeysign_slug', 'external_id'),
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
class DocumentWebhookEventAdmin(SuperuserOnlyModelAdmin):
    list_display = [
        'id',
        'event_type',
        'document_submission',
        'processed',
        'created_at'
    ]
    list_filter = ['event_type', 'processed', 'created_at']
    search_fields = ['document_submission__nextkeysign_submission_id', 'event_type']
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
