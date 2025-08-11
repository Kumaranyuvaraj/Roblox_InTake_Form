import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import (
    ExcelUpload, RetainerRecipient, DocumentSubmission, DocumentWebhookEvent
)
from .tasks import retry_failed_submission

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class DocumentWebhookAPIView(APIView):
    """
    Handle NextKeySign webhook events for retainer documents
    """
    
    def post(self, request):
        try:
            webhook_data = request.data if hasattr(request, 'data') else json.loads(request.body)
            event_type = webhook_data.get('event_type', '')
            
            logger.info(f"Received NextKeySign webhook: {event_type}")
            
            # Extract submission data
            submission_data = webhook_data.get('data', {})
            submission_id = submission_data.get('id')
            external_id = submission_data.get('external_id', '')
            
            if not submission_id:
                logger.error("No submission ID in webhook data")
                return Response({'error': 'No submission ID'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Find corresponding DocumentSubmission
            try:
                doc_submission = DocumentSubmission.objects.get(
                    nextkeysign_submission_id=str(submission_id)
                )
            except DocumentSubmission.DoesNotExist:
                logger.error(f"DocumentSubmission not found for ID: {submission_id}")
                return Response({'error': 'Submission not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Create webhook event record
            webhook_event = DocumentWebhookEvent.objects.create(
                document_submission=doc_submission,
                event_type=event_type,
                webhook_data=webhook_data
            )
            
            # Process different event types
            if event_type == 'form.viewed':
                # User opened the document for viewing
                if doc_submission.status in ['created', 'sent']:
                    doc_submission.status = 'opened'
                    doc_submission.opened_at = timezone.now()
                
            elif event_type == 'form.started':
                # User started filling out the form
                if doc_submission.status in ['created', 'sent', 'opened']:
                    doc_submission.status = 'opened'
                    if not doc_submission.opened_at:
                        doc_submission.opened_at = timezone.now()
                
            elif event_type == 'form.completed':
                # User completed and submitted the form
                if doc_submission.status != 'completed':  # Don't override if already completed
                    doc_submission.status = 'completed'
                    doc_submission.completed_at = timezone.now()
                    doc_submission.recipient.status = 'completed'
                    doc_submission.recipient.last_processed_at = timezone.now()
                    doc_submission.recipient.save()
                
                # Extract document URLs from form.completed event
                # Note: form.completed has different data structure than submission.completed
                if not doc_submission.signed_document_url:  # Only set if not already set
                    documents = submission_data.get('documents', [])
                    if documents and len(documents) > 0:
                        doc_submission.signed_document_url = documents[0].get('url', '')
                
                # Extract audit log URL if available
                if not doc_submission.audit_log_url and submission_data.get('audit_log_url'):
                    doc_submission.audit_log_url = submission_data.get('audit_log_url', '')
                
            elif event_type == 'form.declined':
                # User declined to sign the document
                doc_submission.status = 'declined'
                doc_submission.declined_at = timezone.now()
                doc_submission.recipient.status = 'failed'
                doc_submission.recipient.error_message = 'Document declined by recipient'
                doc_submission.recipient.last_processed_at = timezone.now()
                doc_submission.recipient.save()
                
                # Extract decline reason from submission data
                doc_submission.decline_reason = submission_data.get('decline_reason', '')
                    
            elif event_type == 'submission.created':
                # Submission was created in NextKeySign
                if doc_submission.status == 'created':
                    doc_submission.status = 'sent'
                    doc_submission.sent_at = timezone.now()
                    doc_submission.recipient.status = 'submitted'
                    doc_submission.recipient.last_processed_at = timezone.now()
                    doc_submission.recipient.save()
                
                # Update submitter information if not already set
                submitters = submission_data.get('submitters', [])
                if submitters and not doc_submission.nextkeysign_submitter_id:
                    submitter = submitters[0]
                    doc_submission.nextkeysign_submitter_id = str(submitter.get('id', ''))
                    doc_submission.nextkeysign_slug = str(submitter.get('slug', ''))
                
            elif event_type == 'submission.completed':
                # Submission was completed (all parties signed)
                doc_submission.status = 'completed'
                doc_submission.completed_at = timezone.now()
                doc_submission.recipient.status = 'completed'
                doc_submission.recipient.last_processed_at = timezone.now()
                doc_submission.recipient.save()
                
                # Extract document URLs and audit log from submission.completed
                # This event has more complete data than form.completed
                submitters = submission_data.get('submitters', [])
                if submitters:
                    submitter = submitters[0]
                    # Always update from submission.completed as it's more authoritative
                    documents = submitter.get('documents', [])
                    if documents:
                        doc_submission.signed_document_url = documents[0].get('url', '')
                
                # Always update audit log from submission.completed
                if submission_data.get('audit_log_url'):
                    doc_submission.audit_log_url = submission_data.get('audit_log_url', '')
                
            elif event_type == 'submission.expired':
                # Submission expired without completion
                doc_submission.status = 'expired'
                doc_submission.recipient.status = 'failed'
                doc_submission.recipient.error_message = 'Document submission expired'
                doc_submission.recipient.last_processed_at = timezone.now()
                doc_submission.recipient.save()
                
            elif event_type == 'submission.archived':
                # Submission was archived
                # Keep current status but log the archival
                logger.info(f"Submission {submission_id} was archived")
                
            elif event_type == 'template.created':
                # Template was created - not directly related to submissions
                logger.info(f"Template created: {submission_data.get('name', 'Unknown')}")
                
            elif event_type == 'template.updated':
                # Template was updated - not directly related to submissions
                logger.info(f"Template updated: {submission_data.get('name', 'Unknown')}")                
            else:
                # Unknown event type - log it for debugging
                logger.warning(f"Unknown webhook event type: {event_type}")
                # Don't fail the webhook, just log it
            
            # Save changes
            doc_submission.save()
            
            # Mark webhook as processed
            webhook_event.processed = True
            webhook_event.save()
            
            logger.info(f"Successfully processed webhook event: {event_type} for submission {submission_id}")
            
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error processing NextKeySign webhook: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UploadStatusAPIView(APIView):
    """
    Get status of an Excel upload
    """
    
    def get(self, request, upload_id):
        try:
            upload = ExcelUpload.objects.get(id=upload_id)
            
            data = {
                'id': upload.id,
                'status': upload.status,
                'total_rows': upload.total_rows,
                'processed_rows': upload.processed_rows,
                'successful_submissions': upload.successful_submissions,
                'failed_submissions': upload.failed_submissions,
                'skipped_rows': upload.skipped_rows,
                'success_rate': upload.get_success_rate(),
                'created_at': upload.created_at,
                'completed_at': upload.completed_at,
            }
            
            return Response(data, status=status.HTTP_200_OK)
            
        except ExcelUpload.DoesNotExist:
            return Response({'error': 'Upload not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RetryFailedSubmissionAPIView(APIView):
    """
    Retry a failed submission
    """
    
    def post(self, request, recipient_id):
        try:
            recipient = RetainerRecipient.objects.get(id=recipient_id)
            
            if recipient.status != 'failed':
                return Response(
                    {'error': 'Recipient is not in failed status'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Trigger retry task
            task = retry_failed_submission.delay(recipient_id)
            
            return Response({
                'status': 'retry_triggered',
                'task_id': task.id,
                'recipient_id': recipient_id
            }, status=status.HTTP_200_OK)
            
        except RetainerRecipient.DoesNotExist:
            return Response({'error': 'Recipient not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
