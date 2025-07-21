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

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    


class Question(models.Model):
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text

class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.question.text} - {self.text}"

class UserAnswer(models.Model):
    user = models.ForeignKey(UserDetail, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'question')  # prevent duplicate answers

    