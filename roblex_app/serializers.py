from rest_framework import serializers
from roblex_app.models import IntakeForm,UserDetail,Question, Option, UserAnswer

class IntakeFormSerializer(serializers.ModelSerializer):
    # Required text fields
    gamer_first_name = serializers.CharField(required=True)
    gamer_last_name = serializers.CharField(required=True)
    guardian_first_name = serializers.CharField(required=True)
    guardian_last_name = serializers.CharField(required=True)
    # question = serializers.CharField(required=True)
    description_predators = serializers.CharField(required=True)
    description_medical_psychological = serializers.CharField(required=True)
    description_economic_loss = serializers.CharField(required=True)
    cc_names = serializers.CharField(required=True)
    police_details = serializers.CharField(required=True)
    other_complaints = serializers.CharField(required=True)
    in_person_meeting = serializers.CharField(required=True)
    additional_info = serializers.CharField(required=True)
    discovery_info = serializers.CharField(required=True)
    custody_other_detail = serializers.CharField(required=False, allow_blank=True)

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
        if data.get("first_contact") and data.get("last_contact"):
            if data["first_contact"] > data["last_contact"]:
                raise serializers.ValidationError("First contact date cannot be after last contact date.")
        
        # Require at least one gamertag
        if not any([
            data.get("roblox_gamertag"),
            data.get("discord_profile"),
            data.get("xbox_gamertag"),
            data.get("ps_gamertag")
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
        fields = ['id', 'text']

class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'options']

class UserAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnswer
        fields = ['user', 'question', 'selected_option']
