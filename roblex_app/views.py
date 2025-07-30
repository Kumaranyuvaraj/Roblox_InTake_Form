import json
import re
from django.http import JsonResponse
import requests
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework import status
from roblex_app.models import EmailTemplate, UserDetail, Question, Option, UserAnswer,EmailLog
from roblex_app.serializers import EmailTemplateSerializer, IntakeFormSerializer, UserDetailSerializer,QuestionSerializer, UserAnswerSerializer,EmailLogSerializer
from django.shortcuts import render,redirect

from rest_framework.decorators import api_view

import base64
from django.core.files.base import ContentFile
from django.utils import timezone
import uuid

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.uploadedfile import InMemoryUploadedFile

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
        data = request.data 

        serializer = IntakeFormSerializer(data=data)
        if serializer.is_valid():
            raw_roblox_name = serializer.validated_data.get("roblox_gamertag", "")
            usernames = [re.sub(r'^[^A-Za-z]+', '', name.strip()) for name in raw_roblox_name.split(",") if name.strip()]

            try:
                for username in usernames:
                    roblox_response = requests.post(
                        "https://users.roblox.com/v1/usernames/users",
                        json={"usernames": [username], "excludeBannedUsers": False},
                        headers={"Content-Type": "application/json"},
                        timeout=5
                    )
                    roblox_data = roblox_response.json()
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

            intake_instance = serializer.save()

            # Handle additional fields
            client_ip = data.get("client_ip")
            submitted_at = data.get("submitted_at") or timezone.now()
            pdf_data = data.get("pdf_data")

            intake_instance.client_ip = client_ip
            intake_instance.submitted_at = submitted_at

            if pdf_data:
                try:
                    format, pdfstr = pdf_data.split(';base64,')
                    file_name = f"intake_{uuid.uuid4().hex[:8]}.pdf"
                    file_content = ContentFile(base64.b64decode(pdfstr), name=file_name)
                    intake_instance.pdf_file = file_content
                except Exception as e:
                    return Response({"error": f"Failed to decode PDF: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

            intake_instance.save()


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


def get_client_ip(request):
    ip = request.META.get('HTTP_X_FORWARDED_FOR', '') or request.META.get('REMOTE_ADDR', '')
    return JsonResponse({"ip": ip})



class SendEmailAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        from_email = request.data.get("from_email")
        to_email = request.data.get("to_email")
        subject = request.data.get("subject")
        body = request.data.get("body")
        uploaded_file = request.FILES.get("attachment")

        if not all([from_email, to_email, subject, body]):
            return Response({"error": "Missing required fields."}, status=400)

        # Save initial log entry
        email_log = EmailLog.objects.create(
            from_email=from_email,
            to_email=to_email,
            subject=subject,
            body=body,
            status="pending"
        )

        try:
            # Email setup
            smtp_host = "smtp.gmail.com"
            smtp_port = 587
            smtp_user = "kumaranyuvaraj007@gmail.com"
            smtp_pass = "mbvy xtup tlmx towr"

            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            if uploaded_file:
                file_bytes = uploaded_file.read()

                # Attach to email
                part = MIMEApplication(file_bytes, Name=uploaded_file.name)
                part['Content-Disposition'] = f'attachment; filename="{uploaded_file.name}"'
                msg.attach(part)

                # Save file in database
                email_log.attachment.save(uploaded_file.name, ContentFile(file_bytes))

            # Send email
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, [to_email], msg.as_string())
            server.quit()

            email_log.status = "sent"
            email_log.save()

            return Response({"message": "Email sent successfully."}, status=200)

        except Exception as e:
            email_log.status = "failed"
            email_log.error_message = str(e)
            email_log.save()
            return Response({"error": str(e)}, status=500)


class EmailTemplateAPIView(APIView):
    def get(self, request, template_type):
        try:
            # Directly use template_type from the URL
            template = EmailTemplate.objects.filter(name=template_type).first()

            if not template:
                return Response(
                    {"error": f"Template '{template_type}' not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response({
                "subject": template.subject,
                "body": template.body
            })

        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


def email_view(request):
    return render(request, 'email.html')

def retainer_form(request):
    return render(request,'retainer_form.html')