from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone


class LawFirm(models.Model):
    """
    Model to represent different law firms using the system
    Each law firm gets their own subdomain and isolated data
    """
    name = models.CharField(max_length=200, help_text="Full name of the law firm")
    subdomain = models.CharField(
        max_length=100, 
        unique=True, 
        help_text="Subdomain identifier (e.g., 'hilliard' for hilliard.nextkeylitigation.com)"
    )
    contact_email = models.EmailField(help_text="Primary contact email for the law firm")
    phone_number = models.CharField(max_length=20, blank=True, help_text="Contact phone number")
    address = models.TextField(blank=True, help_text="Law firm address")
    is_active = models.BooleanField(default=True, help_text="Whether this law firm is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Law Firm"
        verbose_name_plural = "Law Firms"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.subdomain})"

    @property
    def full_domain(self):
        """Return the full subdomain URL"""
        return f"{self.subdomain}.nextkeylitigation.com"

    def get_leads_count(self):
        """Return count of leads for this law firm"""
        return self.leads.count()

    def get_active_leads_count(self):
        """Return count of leads that have submitted intake forms"""
        return self.leads.filter(intake_forms__isnull=False).distinct().count()


class LawFirmUser(models.Model):
    """
    Model to associate Django users with law firms and define their roles
    Enables multi-tenant access control
    """
    ROLE_CHOICES = [
        ('super_admin', 'Super Administrator'),
        ('law_firm_admin', 'Law Firm Administrator'),
        ('law_firm_staff', 'Law Firm Staff'),
        ('law_firm_viewer', 'Read Only Access'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='law_firm_profile')
    law_firm = models.ForeignKey(
        LawFirm, 
        on_delete=models.CASCADE, 
        related_name='users',
        null=True,
        blank=True,
        help_text="Leave blank for super administrators"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='law_firm_staff')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Law Firm User"
        verbose_name_plural = "Law Firm Users"

    def __str__(self):
        law_firm_name = self.law_firm.name if self.law_firm else "Super Admin"
        return f"{self.user.get_full_name() or self.user.username} - {law_firm_name}"

    def can_manage_users(self):
        """Check if user can manage other users in their law firm"""
        return self.role in ['super_admin', 'law_firm_admin']

    def can_edit_data(self):
        """Check if user can edit data"""
        return self.role in ['super_admin', 'law_firm_admin', 'law_firm_staff']

    def is_super_admin(self):
        """Check if user is a super administrator"""
        return self.role == 'super_admin'


class IntakeForm(models.Model):

    CUSTODY_CHOICES = [
        ('married_parent', 'Biological parent, married'),
        ('divorced_parent', 'Biological parent, divorced with custody order'),
        ('adoptive_parent', 'Adoptive parent(s)'),
        ('legal_guardian', 'Legal Guardian with custody order'),
        ('no_custody', 'Do not have legal custody'),
        ('other', 'Other'),
    ]

    MUL_CHOICE = [
        
            ('Yes','Yes'),
            ('No','No')
        
    ]

    MUL_UNKNOWN_CHOICE = [
        
            ('Yes','Yes'),
            ('No','No'),
            ('Unknown','Unknown')
             
        
    ]



    # Link to prequalified user
    user_detail = models.ForeignKey('UserDetail', on_delete=models.CASCADE, related_name='intake_forms', null=True, blank=True)
    
    # Law firm association (auto-populated from user_detail.law_firm for easier querying)
    law_firm = models.ForeignKey(
        LawFirm, 
        on_delete=models.CASCADE, 
        related_name='intake_forms',
        null=True,
        blank=True,
        help_text="Auto-populated from user_detail.law_firm"
    )
    
    date = models.DateField(null=True, blank=True)
    gamer_first_name = models.CharField(max_length=100,null=True,blank=False)
    gamer_last_name = models.CharField(max_length=100,null=True,blank=False)
    guardian_first_name = models.CharField(max_length=100,null=True,blank=False)
    guardian_last_name = models.CharField(max_length=100,null=True,blank=False)
    custody_type = ArrayField(
        models.CharField(max_length=30, choices=CUSTODY_CHOICES),
        verbose_name="Do you have legal custody of the gamer (if gamer is a minor)",
        default=list,
        blank=True
    )
    custody_other_detail = models.CharField(max_length=200, blank=True, null=True)
    question = models.TextField(max_length=200,null=True,blank=False)


    roblox_gamertag = models.CharField(max_length=100,null=True, blank=True)
    discord_profile = models.CharField(max_length=100,null=True, blank=True)
    xbox_gamertag = models.CharField(max_length=100,null=True, blank=True)
    ps_gamertag = models.CharField(max_length=100,null=True, blank=True)
   
    description_predators = models.TextField(max_length=200,null=True,blank=False)
    description_medical_psychological = models.TextField(max_length=200,null=True,blank=False)
    description_economic_loss = models.TextField(max_length=200,null=True,blank=False)

    first_contact = models.DateField(null=True, blank=True)
    last_contact = models.DateField(null=True, blank=True)
    complained_to_roblox = ArrayField(
        models.CharField(max_length=30, choices=MUL_CHOICE),
        default=list,
        blank=True
    )
    emails_to_roblox = ArrayField(
        models.CharField(max_length=30, choices=MUL_CHOICE),
        default=list,
        blank=True
    )
    complained_to_apple = ArrayField(
        models.CharField(max_length=30, choices=MUL_CHOICE),
        default=list,
        blank=True
    )
    emails_to_apple = ArrayField(
        models.CharField(max_length=30, choices=MUL_CHOICE),
        default=list,
        blank=True
    )
    complained_to_cc = ArrayField(
        models.CharField(max_length=30, choices=MUL_CHOICE),
        default=list,
        blank=True
    )
    emails_to_cc = ArrayField(
        models.CharField(max_length=30, choices=MUL_CHOICE),
        default=list,
        blank=True
    )
    cc_names = models.TextField(max_length=200,null=True,blank=False)
    contacted_police = ArrayField(
        models.CharField(max_length=30, choices=MUL_CHOICE),
        default=list,
        blank=True
    )
    emails_to_police = ArrayField(
        models.CharField(max_length=30, choices=MUL_CHOICE),
        default=list,
        blank=True
    )
    police_details = models.TextField(max_length=200,null=True,blank=False)
    other_complaints = models.TextField(max_length=200,null=True,blank=False)
    asked_for_photos = ArrayField(
        models.CharField(max_length=30, choices=MUL_CHOICE),
        default=list,
        blank=True
    )
    minor_sent_photos = ArrayField(
        models.CharField(max_length=30, choices=MUL_CHOICE),
        default=list,
        blank=True
    )
    predator_distributed = ArrayField(
        models.CharField(max_length=30, choices=MUL_UNKNOWN_CHOICE),
        default=list,
        blank=True
    )
    predator_threatened = ArrayField(
        models.CharField(max_length=30, choices=MUL_UNKNOWN_CHOICE),
        default=list,
        blank=True
    )
    in_person_meeting = models.TextField(max_length=200,null=True,blank=False)
    additional_info = models.TextField(max_length=200,null=True,blank=False)
    discovery_info = models.TextField(max_length=200,null=True,blank=False)

    client_ip = models.GenericIPAddressField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    pdf_file = models.FileField(upload_to='pdfs/', null=True, blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)
    

    class Meta:
        db_table = "intake_form"



class UserDetail(models.Model):
    ATTORNEY_CHOICES = (
        ('yes', 'Yes'),
        ('no', 'No'),
    )

    AGREEMENT_CHOICES = (
    ('agree', 'I Agree'),
    ('not_agree', 'I Do Not Agree'),
    )

    # Law firm association - automatically set based on subdomain
    law_firm = models.ForeignKey(
        LawFirm, 
        on_delete=models.CASCADE, 
        related_name='leads',
        null=True,
        blank=True,
        help_text="Law firm this lead belongs to (auto-assigned based on subdomain)"
    )
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    cell_phone = models.CharField(max_length=20)
    email = models.EmailField()
    zipcode = models.CharField(max_length=10)
    # working_with_attorney = models.CharField(max_length=3, choices=ATTORNEY_CHOICES)

    additional_notes = models.CharField(max_length=100, blank=True, null=True)
    # gamer_dob = models.DateField(null=True, blank=True)

    agreement_status = models.CharField(
    max_length=20, 
    choices=AGREEMENT_CHOICES,
    null=True,
    blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lead"
        verbose_name_plural = "Leads"
        ordering = ['-created_at']

    def __str__(self):
        law_firm_name = self.law_firm.name if self.law_firm else "Unassigned"
        return f"{self.first_name} {self.last_name} ({law_firm_name})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_age(self):
        """Calculate age from gamer_dob"""
        if self.gamer_dob:
            from datetime import date
            today = date.today()
            return today.year - self.gamer_dob.year - ((today.month, today.day) < (self.gamer_dob.month, self.gamer_dob.day))
        return None
    
# class AgeEligibilityRule(models.Model):
#     min_age = models.PositiveSmallIntegerField(null=True, blank=True)  # inclusive
#     max_age = models.PositiveSmallIntegerField(null=True, blank=True)  # inclusive; null means no upper bound
#     is_eligible = models.BooleanField(default=False)
#     requires_parental_signature = models.BooleanField(default=False)
#     redirect_to_retainer = models.BooleanField(default=False)

#     class Meta:
#         ordering = ['min_age']  

#     def matches(self, age: int) -> bool:
#         if self.min_age is not None and age < self.min_age:
#             return False
#         if self.max_age is not None and age > self.max_age:
#             return False
#         return True

#     def __str__(self):
#         upper = f"{self.max_age}" if self.max_age is not None else "+"
#         return f"{self.min_age or 0}-{upper}: eligible={self.is_eligible}, parental={self.requires_parental_signature}"

    


class Question(models.Model):
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text

class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)

    is_eligible = models.BooleanField(default=False)
    requires_parental_signature = models.BooleanField(default=False)
    redirect_to_retainer = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.question.text} - {self.text}"

class UserAnswer(models.Model):
    user = models.ForeignKey(UserDetail, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'question')

class EmailTemplate(models.Model):
    """Dynamic email template model for various email types"""
    
    # Template type for categorization (flexible, no fixed choices)
    template_type = models.CharField(
        max_length=50,
        help_text="Template type (e.g., rejection, followup, notification, etc.)"
    )
    
    # Template name (unique identifier)
    name = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Unique template name (e.g., 'landing_page_parents_followup', 'intake_rejection')"
    )
    
    # Email content
    subject = models.CharField(max_length=255)
    body = models.TextField(
        help_text="Supported placeholders: [NAME], [EMAIL], [PHONE], [STATE], [USER FIRST NAME], etc."
    )
    
    # Template status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Email Template"
        verbose_name_plural = "Email Templates"
        ordering = ['template_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.template_type})"


class EmailLog(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    from_email = models.EmailField()
    to_email = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to='attachments/', blank=True, null=True)
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class DocumentTemplate(models.Model):
    """Maps legal document types to NextKeySign template IDs"""
    TEMPLATE_TYPES = [
        ('retainer_minor', 'Retainer Agreement - Minor (with parent signature)'),
        ('retainer_adult', 'Retainer Agreement - Adult (18-20)'),
        ('intake_supplemental', 'Supplemental Intake Document'),
        ('florida_disclosure', 'Florida Disclosure Document (Zipcode 32003-34997)'),
    ]
    
    name = models.CharField(max_length=50, choices=TEMPLATE_TYPES)
    # Law firm association - null means global template, specific value means law firm override
    law_firm = models.ForeignKey(
        LawFirm, 
        on_delete=models.CASCADE, 
        related_name='document_templates',
        null=True,
        blank=True,
        help_text="Leave blank for global templates, set for law firm-specific overrides"
    )
    nextkeysign_template_id = models.IntegerField()  # Template ID from NextKeySign
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensure each law firm can have only one template per type
        unique_together = [['name', 'law_firm']]

    def __str__(self):
        law_firm_name = f" ({self.law_firm.name})" if self.law_firm else " (Global)"
        return f"{self.get_name_display()}{law_firm_name}"
    
    @classmethod
    def get_template_for_law_firm(cls, template_type, law_firm=None):
        """
        Get the appropriate template for a law firm with fallback to global
        Args:
            template_type: One of the TEMPLATE_TYPES choices
            law_firm: LawFirm instance or None
        Returns:
            DocumentTemplate instance or None
        """
        # First try to get law firm-specific template
        if law_firm:
            template = cls.objects.filter(
                name=template_type, 
                law_firm=law_firm, 
                is_active=True
            ).first()
            if template:
                return template
        
        # Fallback to global template
        return cls.objects.filter(
            name=template_type, 
            law_firm__isnull=True, 
            is_active=True
        ).first()


class DocumentSubmission(models.Model):
    """Tracks document signing submissions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent to Signer'),
        ('opened', 'Opened by Signer'),
        ('completed', 'Completed'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
        ('archived', 'Archived'),
    ]
    
    user_detail = models.ForeignKey(UserDetail, on_delete=models.CASCADE, related_name='document_submissions')
    intake_form = models.ForeignKey(IntakeForm, on_delete=models.CASCADE, null=True, blank=True)
    document_template = models.ForeignKey(DocumentTemplate, on_delete=models.CASCADE)
    
    # NextKeySign integration fields
    nextkeysign_submission_id = models.IntegerField(unique=True)
    nextkeysign_submitter_id = models.IntegerField()
    nextkeysign_slug = models.CharField(max_length=100)  # Unique signing URL slug
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    declined_at = models.DateTimeField(null=True, blank=True)
    
    # Document URLs (populated after completion)
    signed_document_url = models.URLField(max_length=500, blank=True, null=True)
    audit_log_url = models.URLField(max_length=500, blank=True, null=True)
    
    # Metadata
    decline_reason = models.TextField(blank=True, null=True)
    external_id = models.CharField(max_length=100, unique=True)  # Your app's unique ID
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user_detail} - {self.document_template.name} ({self.status})"
    
    @property
    def law_firm(self):
        """Get law firm from user_detail"""
        return self.user_detail.law_firm if self.user_detail else None


class DocumentWebhookEvent(models.Model):
    """Logs all webhook events from NextKeySign"""
    EVENT_TYPES = [
        ('form.viewed', 'Form Viewed'),
        ('form.started', 'Form Started'),
        ('form.completed', 'Form Completed'),
        ('form.declined', 'Form Declined'),
        ('submission.created', 'Submission Created'),
        ('submission.completed', 'Submission Completed'),
        ('submission.expired', 'Submission Expired'),
    ]
    
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    document_submission = models.ForeignKey(DocumentSubmission, on_delete=models.CASCADE, related_name='webhook_events')
    webhook_data = models.JSONField()  # Store full webhook payload
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} - {self.document_submission}"


class LandingPageLead(models.Model):
    """
    Model to store leads from landing page forms (ParentsPage and KidsPage)
    """
    LEAD_SOURCE_CHOICES = [
        ('parents', 'Parents Page'),
        ('kids', 'Kids Page'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'New Lead'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('converted', 'Converted to Intake'),
        ('declined', 'Declined'),
        ('inactive', 'Inactive'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=200, help_text="Full name of the person submitting the form")
    email = models.EmailField(help_text="Contact email address")
    phone = models.CharField(max_length=20, blank=True, help_text="Phone number (only for Parents Page)")
    state_location = models.CharField(max_length=100, blank=True, help_text="State/Location (only for Parents Page)")
    description = models.TextField(blank=True, help_text="Description of concern or issue (optional)")
    
    # Lead Tracking
    lead_source = models.CharField(
        max_length=10, 
        choices=LEAD_SOURCE_CHOICES, 
        help_text="Which landing page the lead came from"
    )
    status = models.CharField(
        max_length=15, 
        choices=STATUS_CHOICES, 
        default='new',
        help_text="Current status of this lead"
    )
    
    # Law Firm Association (based on subdomain where form was submitted)
    law_firm = models.ForeignKey(
        LawFirm, 
        on_delete=models.CASCADE, 
        related_name='landing_page_leads',
        null=True,
        blank=True,
        help_text="Law firm this lead belongs to (auto-assigned based on subdomain)"
    )
    
    # Technical Information
    client_ip = models.GenericIPAddressField(null=True, blank=True, help_text="IP address of the submitter")
    user_agent = models.TextField(blank=True, help_text="Browser user agent string")
    referrer = models.URLField(max_length=500, blank=True, help_text="Referring page URL")
    
    # Follow-up Information
    contacted_at = models.DateTimeField(null=True, blank=True, help_text="When the lead was first contacted")
    notes = models.TextField(blank=True, help_text="Internal notes about this lead")
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_leads',
        help_text="Staff member assigned to follow up with this lead"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Landing Page Lead"
        verbose_name_plural = "Landing Page Leads"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['law_firm', 'status']),
            models.Index(fields=['lead_source', 'created_at']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        law_firm_name = self.law_firm.name if self.law_firm else "Unassigned"
        return f"{self.name} ({self.get_lead_source_display()}) - {law_firm_name}"
    
    @property
    def is_parents_page_lead(self):
        """Check if this lead came from the Parents Page (has phone and state)"""
        return self.lead_source == 'parents'
    
    @property
    def is_kids_page_lead(self):
        """Check if this lead came from the Kids Page"""
        return self.lead_source == 'kids'
    
    def mark_contacted(self, user=None):
        """Mark this lead as contacted"""
        self.status = 'contacted'
        self.contacted_at = timezone.now()
        if user:
            self.assigned_to = user
        self.save()
    
    def convert_to_intake(self):
        """Convert this lead to a UserDetail for the intake process"""
        # Split name into first and last name
        name_parts = self.name.strip().split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Create UserDetail from this lead
        user_detail = UserDetail.objects.create(
            law_firm=self.law_firm,
            first_name=first_name,
            last_name=last_name,
            email=self.email,
            cell_phone=self.phone or '',  # Kids page might not have phone
            zipcode='',  # Will be filled in intake form
            working_with_attorney='no',  # Default value
            additional_notes=f"Converted from landing page lead. Original description: {self.description}"
        )
        
        # Update lead status
        self.status = 'converted'
        self.save()
        
        return user_detail


class LandingPageLeadEmail(models.Model):
    """
    Track email notifications sent for landing page leads
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    lead = models.ForeignKey(LandingPageLead, on_delete=models.CASCADE, related_name='email_notifications')
    email_type = models.CharField(max_length=50, help_text="Type of email (e.g., 'new_lead_notification', 'auto_reply')")
    recipient_email = models.EmailField(help_text="Email address where notification was sent")
    subject = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Landing Page Lead Email"
        verbose_name_plural = "Landing Page Lead Emails"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email_type} to {self.recipient_email} for {self.lead.name}"


    