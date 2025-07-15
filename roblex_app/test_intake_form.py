import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from roblex_app.models import IntakeForm

@pytest.mark.django_db
def test_valid_intake_form_submission():
    client = APIClient()
    url = reverse('intake-form')  
    
    payload = {
        "date": "2025-07-14",
        "gamer_first_name": "John",
        "gamer_last_name": "Doe",
        "guardian_first_name": "Jane",
        "guardian_last_name": "Doe",
        "custody_type": "married_parent",
        "question": "What is your concern?",
        "roblox_gamertag": "johnny123",
        "discord_profile": "john#1234",
        "description_predators": "Pretended to be a child.",
        "description_medical_psychological": "Therapy sessions ongoing.",
        "description_economic_loss": "Lost approx. $500",
        "first_contact": "2024-01-01",
        "last_contact": "2024-02-01",
        "complained_to_roblox": True,
        "emails_to_roblox": True,
        "complained_to_apple": False,
        "emails_to_apple": False,
        "complained_to_cc": True,
        "emails_to_cc": True,
        "cc_names": "Visa, Mastercard",
        "contacted_police": True,
        "emails_to_police": True,
        "police_details": "NYPD, Case #1234, open",
        "other_complaints": "Reported to ISP",
        "asked_for_photos": True,
        "minor_sent_photos": False,
        "predator_distributed": "Unknown",
        "predator_threatened": "No",
        "in_person_meeting": "No meeting occurred",
        "additional_info": "Everything above is true",
        "discovery_info": "Found out from child's messages"
    }

    response = client.post(url, data=payload, format='json')
    assert response.status_code == 201
    assert IntakeForm.objects.count() == 1


def test_missing_required_fields():
    client = APIClient()
    url = reverse('intake-form')
    response = client.post(url, data={}, format='json')

    assert response.status_code == 400
    errors = response.json()

    # Validate that at least one field error is returned
    assert isinstance(errors, dict)
    assert len(errors) > 0


