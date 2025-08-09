from datetime import date
import json
import os
import re
import traceback
from docx import Document
import requests
import base64
import uuid
import smtplib
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from roblex_app.models import IntakeForm, EmailTemplate, UserDetail, Question, Option, UserAnswer, EmailLog, DocumentTemplate, DocumentSubmission, DocumentWebhookEvent
from roblex_app.serializers import EmailTemplateSerializer, IntakeFormSerializer, UserDetailSerializer, QuestionSerializer, UserAnswerSerializer, EmailLogSerializer
from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from rest_framework.parsers import MultiPartParser, FormParser


def requires_florida_disclosure(zipcode):
    """
    Check if zipcode falls within Florida disclosure range (32003-34997)
    """
    if not zipcode:
        return False
    
    # Extract numeric part from zipcode (handle ZIP+4 format)
    zip_numeric = zipcode.split('-')[0]
    
    try:
        zip_int = int(zip_numeric)
        return 32003 <= zip_int <= 34997
    except (ValueError, TypeError):
        return False


def intake_form_view(request, user_detail_id):
    """
    Handles GET to show the form with access control based on UserDetail ID
    """
    # Verify that the user_detail_id exists - returns 404 if not found
    user_detail = get_object_or_404(UserDetail, id=user_detail_id)
    
    # Check if user has already submitted an intake form
    existing_intake = IntakeForm.objects.filter(user_detail=user_detail).first()
    if existing_intake:
        # User has already submitted an intake form, redirect to thank you page
        return redirect('/gratitude?already_submitted=true')
    
    # Only handle GET requests for form display
    if request.method != 'GET':
        # For POST requests, redirect back to form (keeping the same pattern)
        return redirect('intake-form-page', user_detail_id=user_detail_id)
    
    # Check for status parameters from document signing
    signed = request.GET.get('signed')
    workflow = request.GET.get('workflow')
    prequalified = request.GET.get('prequalified')
    
    # Pass user_detail context to template for prefilling form data
    context = {
        'user_detail': user_detail,
        'user_detail_id': user_detail_id,
        'signed_status': signed,
        'workflow_type': workflow,
        'prequalified': prequalified
    }
    
    return render(request, 'forms.html', context)


def landing_page(request):
    """
    Serves the landing page form HTML page
    """
    return render(request, 'index.html')
    
def index_page(request):
    """
    Serves the index page form HTML page
    """
    return render(request, 'index.html')

class IntakeFormAPIView(APIView):
    def post(self, request):
        # Get user_detail_id from request data or URL
        user_detail_id = request.data.get('user_detail_id')
        
        if not user_detail_id:
            return Response(
                {'error': 'user_detail_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify UserDetail exists
        try:
            user_detail = UserDetail.objects.get(id=user_detail_id)
        except UserDetail.DoesNotExist:
            return Response(
                {'error': 'Invalid user_detail_id'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = IntakeFormSerializer(data=request.data)
        
        if serializer.is_valid():
            # Get the law firm from middleware (subdomain detection)
            law_firm = getattr(request, 'law_firm', None)
            if not law_firm:
                # Fallback to user_detail's law firm or default
                law_firm = user_detail.law_firm
            
            # Link the intake form to the UserDetail and law firm
            intake_form = serializer.save(user_detail=user_detail, law_firm=law_firm)
            
            # Push to SmartAdvocate
            response = push_to_smart_advocate(data=request.data)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
    

class CheckIntakeStatusAPIView(APIView):
    """
    Check if a user has already submitted an intake form
    """
    def post(self, request):
        try:
            user_detail_id = request.data.get('user_detail_id')
            
            if not user_detail_id:
                return Response(
                    {"error": "user_detail_id is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                user_detail = UserDetail.objects.get(id=user_detail_id)
            except UserDetail.DoesNotExist:
                return Response(
                    {"error": "User not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if intake form exists
            existing_intake = IntakeForm.objects.filter(user_detail=user_detail).first()
            
            return Response({
                "already_submitted": existing_intake is not None,
                "intake_id": existing_intake.id if existing_intake else None
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
        data = request.data.copy() 
        
        # Get user_detail_id from request data
        user_detail_id = data.get('user_detail_id')
        if not user_detail_id:
            return Response(
                {'error': 'user_detail_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify UserDetail exists
        try:
            user_detail = UserDetail.objects.get(id=user_detail_id)
        except UserDetail.DoesNotExist:
            return Response(
                {'error': 'Invalid user_detail_id'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user has already submitted an intake form
        existing_intake = IntakeForm.objects.filter(user_detail=user_detail).first()
        if existing_intake:
            return Response(
                {
                    'error': 'You have already submitted an intake form',
                    'already_submitted': True,
                    'intake_id': existing_intake.id
                }, 
                status=status.HTTP_409_CONFLICT
            )
            
        if 'client_ip' in data and data['client_ip']:
            client_ip_raw = str(data['client_ip']).strip()
            first_ip = client_ip_raw.split(',')[0].strip()
            data['client_ip'] = first_ip

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

            # Link the intake form to the UserDetail
            intake_instance = serializer.save(user_detail=user_detail)

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
            # Automatically associate with the law firm from subdomain
            law_firm = getattr(request, 'law_firm', None)
            if law_firm:
                serializer.save(law_firm=law_firm)
            else:
                # Fallback to default law firm if middleware isn't working
                from roblex_app.models import LawFirm
                default_firm = LawFirm.objects.filter(subdomain='default').first()
                serializer.save(law_firm=default_firm)
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

def thanks(request):
    # Check if user is being redirected because they already submitted
    already_submitted = request.GET.get('already_submitted', 'false').lower() == 'true'
    
    context = {
        'already_submitted': already_submitted
    }
    
    return render(request, 'thankyou.html', context)

# ====================
# DocuSeal API Views
# ====================

class CreateDocumentSubmissionAPIView(APIView):
    """
    Creates document submissions with dynamic Florida disclosure workflow.
    For Florida zipcodes (32003-34997), creates both disclosure and retainer documents at once.
    """
    
    def post(self, request):
        try:
            # Extract required parameters
            user_detail_id = request.data.get('user_detail_id')
            template_type = request.data.get('template_type', 'retainer_agreement')
            email_template_type = request.data.get('email_template_type', 'eligible_no_parent')
            
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
            
            # **NEW**: Florida disclosure workflow - create all required documents at once
            florida_required = requires_florida_disclosure(user_detail.zipcode)
            
            if florida_required and template_type in ['retainer_agreement', 'retainer_minor', 'retainer_adult']:
                # Create both Florida disclosure and retainer documents
                print(f"Florida zipcode {user_detail.zipcode} detected - creating both documents")
                
                # Determine correct retainer type based on age
                retainer_template_type = 'retainer_adult'  # Default
                if user_detail.gamer_dob:
                    from datetime import date
                    today = date.today()
                    dob = user_detail.gamer_dob
                    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                    retainer_template_type = 'retainer_minor' if age < 18 else 'retainer_adult'
                
                # Create both documents
                documents_created = self._create_florida_workflow_documents(user_detail, retainer_template_type, email_template_type, request)
                
                if documents_created:
                    # Get the first document (Florida disclosure) for initial signing
                    florida_disclosure_submission = None
                    for doc in documents_created:
                        if doc.document_template.name == 'florida_disclosure':
                            florida_disclosure_submission = doc
                            break
                    
                    # If we found the Florida disclosure, provide its signing URL
                    if florida_disclosure_submission:
                        signing_url = f"{settings.NEXTKEYSIGN_BASE_URL}/s/{florida_disclosure_submission.docuseal_slug}"
                        
                        return Response({
                            "message": "Both Florida disclosure and retainer documents created successfully",
                            "submission_url": signing_url,  # Frontend expects this field
                            "submission_id": florida_disclosure_submission.docuseal_submission_id,
                            "status": "pending",
                            "external_id": florida_disclosure_submission.external_id,
                            "template_type": "florida_disclosure",
                            "florida_disclosure_required": True,
                            "documents_created": len(documents_created),
                            "workflow": "florida_dynamic"
                        }, status=status.HTTP_201_CREATED)
                    else:
                        return Response(
                            {"error": "Florida disclosure document not found in created documents"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
                else:
                    return Response(
                        {"error": "Failed to create Florida workflow documents"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                # Standard single document creation for non-Florida residents
                return self._create_single_document(user_detail, template_type, email_template_type, request)
                
        except Exception as e:
            print(f"Error creating document submission: {str(e)}")
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _create_florida_workflow_documents(self, user_detail, retainer_template_type, email_template_type, request):
        """
        Create both Florida disclosure and retainer documents at once
        """
        documents_created = []
        
        try:
            # 1. Create Florida disclosure document with specific Florida email template
            florida_submission = self._create_document_submission(
                user_detail, 
                'florida_disclosure', 
                'florida_disclosure',  # Use specific Florida disclosure email template
                request
            )
            
            if florida_submission:
                documents_created.append(florida_submission)
                print(f"Created Florida disclosure document: {florida_submission.id}")
            
            # 2. Create retainer document with regular email template
            retainer_submission = self._create_document_submission(
                user_detail, 
                retainer_template_type, 
                email_template_type,  # Use the original email template (eligible_no_parent or eligible_with_parent)
                request
            )
            
            if retainer_submission:
                documents_created.append(retainer_submission)
                print(f"Created retainer document: {retainer_submission.id}")
            
            return documents_created
            
        except Exception as e:
            print(f"Error creating Florida workflow documents: {str(e)}")
            return None
    
    def _create_single_document(self, user_detail, template_type, email_template_type, request):
        """
        Create a single document for non-Florida residents
        """
        try:
            # Determine correct retainer type based on age if needed
            actual_template_type = template_type
            if template_type == 'retainer_agreement':
                if user_detail.gamer_dob:
                    from datetime import date
                    today = date.today()
                    dob = user_detail.gamer_dob
                    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                    actual_template_type = 'retainer_minor' if age < 18 else 'retainer_adult'
                else:
                    actual_template_type = 'retainer_minor'  # Default to minor if no DOB
            
            submission = self._create_document_submission(
                user_detail, 
                actual_template_type, 
                email_template_type, 
                request
            )
            
            if submission:
                signing_url = f"{settings.NEXTKEYSIGN_BASE_URL}/s/{submission.docuseal_slug}"
                
                return Response({
                    "submission_url": signing_url,
                    "submission_id": submission.docuseal_submission_id,
                    "status": "pending",
                    "external_id": submission.external_id,
                    "template_type": actual_template_type,
                    "florida_disclosure_required": False
                }, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {"error": "Failed to create document submission"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            print(f"Error creating single document: {str(e)}")
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _create_document_submission(self, user_detail, template_name, email_template_type, request):
        """
        Helper method to create a single document submission
        """
        try:
            # Get document template using law firm-specific logic
            doc_template = DocumentTemplate.get_template_for_law_firm(template_name, user_detail.law_firm)
            
            if not doc_template:
                print(f"Document template '{template_name}' not found for law firm '{user_detail.law_firm}' or globally")
                return None
            
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
                "completed_redirect_url": f"{request.build_absolute_uri('/')}api/check-document-status/?user_id={user_detail.id}",
                "declined_redirect_url": f"{request.build_absolute_uri('/')}?signed=declined"
            }
            
            # Add custom message if email template exists
            if email_template:
                custom_body = email_template.body.replace('[User First Name]', user_detail.first_name)
                submitter_data["message"] = {
                    "subject": email_template.subject,
                    "body": custom_body
                }
            
            # Make API call to DocuSeal
            headers = {
                "X-Auth-Token": settings.NEXTKEYSIGN_API_TOKEN,
                "Content-Type": "application/json"
            }
            
            response = requests.post(docuseal_url, json=submitter_data, headers=headers)
            
            if response.status_code in [200, 201]:
                docuseal_response = response.json()
                
                if isinstance(docuseal_response, list) and len(docuseal_response) > 0:
                    first_submitter = docuseal_response[0]
                    
                    submission_id = first_submitter.get('submission_id')
                    submitter_id = first_submitter.get('id')
                    submitter_slug = first_submitter.get('slug', '')
                    
                    if submission_id and submitter_id:
                        # Generate unique external ID
                        external_id = f"roblox_{template_name}_{user_detail.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
                        
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
                        
                        print(f"Created document submission {submission.id} for template {template_name}")
                        return submission
            
            return None
            
        except Exception as e:
            print(f"Error creating document submission for {template_name}: {str(e)}")
            return None


class CheckDocumentStatusAPIView(APIView):
    """
    Endpoint to check document signing status for dynamic Florida workflow.
    Redirects users based on which documents they've completed.
    """
    
    def get(self, request):
        try:
            user_id = request.GET.get('user_id')
            
            if not user_id:
                return redirect('/?error=missing_user_id')
            
            try:
                user_detail = UserDetail.objects.get(id=user_id)
            except UserDetail.DoesNotExist:
                return redirect('/?error=user_not_found')
            
            # Get all document submissions for this user
            submissions = DocumentSubmission.objects.filter(user_detail=user_detail).order_by('-created_at')
            
            if not submissions.exists():
                return redirect('/?error=no_documents_found')
            
            # Check if this is a Florida workflow (has both disclosure and retainer documents)
            florida_required = requires_florida_disclosure(user_detail.zipcode)
            
            # Count completed documents by type
            completed_docs = {}
            pending_docs = {}
            import time
            time.sleep(3)
            for submission in submissions:
                template_name = submission.document_template.name
                
                if submission.status == 'completed':
                    completed_docs[template_name] = submission
                else:
                    pending_docs[template_name] = submission
            
            if florida_required:
                # Florida workflow - need both disclosure and retainer completed
                florida_completed = 'florida_disclosure' in completed_docs
                retainer_completed = any(template in completed_docs for template in ['retainer_minor', 'retainer_adult'])
                
                if florida_completed and retainer_completed:
                    # Both documents completed - success!
                    return redirect(f'/intake-form/{user_detail.id}/?signed=success&workflow=florida_complete')
                elif florida_completed and not retainer_completed:
                    # Disclosure complete, need to sign retainer
                    retainer_pending = None
                    for template in ['retainer_minor', 'retainer_adult']:
                        if template in pending_docs:
                            retainer_pending = pending_docs[template]
                            break
                    
                    if retainer_pending:
                        signing_url = f"{settings.NEXTKEYSIGN_BASE_URL}/s/{retainer_pending.docuseal_slug}"
                        return redirect(signing_url)
                    else:
                        return redirect('/?error=retainer_document_missing')
                elif not florida_completed and retainer_completed:
                    # Retainer complete, need to sign disclosure
                    florida_pending = pending_docs.get('florida_disclosure')
                    
                    if florida_pending:
                        signing_url = f"{settings.NEXTKEYSIGN_BASE_URL}/s/{florida_pending.docuseal_slug}"
                        return redirect(signing_url)
                    else:
                        return redirect('/?error=disclosure_document_missing')
                else:
                    # Neither completed - redirect to first available document
                    if 'florida_disclosure' in pending_docs:
                        signing_url = f"{settings.NEXTKEYSIGN_BASE_URL}/s/{pending_docs['florida_disclosure'].docuseal_slug}"
                        return redirect(signing_url)
                    elif pending_docs:
                        # Redirect to any pending document
                        first_pending = list(pending_docs.values())[0]
                        signing_url = f"{settings.NEXTKEYSIGN_BASE_URL}/s/{first_pending.docuseal_slug}"
                        return redirect(signing_url)
                    else:
                        return redirect('/?error=no_pending_documents')
            else:
                # Standard workflow - single document
                if completed_docs:
                    # Document completed - success!
                    return redirect(f'/intake-form/{user_detail.id}/?signed=success')
                elif pending_docs:
                    # Redirect to pending document
                    first_pending = list(pending_docs.values())[0]
                    signing_url = f"{settings.NEXTKEYSIGN_BASE_URL}/s/{first_pending.docuseal_slug}"
                    return redirect(signing_url)
                else:
                    return redirect('/?error=no_documents_available')
                    
        except Exception as e:
            print(f"Error checking document status: {str(e)}")
            return redirect('/?error=status_check_failed')


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
    


# def read_docx_file(request, filename):
#     file_path = os.path.join(settings.BASE_DIR, 'roblex_app', 'static', 'docs', filename)

#     if not os.path.exists(file_path):
#         raise Http404("Document not found")

#     doc = Document(file_path)
#     content = "\n".join([para.text for para in doc.paragraphs])

#     return render(request, 'doc_reader.html', {'content': content, 'filename': filename})


def about_us_view(request):
    return render(request, 'about_us.html')


# def consent_box_view(request):
#     return render(request, 'consent_box.html')


def disclaimer_view(request):
    return render(request, 'disclaimer.html')

def participating_firms_view(request):
    return render(request, 'participating_firms.html')

def privacy_policy_view(request):
    return render(request, 'privacy_policy.html')

def terms_of_service_view(request):
    return render(request, 'terms.html')
