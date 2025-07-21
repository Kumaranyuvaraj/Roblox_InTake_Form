import re
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from roblex_app.models import UserDetail, Question, Option, UserAnswer
from roblex_app.serializers import IntakeFormSerializer, UserDetailSerializer,QuestionSerializer, UserAnswerSerializer
from django.shortcuts import render,redirect

from rest_framework.decorators import api_view

# from django.http import Http404, HttpResponse
# from django.template.loader import render_to_string
# from weasyprint import HTML
# from roblex_app.models import IntakeForm

class IntakeFormView(APIView):
    """
    Handles GET to show the form, and POST to process or redirect
    """
    def get(self, request):
        return render(request, 'forms.html')

    def post(self, request):
        # After submission, redirect back to form
        return redirect('')  # assuming you have this URL name

class LandingPage(APIView):
    """
    Serves the landing page form HTML page
    """
    def get(self, request):
        return render(request, 'Home.html')
    
class IndexPage(APIView):
    """
    Serves the index page form HTML page
    """
    def get(self, request):
        return render(request, 'index.html')

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

    # if not re.fullmatch(r"[A-Za-z0-9@_]+", raw_username):
    #     return Response({
    #         "valid": False,
    #         "error": "Only letters, @ and _ are allowed. No digits or special characters."
    #     }, status=status.HTTP_400_BAD_REQUEST)

    
    username = re.sub(r'^[^A-Za-z]+', '', raw_username)


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
                "error": "Gamertag not found"
            }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class SubmitIntakeIfValidAPIView(APIView):
    def post(self, request):
        serializer = IntakeFormSerializer(data=request.data)
        if serializer.is_valid():
            raw_roblox_name = serializer.validated_data.get("roblox_gamertag")

            # Remove leading non-letter characters (@, _, digits)
            usernames = [re.sub(r'^[^A-Za-z]+', '', name.strip()) for name in raw_roblox_name.split(",") if name.strip()]
            print(usernames)

            try:
                # Validate each username using the Roblox API
                for username in usernames:
                    roblox_response = requests.post(
                        "https://users.roblox.com/v1/usernames/users",
                        json={"usernames": [username], "excludeBannedUsers": False},
                        headers={"Content-Type": "application/json"},
                        timeout=5
                    )
                    roblox_data = roblox_response.json()

                    # If Roblox returns no data for username, it's invalid
                    if "data" not in roblox_data or not roblox_data["data"]:
                        return Response(
                            {"error": f"Invalid Roblox username: {username}. Cannot save."},
                            status=status.HTTP_400_BAD_REQUEST
                        )

            except Exception as e:
                return Response(
                    {"error": f"Roblox validation failed: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Save the intake form only if all usernames are valid
            intake_instance = serializer.save()
            return Response({
                "message": "Form submitted successfully.",
                "data": IntakeFormSerializer(intake_instance).data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class UserDetailCreateView(APIView):
    def post(self, request):
        serializer = UserDetailSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class QuestionListAPIView(APIView):
    def get(self, request):
        questions = Question.objects.prefetch_related('options').all()
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# Submit answer to a question
class SubmitAnswerAPIView(APIView):
    def post(self, request):
        serializer = UserAnswerSerializer(data=request.data)
        if serializer.is_valid():
            # prevent duplicate entries
            user = serializer.validated_data['user']
            question = serializer.validated_data['question']

            UserAnswer.objects.update_or_create(
                user=user, question=question,
                defaults={'selected_option': serializer.validated_data['selected_option']}
            )

            return Response({"message": "Answer submitted."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
