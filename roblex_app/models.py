from django.db import models

from django.contrib.postgres.fields import ArrayField


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

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    cell_phone = models.CharField(max_length=20)
    email = models.EmailField()
    zipcode = models.CharField(max_length=10)
    working_with_attorney = models.CharField(max_length=3, choices=ATTORNEY_CHOICES)
    additional_notes = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    


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
    TEMPLATE_TYPES = [
        ('rejected', 'Rejected (>20 years)'),
        ('eligible_no_parent', 'Eligible (18-20, no parent signature)'),
        ('eligible_with_parent', 'Eligible (<=17, parent signature required)')
    ]

    name = models.CharField(max_length=50, choices=TEMPLATE_TYPES, unique=True)
    subject = models.CharField(max_length=255)
    body = models.TextField()

    def __str__(self):
        return self.get_name_display()


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
    """Maps legal document types to DocuSeal template IDs"""
    TEMPLATE_TYPES = [
        ('retainer_minor', 'Retainer Agreement - Minor (with parent signature)'),
        ('retainer_adult', 'Retainer Agreement - Adult (18-20)'),
        ('intake_supplemental', 'Supplemental Intake Document'),
    ]
    
    name = models.CharField(max_length=50, choices=TEMPLATE_TYPES, unique=True)
    docuseal_template_id = models.IntegerField()  # Template ID from DocuSeal
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.get_name_display()


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
    
    # DocuSeal integration fields
    docuseal_submission_id = models.IntegerField(unique=True)
    docuseal_submitter_id = models.IntegerField()
    docuseal_slug = models.CharField(max_length=100)  # Unique signing URL slug
    
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


class DocumentWebhookEvent(models.Model):
    """Logs all webhook events from DocuSeal"""
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


    