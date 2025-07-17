import re
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from roblex_app.serializers import IntakeFormSerializer
from django.shortcuts import render

from rest_framework.decorators import api_view

# from django.http import Http404, HttpResponse
# from django.template.loader import render_to_string
# from weasyprint import HTML
# from roblex_app.models import IntakeForm

class IntakeFormView(APIView):
    """
    Serves the intake form HTML page
    """
    def get(self, request):
        return render(request, 'forms.html')

class IntakeFormAPIView(APIView):
    def post(self, request):
        serializer = IntakeFormSerializer(data=request.data)
        response =push_to_smart_advocate(data=request.data)

        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class IntakeFormPDFView(APIView):
#     def get(self, request, pk):
#         try:
#             intake = IntakeForm.objects.get(pk=pk)
#         except IntakeForm.DoesNotExist:
#             raise Http404("Intake form not found.")

#         html_string = render_to_string('pdf_template.html', {'data': intake})
#         pdf = HTML(string=html_string).write_pdf()

#         response = HttpResponse(pdf, content_type='application/pdf')
#         response['Content-Disposition'] = f'attachment; filename="intake_form_{pk}.pdf"'
#         return response

def push_to_smart_advocate(data):
    SMARTADVOCATE_URL = "https://api.smartadvocate.com/saservice/sawebservice.svc/Receiver/OfficeCalls/a199ce2be8374f129d4bdd34adc6c3ce"

    mapped_data = {
        "firstName": data.get("guardian_first_name"),
        "lastName": data.get("guardian_last_name"),
        "injuredFirstName": data.get("gamer_first_name"),
        "injuredLastName": data.get("gamer_last_name"),
        "retainDate": data.get("first_contact"),
        "caseDetails": data.get("description_predators"),
        "cljExposureDetails": data.get("question"),
        "cljDiagnosisAdditionalDetails": data.get("description_medical_psychological"),
        "cljExposureAdditionalDetails": data.get("additional_info"),
        "cljMilitaryService": "no",
        "cljAdministrativeClaimVa": "no",
        "cljAdministrativeClaimNavy": "no"
    }

    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(SMARTADVOCATE_URL, json=mapped_data, headers=headers)
        print("response:",response.json())

        return Response({
            "message": "Successfully forwarded to SmartAdvocate",
            "status_code": response.status_code,
            "response": response.text
        }, status=status.HTTP_200_OK)
    except requests.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
    

@api_view(['POST'])
def validate_roblox_username(request):
    raw_username = request.data.get("username")

    if not raw_username:
        return Response({"error": "Username is required"}, status=status.HTTP_400_BAD_REQUEST)

    if not re.fullmatch(r"[A-Za-z@_]+", raw_username):
        return Response({
            "valid": False,
            "error": "Only letters, @ and _ are allowed. No digits or special characters."
        }, status=status.HTTP_400_BAD_REQUEST)

    # ✅ Remove @ and _ before API call
    username = re.sub(r'[@_]', '', raw_username)

    try:
        roblox_response = requests.post(
            "https://users.roblox.com/v1/usernames/users",
            json={"usernames": [username], "excludeBannedUsers": False},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        roblox_data = roblox_response.json()

        if roblox_data.get("data"):
            return Response({
                "valid": True,
                "displayName": roblox_data["data"][0]["displayName"],
                "robloxId": roblox_data["data"][0]["id"]
            })
        else:
            return Response({
                "valid": False,
                "error": "Username not found"
            }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class SubmitIntakeIfValidAPIView(APIView):
    def post(self, request):
        serializer = IntakeFormSerializer(data=request.data)
        if serializer.is_valid():
            raw_roblox_name = serializer.validated_data.get("roblox_gamertag")

            # Validate format: only letters, @ and _
            if not re.fullmatch(r"[A-Za-z@_]+", raw_roblox_name):
                return Response(
                    {"error": "Only letters, @ and _ are allowed. No digits or special characters."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Remove @ and _ before sending to Roblox API
            cleaned_name = re.sub(r'[@_]', '', raw_roblox_name)

            # Validate against Roblox API
            try:
                roblox_response = requests.post(
                    "https://users.roblox.com/v1/usernames/users",
                    json={"usernames": [cleaned_name], "excludeBannedUsers": False},
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                roblox_data = roblox_response.json()

                if not roblox_data.get("data"):
                    return Response(
                        {"error": "Invalid Roblox username. Cannot save."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Exception as e:
                return Response(
                    {"error": f"Roblox validation failed: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            #  Save to DB only if valid
            intake_instance = serializer.save()
            return Response({
                "message": "Form submitted successfully.",
                "data": IntakeFormSerializer(intake_instance).data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

