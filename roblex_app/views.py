from datetime import date
import json
import re
import traceback
from django.http import JsonResponse
import requests
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework import status
from roblex_app.models import EmailTemplate, UserDetail, Question, Option, UserAnswer,EmailLog
from roblex_app.serializers import EmailTemplateSerializer, IntakeFormSerializer, UserDetailSerializer,QuestionSerializer, UserAnswerSerializer
from django.conf import settings
from roblex_app.models import EmailTemplate, UserDetail, Question, Option, UserAnswer,EmailLog, DocumentTemplate, DocumentSubmission, DocumentWebhookEvent
from roblex_app.serializers import EmailTemplateSerializer, IntakeFormSerializer, UserDetailSerializer,QuestionSerializer, UserAnswerSerializer,EmailLogSerializer, DocumentTemplateSerializer, DocumentSubmissionSerializer, DocumentWebhookEventSerializer
from django.shortcuts import render,redirect

from rest_framework.decorators import api_view

import base64
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.dateparse import parse_datetime
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

# class EligibilityAPIView(APIView):
#     def post(self, request):
#         dob_str = request.data.get("dob")  # expect "YYYY-MM-DD"
#         if not dob_str:
#             return Response({"error": "Date of birth is required."}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             dob = date.fromisoformat(dob_str)
#         except ValueError:
#             return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

#         today = date.today()
#         age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

#         # Find the first matching rule (you can order by priority if needed)
#         rule = None
#         for r in AgeEligibilityRule.objects.all():
#             if r.matches(age):
#                 rule = r
#                 break

#         if not rule:
#             return Response({"error": "No matching eligibility rule."}, status=status.HTTP_404_NOT_FOUND)

#         if not rule.is_eligible:
#             template_type = "rejected"
#         elif rule.requires_parental_signature:
#             template_type = "eligible_with_parent"
#         else:
#             template_type = "eligible_no_parent"

#         payload = {
#             "age": age,
#             "is_eligible": rule.is_eligible,
#             "requires_parental_signature": rule.requires_parental_signature,
#             "redirect_to_retainer": rule.redirect_to_retainer,
#             "template_type": template_type,
#         }
#         serializer = EligibilityResultSerializer(payload)
#         return Response(serializer.data, status=status.HTTP_200_OK)
    

def thanks(request):
    return render(request, 'thankyou.html')

# ====================
# DocuSeal API Views
# ====================

class CreateDocumentSubmissionAPIView(APIView):

    
    def post(self, request):
        try:
            # Extract required parameters
            user_detail_id = request.data.get('user_detail_id')
            template_type = request.data.get('template_type', 'retainer_agreement')
            email_template_type = request.data.get('email_template_type', 'eligible_no_parent')  # Default for eligible users
            
            if not user_detail_id:
                return Response(
                    {"error": "user_detail_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get user details
            try:
                user_detail = UserDetail.objects.get(id=user_detail_id)
            except UserDetail.DoesNotExist:
                return Response(
                    {"error": "User detail not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get document template
            try:
                doc_template = DocumentTemplate.objects.get(name=template_type)
            except DocumentTemplate.DoesNotExist:
                return Response(
                    {"error": f"Document template '{template_type}' not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get email template for custom message
            email_template = None
            try:
                email_template = EmailTemplate.objects.get(name=email_template_type)
            except EmailTemplate.DoesNotExist:
                print(f"Warning: Email template '{email_template_type}' not found, will use default DocuSeal message")
            
            # Prepare DocuSeal API request
            docuseal_url = f"{settings.NEXTKEYSIGN_BASE_URL}/api/submissions"
            
            # Build submitter data
            submitter_data = {
                "template_id": doc_template.docuseal_template_id,
                "submitters": [
                    {
                        "name": f"{user_detail.first_name} {user_detail.last_name}",
                        "email": user_detail.email,
                        "values": {
                            "Name": f"{user_detail.first_name} {user_detail.last_name}",
                            "Current Date": timezone.now().strftime("%Y-%m-%d")
                        },
                        "role": "First Party"
                    }
                ],
                "send_email": True,
                "completed_redirect_url": f"{request.build_absolute_uri('/')}?signed=success",
                "declined_redirect_url": f"{request.build_absolute_uri('/')}?signed=declined"
            }
            
            # Add custom message if email template exists
            if email_template:
                # Replace placeholder in email body with user's first name
                custom_body = email_template.body.replace('[User First Name]', user_detail.first_name)
                
                submitter_data["message"] = {
                    "subject": email_template.subject,
                    "body": custom_body
                }
                
                print(f"Using custom email message: Subject='{email_template.subject}' for user {user_detail.email}")
            else:
                print(f"No email template found, using default DocuSeal message for user {user_detail.email}")
            
            # Make API call to DocuSeal
            headers = {
                "X-Auth-Token": settings.NEXTKEYSIGN_API_TOKEN,
                "Content-Type": "application/json"
            }


            response = requests.post(docuseal_url, json=submitter_data, headers=headers)
            
            if response.status_code in [200, 201]:
                docuseal_response = response.json()
                
                # DocuSeal API returns an array of submitters directly
                if isinstance(docuseal_response, list) and len(docuseal_response) > 0:
                    first_submitter = docuseal_response[0]
                else:
                    print(f"DocuSeal API response validation failed: Expected array with submitters")
                    print(f"Full response: {docuseal_response}")
                    
                    return Response(
                        {"error": "Document service returned invalid response format"},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE
                    )
                
                # Validate required DocuSeal data from submitter object
                submission_id = first_submitter.get('submission_id')
                submitter_id = first_submitter.get('id')
                submitter_slug = first_submitter.get('slug', '')
                
                if not submission_id or not submitter_id:
                    error_msg = f"Invalid DocuSeal response - missing required data: submission_id={submission_id}, submitter_id={submitter_id}"
                    print(f"DocuSeal API response validation failed: {error_msg}")
                    print(f"Full response: {docuseal_response}")
                    
                    return Response(
                        {"error": f"Document service returned invalid data: {error_msg}"},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE
                    )
                
                # Generate unique external ID
                external_id = f"roblox_intake_{user_detail.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Create document submission record
                submission = DocumentSubmission.objects.create(
                    user_detail=user_detail,
                    document_template=doc_template,
                    docuseal_submission_id=submission_id,
                    docuseal_submitter_id=submitter_id,
                    docuseal_slug=submitter_slug,
                    status='pending',
                    external_id=external_id
                )
                
                # Build signing URL
                signing_url = f"{settings.NEXTKEYSIGN_BASE_URL}/s/{submitter_slug}"
                
                # Log the creation
                print(f"Created document submission {submission.id} for user {user_detail.email}")
                
                return Response({
                    "submission_url": signing_url,
                    "submission_id": submission_id,
                    "status": "pending",
                    "external_id": external_id
                }, status=status.HTTP_201_CREATED)
            
            else:
                # DocuSeal API error
                error_msg = response.text
                print(f"DocuSeal API error: {response.status_code} - {error_msg}")
                
                return Response(
                    {"error": f"Document service error: {error_msg}"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
                
        except Exception as e:
            print(f"Error creating document submission: {str(e)}")
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentWebhookAPIView(APIView):
    def post(self, request):
        try:
            webhook_data = request.data
            
            # Extract event type and timestamp
            event_type = webhook_data.get('event_type')
            webhook_timestamp = webhook_data.get('timestamp')
            
            # Convert webhook timestamp to Django timezone
            webhook_datetime = None
            if webhook_timestamp:
                webhook_datetime = parse_datetime(webhook_timestamp)
            
            # Extract submission or submitter data based on event type
            data = webhook_data.get('data', {})
            
            # Determine submission ID based on event type
            submission_id = None
            submitter_id = None
            
            if event_type and event_type.startswith('form.'):
                # Form webhook - data contains submitter info
                submission_id = data.get('submission_id')
                submitter_id = data.get('id')
            elif event_type and event_type.startswith('submission.'):
                # Submission webhook - data contains submission info
                submission_id = data.get('id')
                submitter_id = None
            else:
                return Response({"status": "ok"}, status=status.HTTP_200_OK)
            
            if not submission_id:
                return Response({"error": "No submission ID in webhook"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Find corresponding submission
            try:
                submission = DocumentSubmission.objects.get(docuseal_submission_id=submission_id)
            except DocumentSubmission.DoesNotExist:
                return Response({"status": "ok"}, status=status.HTTP_200_OK)
            
            # Log webhook event for debugging and audit trail
            DocumentWebhookEvent.objects.create(
                event_type=event_type,
                document_submission=submission,
                webhook_data=webhook_data,
                processed=False
            )
            
            # Update status based on event type
            updated = False
            
            if event_type == 'submission.completed':
                submission.status = 'completed'
                
                # Use webhook timestamp or current time
                submission.completed_at = webhook_datetime or timezone.now()
                updated = True
                
                # Extract audit log URL from submission data
                audit_log_url = data.get('audit_log_url')
                if audit_log_url:
                    submission.audit_log_url = audit_log_url
                
                # Extract document URLs from documents array
                documents = data.get('documents', [])
                if documents and len(documents) > 0:
                    submission.signed_document_url = documents[0].get('url')
                    
            elif event_type == 'form.completed':
                # Single party completed form
                submission.status = 'completed'
                
                # Use timestamp from webhook data - check multiple locations
                completed_at = data.get('completed_at')
                if completed_at:
                    submission.completed_at = parse_datetime(completed_at)
                else:
                    submission.completed_at = webhook_datetime or timezone.now()
                
                updated = True
                
                # Extract document URLs - check both direct and nested submission
                documents = data.get('documents', [])
                
                if not documents:
                    # Check nested submission object
                    nested_submission = data.get('submission', {})
                    
                    if nested_submission.get('combined_document_url'):
                        submission.signed_document_url = nested_submission['combined_document_url']
                    elif nested_submission.get('audit_log_url'):
                        submission.audit_log_url = nested_submission['audit_log_url']
                elif len(documents) > 0:
                    submission.signed_document_url = documents[0].get('url')
                
                # Extract audit log URL from multiple possible locations
                audit_log_url = data.get('audit_log_url')
                if not audit_log_url:
                    nested_submission = data.get('submission', {})
                    audit_log_url = nested_submission.get('audit_log_url')
                
                if audit_log_url:
                    submission.audit_log_url = audit_log_url
                    
            elif event_type == 'form.declined':
                submission.status = 'declined'
                
                # Use timestamp from webhook data
                declined_at = data.get('declined_at')
                if declined_at:
                    submission.declined_at = parse_datetime(declined_at)
                else:
                    submission.declined_at = webhook_datetime or timezone.now()
                
                # Extract decline reason if provided
                decline_reason = data.get('decline_reason')
                if decline_reason:
                    submission.decline_reason = decline_reason
                updated = True
                
            elif event_type == 'submission.expired':
                submission.status = 'expired'
                updated = True
                
            elif event_type == 'form.viewed':
                # Update opened status and timestamp
                if submission.status in ['pending', 'sent']:
                    submission.status = 'opened'
                
                # Use timestamp from webhook data
                opened_at = data.get('opened_at')
                if opened_at and not submission.opened_at:
                    submission.opened_at = parse_datetime(opened_at)
                elif not submission.opened_at:
                    submission.opened_at = webhook_datetime or timezone.now()
                
                updated = True
                
            elif event_type == 'form.started':
                # Similar to form.viewed
                if submission.status in ['pending', 'sent']:
                    submission.status = 'opened'
                
                if not submission.opened_at:
                    submission.opened_at = webhook_datetime or timezone.now()
                
                updated = True
                    
            elif event_type == 'submission.created':
                # Update to sent status and set sent_at timestamp
                if submission.status == 'pending':
                    submission.status = 'sent'
                    
                    # Extract sent_at from submitters array
                    submitters = data.get('submitters', [])
                    if submitters and len(submitters) > 0:
                        sent_at = submitters[0].get('sent_at')
                        if sent_at:
                            submission.sent_at = parse_datetime(sent_at)
                        else:
                            submission.sent_at = webhook_datetime or timezone.now()
                    else:
                        submission.sent_at = webhook_datetime or timezone.now()
                    
                    updated = True
                    
            elif event_type == 'submission.archived':
                submission.status = 'archived'
                updated = True
            
            # Save submission if updated
            if updated:
                submission.save()
            
            # Mark webhook as processed
            webhook_event = DocumentWebhookEvent.objects.filter(
                document_submission=submission, 
                event_type=event_type
            ).last()
            if webhook_event:
                webhook_event.processed = True
                webhook_event.save()
            
            return Response({"status": "ok"}, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {"error": f"Webhook processing error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
