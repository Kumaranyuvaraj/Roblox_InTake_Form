from rest_framework import serializers
from roblex_app.models import EmailLog, EmailTemplate, IntakeForm,UserDetail,Question, Option, UserAnswer, DocumentTemplate, DocumentSubmission, DocumentWebhookEvent

class IntakeFormSerializer(serializers.ModelSerializer):
    # Required text fields
    gamer_first_name = serializers.CharField(required=True)
    gamer_last_name = serializers.CharField(required=True)
    guardian_first_name = serializers.CharField(required=True)
    guardian_last_name = serializers.CharField(required=True)
    # question = serializers.CharField(required=True)
    description_predators = serializers.CharField(required=False, allow_blank=True)
    description_medical_psychological = serializers.CharField(required=False,allow_blank=True)
    description_economic_loss = serializers.CharField(required=False,allow_blank=True)
    cc_names = serializers.CharField(required=True)
    police_details = serializers.CharField(required=True)
    other_complaints = serializers.CharField(required=True)
    in_person_meeting = serializers.CharField(required=True)
    additional_info = serializers.CharField(required=True)
    discovery_info = serializers.CharField(required=False, allow_blank=True)
    custody_other_detail = serializers.CharField(required=False, allow_blank=True)

    first_contact = serializers.DateField(input_formats=["%m-%d-%Y"])
    last_contact = serializers.DateField(input_formats=["%m-%d-%Y"])

    # Multiple checkbox (array) fields
    custody_type = serializers.ListField(child=serializers.CharField(), required=False)
    complained_to_roblox = serializers.ListField(child=serializers.CharField(), required=False)
    emails_to_roblox = serializers.ListField(child=serializers.CharField(), required=False)
    complained_to_apple = serializers.ListField(child=serializers.CharField(), required=False)
    emails_to_apple = serializers.ListField(child=serializers.CharField(), required=False)
    complained_to_cc = serializers.ListField(child=serializers.CharField(), required=False)
    emails_to_cc = serializers.ListField(child=serializers.CharField(), required=False)
    contacted_police = serializers.ListField(child=serializers.CharField(), required=False)
    emails_to_police = serializers.ListField(child=serializers.CharField(), required=False)
    asked_for_photos = serializers.ListField(child=serializers.CharField(), required=False)
    minor_sent_photos = serializers.ListField(child=serializers.CharField(), required=False)
    predator_distributed = serializers.ListField(child=serializers.CharField(), required=False)
    predator_threatened = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = IntakeForm
        fields = '__all__'

    def validate(self, data):
    # Validate contact dates
        first_contact = data.get("first_contact")
        last_contact = data.get("last_contact")
        if first_contact and last_contact:
            if first_contact > last_contact:
                raise serializers.ValidationError("First contact date cannot be after last contact date.")
            
        

    # Require at least one gamertag
        if not any([
            data.get("roblox_gamertag"),
            data.get("discord_profile"),
            data.get("xbox_gamertag"),
            data.get("ps_gamertag"),
            data.get("description_predators"),
            data.get("description_medical_psychological"),
            data.get("description_economic_loss"),
            data.get("discovery_info")
        ]):
            raise serializers.ValidationError("At least one gamertag or profile must be provided.")

        return data



class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDetail
        fields = '__all__'
        extra_kwargs = {
            'additional_notes': {'required': False},
        }



class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ['id', 'text', 'is_eligible', 'requires_parental_signature', 'redirect_to_retainer']

class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True)
    
    class Meta:
        model = Question
        fields = ['id', 'text', 'options']


class UserAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnswer
        fields = ['user', 'question', 'selected_option']



class EmailLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailLog
        fields = '__all__'

class EmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplate
        fields = ['name', 'subject', 'body']


# class EligibilityResultSerializer(serializers.Serializer):
#     age = serializers.IntegerField()
#     is_eligible = serializers.BooleanField()
#     requires_parental_signature = serializers.BooleanField()
#     redirect_to_retainer = serializers.BooleanField()
#     template_type = serializers.CharField()

class DocumentTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentTemplate
        fields = ['id', 'name', 'docuseal_template_id', 'description', 'is_active']


class DocumentSubmissionSerializer(serializers.ModelSerializer):
    user_detail = UserDetailSerializer(read_only=True)
    document_template = DocumentTemplateSerializer(read_only=True)
    
    class Meta:
        model = DocumentSubmission
        fields = ['id', 'user_detail', 'document_template', 'docuseal_submission_id', 
                 'docuseal_submitter_id', 'docuseal_slug', 'status', 'sent_at', 'opened_at', 
                 'completed_at', 'declined_at', 'signed_document_url', 'audit_log_url', 
                 'decline_reason', 'external_id', 'created_at', 'updated_at']


class DocumentWebhookEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentWebhookEvent
        fields = ['id', 'event_type', 'document_submission', 'webhook_data', 'processed', 'created_at']
