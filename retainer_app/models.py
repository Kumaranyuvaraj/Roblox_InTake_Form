from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class LawFirm(models.Model):
    """Duplicate of main LawFirm model for retainer database"""
    name = models.CharField(max_length=255, unique=True)
    subdomain = models.CharField(max_length=100, unique=True)
    contact_email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
        # Email Configuration
    email_host = models.CharField(max_length=255, blank=True, help_text="SMTP server hostname (e.g., smtp.gmail.com)")
    email_port = models.IntegerField(default=587, help_text="SMTP server port (587 for TLS, 465 for SSL)")
    email_host_user = models.CharField(max_length=255, blank=True, help_text="SMTP username/email")
    email_host_password = models.CharField(max_length=500, blank=True, help_text="SMTP password or app password (encrypted)")
    email_use_tls = models.BooleanField(default=True, help_text="Use TLS encryption")
    email_use_ssl = models.BooleanField(default=False, help_text="Use SSL encryption")
    email_from_email = models.EmailField(blank=True, help_text="From email address for notifications")
    email_from_name = models.CharField(max_length=255, blank=True, help_text="From name for notifications")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def full_domain(self):
        if self.subdomain == 'default':
            return 'localhost:8000'
        return f"{self.subdomain}.yourdomain.com"

    def get_leads_count(self):
        return self.excel_uploads.count()

    def get_active_leads_count(self):
        return self.excel_uploads.filter(status='completed').count()

    def get_email_config(self):
        """Get email configuration for this law firm"""
        return {
            'EMAIL_HOST': self.email_host,
            'EMAIL_PORT': self.email_port,
            'EMAIL_USE_TLS': self.email_use_tls,
            'EMAIL_USE_SSL': self.email_use_ssl,
            'EMAIL_HOST_USER': self.email_host_user,
            'EMAIL_HOST_PASSWORD': self.email_host_password,
            'DEFAULT_FROM_EMAIL': self.email_from_email or self.contact_email,
            'EMAIL_FROM_NAME': self.email_from_name or self.name,
        }

    def has_email_config(self):
        """Check if law firm has complete email configuration"""
        return bool(
            self.email_host and 
            self.email_host_user and 
            self.email_host_password
        )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Law Firm"
        verbose_name_plural = "Law Firms"
        ordering = ['name']


class LawFirmUser(models.Model):
    """Duplicate of main LawFirmUser model for retainer database"""
    ROLE_CHOICES = [
        ('super_admin', 'Super Administrator'),
        ('law_firm_admin', 'Law Firm Administrator'),
        ('law_firm_staff', 'Law Firm Staff'),
        ('law_firm_viewer', 'Read Only Access'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='retainer_law_firm_profile')
    law_firm = models.ForeignKey(
        LawFirm, 
        on_delete=models.CASCADE, 
        related_name='users',
        null=True, 
        blank=True
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='law_firm_staff')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        law_firm_name = self.law_firm.name if self.law_firm else "Super Admin"
        return f"{self.user.get_full_name() or self.user.username} - {law_firm_name}"

    def is_super_admin(self):
        return self.role == 'super_admin'

    def can_manage_users(self):
        return self.role in ['super_admin', 'law_firm_admin']

    def can_edit_data(self):
        return self.role in ['super_admin', 'law_firm_admin', 'law_firm_staff']

    class Meta:
        verbose_name = "Law Firm User"
        verbose_name_plural = "Law Firm Users"


class DocumentTemplate(models.Model):
    """NextKeySign document templates for retainer documents"""
    # Make it dynamic - no fixed choices, users can create any retainer type
    name = models.CharField(
        max_length=100, 
        help_text="Custom retainer type name (e.g., 'Kratom Retainer', 'Realpage Retainer', etc.)"
    )
    display_name = models.CharField(
        max_length=150,
        help_text="Display name for this retainer type"
    )
    law_firm = models.ForeignKey(
        LawFirm, 
        on_delete=models.CASCADE, 
        related_name='document_templates'
    )
    nextkeysign_template_id = models.CharField(max_length=100)
    description = models.TextField(
        blank=True,
        help_text="Description of this retainer agreement and what cases it covers"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.display_name} - {self.law_firm.name}"

    class Meta:
        verbose_name = "Document Template"
        verbose_name_plural = "Document Templates"
        unique_together = ('name', 'law_firm')


class EmailTemplate(models.Model):
    """Email templates for NextKeySign notifications"""
    # Make it dynamic - no fixed choices, users can create custom email templates
    name = models.CharField(
        max_length=100,
        help_text="Email template name (e.g., 'Kratom Invitation', 'Realpage Reminder', etc.)"
    )
    template_type = models.CharField(
        max_length=50,
        help_text="Template type (invitation, reminder, completion, etc.)"
    )
    law_firm = models.ForeignKey(
        LawFirm, 
        on_delete=models.CASCADE, 
        related_name='email_templates',
        null=True, 
        blank=True,
        help_text="Leave blank for global templates"
    )
    subject = models.CharField(max_length=255)
    body = models.TextField(
        help_text="Supported placeholders: [First Name Injured], [Last Name Injured], [Name], [State], [Age], [External ID]"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        scope = self.law_firm.name if self.law_firm else "Global"
        return f"{self.name} ({self.template_type}) - {scope}"

    class Meta:
        verbose_name = "Email Template"
        verbose_name_plural = "Email Templates"
        unique_together = ('name', 'law_firm')


class ExcelUpload(models.Model):
    """Excel file uploads for bulk retainer document processing"""
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    law_firm = models.ForeignKey(LawFirm, on_delete=models.CASCADE, related_name='excel_uploads')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='retainer_excel_uploads/')
    document_template = models.ForeignKey(DocumentTemplate, on_delete=models.CASCADE)
    email_template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    
    # Processing statistics
    total_rows = models.IntegerField(null=True, blank=True)
    processed_rows = models.IntegerField(default=0)
    successful_submissions = models.IntegerField(default=0)
    failed_submissions = models.IntegerField(default=0)
    skipped_rows = models.IntegerField(default=0)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Excel Upload {self.id} - {self.law_firm.name} - {self.status}"

    def get_success_rate(self):
        if self.total_rows and self.total_rows > 0:
            return round((self.successful_submissions / self.total_rows) * 100, 2)
        return 0

    class Meta:
        verbose_name = "Excel Upload"
        verbose_name_plural = "Excel Uploads"
        ordering = ['-created_at']


class RetainerRecipient(models.Model):
    """Individual recipients from Excel file for retainer documents"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('submitted', 'Submitted to NextKeySign'),
        ('completed', 'Document Completed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped (Invalid Data)'),
    ]

    excel_upload = models.ForeignKey(ExcelUpload, on_delete=models.CASCADE, related_name='recipients')
    
    # Excel data fields
    external_id = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    state = models.CharField(max_length=50, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)
    age = models.IntegerField(null=True, blank=True)
    first_name_injured = models.CharField(max_length=100, blank=True)
    last_name_injured = models.CharField(max_length=100, blank=True)
    
    # Processing status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.email}) - {self.status}"

    @property
    def display_name_injured(self):
        """Get the injured person's display name"""
        if self.first_name_injured and self.last_name_injured:
            return f"{self.first_name_injured} {self.last_name_injured}"
        return self.name

    class Meta:
        verbose_name = "Retainer Recipient"
        verbose_name_plural = "Retainer Recipients"
        ordering = ['-created_at']


class DocumentSubmission(models.Model):
    """NextKeySign submission tracking for retainer documents"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('opened', 'Opened'),
        ('completed', 'Completed'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]

    recipient = models.OneToOneField(RetainerRecipient, on_delete=models.CASCADE, related_name='document_submission')
    document_template = models.ForeignKey(DocumentTemplate, on_delete=models.CASCADE)
    
    # NextKeySign data
    nextkeysign_submission_id = models.CharField(max_length=100, blank=True)
    nextkeysign_submitter_id = models.CharField(max_length=100, blank=True)
    nextkeysign_slug = models.CharField(max_length=100, blank=True)
    external_id = models.CharField(max_length=200)
    
    # Status and URLs
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    signed_document_url = models.URLField(max_length=500, blank=True, null=True)
    audit_log_url = models.URLField(max_length=500, blank=True, null=True)
    decline_reason = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    declined_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Document for {self.recipient.name} - {self.status}"

    @property
    def law_firm(self):
        """Get law firm through recipient's Excel upload"""
        return self.recipient.excel_upload.law_firm

    class Meta:
        verbose_name = "Document Submission"
        verbose_name_plural = "Document Submissions"
        ordering = ['-created_at']


class DocumentWebhookEvent(models.Model):
    """NextKeySign webhook events for retainer documents"""
    document_submission = models.ForeignKey(DocumentSubmission, on_delete=models.CASCADE, related_name='webhook_events')
    event_type = models.CharField(max_length=50)
    webhook_data = models.JSONField()
    processed = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} - {self.document_submission.recipient.name}"

    class Meta:
        verbose_name = "Document Webhook Event"
        verbose_name_plural = "Document Webhook Events"
        ordering = ['-created_at']
