import logging
import pandas as pd
import requests
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from celery import shared_task
from celery.exceptions import Retry
from .models import (
    ExcelUpload, RetainerRecipient, DocumentSubmission, 
    DocumentWebhookEvent, DocumentTemplate, EmailTemplate
)
from .email_service import LawFirmEmailService

logger = logging.getLogger(__name__)


@shared_task(bind=True, queue='retainer_processing')
def process_excel_upload(self, upload_id):
    """
    Main task to process an Excel upload and create RetainerRecipient records
    """
    try:
        upload = ExcelUpload.objects.get(id=upload_id)
        upload.status = 'processing'
        upload.processing_started_at = timezone.now()
        upload.save()
        
        logger.info(f"Starting processing of Excel upload {upload_id}")
        
        # Read Excel file
        df = pd.read_excel(upload.file.path)
        total_rows = len(df)
        upload.total_rows = total_rows
        upload.save()
        
        # Expected columns
        required_columns = ['ID', 'Name', 'Email']
        optional_columns = ['Phone', 'State', 'Zip Code', 'Age', 'First Name Injured', 'Last Name Injured']
        
        # Validate required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        
        successful_count = 0
        failed_count = 0
        skipped_count = 0
        
        for index, row in df.iterrows():
            try:
                # Validate required fields
                if pd.isna(row['ID']) or pd.isna(row['Name']) or pd.isna(row['Email']):
                    skipped_count += 1
                    logger.warning(f"Skipping row {index + 1}: Missing required data")
                    continue
                
                # Create RetainerRecipient
                recipient = RetainerRecipient.objects.create(
                    excel_upload=upload,
                    external_id=str(row['ID']),
                    name=str(row['Name']),
                    email=str(row['Email']),
                    phone=str(row.get('Phone', '')) if not pd.isna(row.get('Phone', '')) else '',
                    state=str(row.get('State', '')) if not pd.isna(row.get('State', '')) else '',
                    zip_code=str(row.get('Zip Code', '')) if not pd.isna(row.get('Zip Code', '')) else '',
                    age=int(row.get('Age', 0)) if not pd.isna(row.get('Age', 0)) and row.get('Age', 0) != '' else None,
                    first_name_injured=str(row.get('First Name Injured', '')) if not pd.isna(row.get('First Name Injured', '')) else '',
                    last_name_injured=str(row.get('Last Name Injured', '')) if not pd.isna(row.get('Last Name Injured', '')) else '',
                )
                
                # Queue NextKeySign submission task
                create_nextkeysign_submission.delay(recipient.id)
                successful_count += 1
                
                # Update progress
                upload.processed_rows = successful_count + failed_count + skipped_count
                upload.save()
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Error processing row {index + 1}: {str(e)}")
                continue
        
        # Update final statistics
        upload.successful_submissions = successful_count
        upload.failed_submissions = failed_count
        upload.skipped_rows = skipped_count
        upload.status = 'completed'
        upload.completed_at = timezone.now()
        upload.save()
        
        logger.info(f"Completed processing Excel upload {upload_id}: {successful_count} successful, {failed_count} failed, {skipped_count} skipped")
        
        return {
            'upload_id': upload_id,
            'total_rows': total_rows,
            'successful': successful_count,
            'failed': failed_count,
            'skipped': skipped_count
        }
        
    except Exception as e:
        logger.error(f"Error processing Excel upload {upload_id}: {str(e)}")
        
        try:
            upload = ExcelUpload.objects.get(id=upload_id)
            upload.status = 'failed'
            upload.error_message = str(e)
            upload.completed_at = timezone.now()
            upload.save()
        except:
            pass
            
        raise


@shared_task(bind=True, queue='retainer_submissions', max_retries=3)
def create_nextkeysign_submission(self, recipient_id):
    """
    Create a NextKeySign submission for a specific recipient and send custom email
    """
    try:
        recipient = RetainerRecipient.objects.get(id=recipient_id)
        upload = recipient.excel_upload
        law_firm = upload.law_firm
        
        logger.info(f"Creating NextKeySign submission for recipient {recipient_id}")
        
        # Generate external ID
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        external_id = f"retainer_{recipient.id}_{timestamp}"
        
        # Prepare NextKeySign API request (with email disabled)
        nextkeysign_url = f"{settings.NEXTKEYSIGN_BASE_URL}/api/submissions"
        headers = {
            'X-Auth-Token': settings.NEXTKEYSIGN_API_TOKEN,
            'Content-Type': 'application/json'
        }
        
        payload = {
            "template_id": upload.document_template.nextkeysign_template_id,
            "send_email": False,
            "submitters": [
                {
                    "name": recipient.name,
                    "email": recipient.email,
                    "external_id": external_id,
                    "role": "Client"
                }
            ]
        }
        
        # Make API request
        response = requests.post(nextkeysign_url, json=payload, headers=headers)
        response.raise_for_status()
        
        response_data = response.json()
        
        # Handle NextKeySign response format - it returns an array of submitters directly
        if isinstance(response_data, list) and len(response_data) > 0:
            first_submitter = response_data[0]
            submission_id = first_submitter.get('submission_id', '')
            submitter_slug = first_submitter.get('slug', '')
        else:
            # Fallback to handle different response formats
            first_submitter = response_data.get('submitters', [{}])[0] if 'submitters' in response_data else {}
            submission_id = response_data.get('id', '')
            submitter_slug = first_submitter.get('slug', '')
        
        # Create DocumentSubmission record
        submission = DocumentSubmission.objects.create(
            recipient=recipient,
            document_template=upload.document_template,
            nextkeysign_submission_id=str(submission_id),
            nextkeysign_submitter_id=str(first_submitter.get('id', '')),
            nextkeysign_slug=str(submitter_slug),
            external_id=external_id,
            status='created',  # Set to created, will update to sent after email
            sent_at=timezone.now()
        )
        
        # Generate signing URL
        signing_url = f"{settings.NEXTKEYSIGN_BASE_URL}/s/{submitter_slug}"
        
        # Send custom email using law firm's email configuration
        if law_firm.has_email_config():
            # Send custom email via background task
            send_retainer_email.delay(recipient.id, submission.id, external_id)
            submission.status = 'sent'
            submission.save()
            logger.info(f"Custom email queued for recipient {recipient_id}")
        else:
            logger.warning(f"Law firm {law_firm.name} has incomplete email configuration, skipping email")
            submission.status = 'sent'  # Still mark as sent so NextKeySign process continues
            submission.save()
        
        # Update recipient status
        recipient.status = 'submitted'
        recipient.last_processed_at = timezone.now()
        recipient.save()
        
        logger.info(f"Successfully created NextKeySign submission {submission.nextkeysign_submission_id} for recipient {recipient_id}")
        
        return {
            'recipient_id': recipient_id,
            'submission_id': submission.nextkeysign_submission_id,
            'external_id': external_id,
            'signing_url': signing_url
        }
        
    except Exception as e:
        logger.error(f"Error creating NextKeySign submission for recipient {recipient_id}: {str(e)}")
        
        try:
            recipient = RetainerRecipient.objects.get(id=recipient_id)
            recipient.status = 'failed'
            recipient.error_message = str(e)
            recipient.retry_count += 1
            recipient.last_processed_at = timezone.now()
            recipient.save()
        except:
            pass
        
        # Retry logic
        if self.request.retries < self.max_retries:
            countdown = 60 * (2 ** self.request.retries)  # Exponential backoff
            raise self.retry(countdown=countdown, exc=e)
        
        raise


@shared_task(bind=True, queue='retainer_submissions')
def retry_failed_submission(self, recipient_id):
    """
    Retry a failed NextKeySign submission
    """
    try:
        recipient = RetainerRecipient.objects.get(id=recipient_id)
        
        if recipient.status != 'failed':
            logger.warning(f"Recipient {recipient_id} is not in failed status, skipping retry")
            return
        
        logger.info(f"Retrying failed submission for recipient {recipient_id}")
        
        # Reset status and call main submission task
        recipient.status = 'pending'
        recipient.error_message = ''
        recipient.save()
        
        return create_nextkeysign_submission.delay(recipient_id)
        
    except Exception as e:
        logger.error(f"Error retrying submission for recipient {recipient_id}: {str(e)}")
        raise


@shared_task(bind=True, queue='retainer_submissions')
def resend_email_notification(self, recipient_id):
    """
    Resend email notification for an existing NextKeySign submission
    """
    try:
        recipient = RetainerRecipient.objects.get(id=recipient_id)
        
        # Check if recipient has a document submission
        try:
            submission = recipient.document_submission
        except DocumentSubmission.DoesNotExist:
            logger.error(f"No document submission found for recipient {recipient_id}")
            return False
        
        upload = recipient.excel_upload
        law_firm = upload.law_firm
        
        # Check if law firm has email configuration
        if not law_firm.has_email_config():
            logger.error(f"Law firm {law_firm.name} has incomplete email configuration")
            return False
        
        # Generate signing URL
        signing_url = f"{settings.NEXTKEYSIGN_BASE_URL}/s/{submission.nextkeysign_slug}"
        
        # Send email
        email_sent = send_retainer_email.delay(
            recipient_id=recipient.id,
            submission_id=submission.id,
            external_id=submission.external_id
        )
        
        if email_sent:
            # Update submission status if it was previously failed
            if submission.status in ['failed', 'created']:
                submission.status = 'sent'
                submission.sent_at = timezone.now()
                submission.save()
            
            recipient.last_processed_at = timezone.now()
            recipient.save()
            
            logger.info(f"Email resent successfully for recipient {recipient_id}")
            return True
        else:
            logger.error(f"Failed to resend email for recipient {recipient_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error resending email for recipient {recipient_id}: {str(e)}")
        return False


@shared_task(queue='retainer_processing')
def test_law_firm_email(law_firm_id, test_email):
    """
    Test email configuration for a law firm
    """
    try:
        from .models import LawFirm
        from .email_service import send_test_email
        
        law_firm = LawFirm.objects.get(id=law_firm_id)
        success, message = send_test_email(law_firm, test_email)
        
        logger.info(f"Email test for law firm {law_firm.name}: {message}")
        return {
            'success': success,
            'message': message,
            'law_firm': law_firm.name
        }
        
    except Exception as e:
        logger.error(f"Error testing email for law firm {law_firm_id}: {str(e)}")
        return {
            'success': False,
            'message': f"Error: {str(e)}",
            'law_firm': 'Unknown'
        }

@shared_task(bind=True, queue='retainer_submissions', max_retries=3)
def send_retainer_email(self, recipient_id, submission_id, external_id):
    """
    Send retainer agreement email using law firm's email configuration
    """
    try:
        from .models import RetainerRecipient, DocumentSubmission
        
        recipient = RetainerRecipient.objects.get(id=recipient_id)
        submission = DocumentSubmission.objects.get(id=submission_id)
        upload = recipient.excel_upload
        law_firm = upload.law_firm
        
        logger.info(f"Sending retainer email for recipient {recipient_id}")
        
        # Check if law firm has email configuration
        if not law_firm.has_email_config():
            raise ValueError(f"Law firm {law_firm.name} has incomplete email configuration")
        
        # Generate signing URL
        signing_url = f"{settings.NEXTKEYSIGN_BASE_URL}/s/{submission.nextkeysign_slug}"
        
        # Send email using law firm's email service
        email_service = LawFirmEmailService(law_firm)
        email_sent = email_service.send_retainer_email(
            recipient=recipient,
            email_template=upload.email_template,
            signing_url=signing_url,
            external_id=external_id
        )
        
        if email_sent:
            # Update submission status
            submission.status = 'sent'
            submission.sent_at = timezone.now()
            submission.save()
            
            # Update recipient
            recipient.last_processed_at = timezone.now()
            recipient.save()
            
            logger.info(f"Email sent successfully for recipient {recipient_id}")
            return {
                'recipient_id': recipient_id,
                'submission_id': submission_id,
                'email_sent': True
            }
        else:
            raise Exception("Failed to send email")
            
    except Exception as e:
        logger.error(f"Error sending email for recipient {recipient_id}: {str(e)}")
        
        try:
            # Update submission status on failure
            submission = DocumentSubmission.objects.get(id=submission_id)
            submission.status = 'email_failed'
            submission.save()
            
            recipient = RetainerRecipient.objects.get(id=recipient_id)
            recipient.error_message = f"Email failed: {str(e)}"
            recipient.save()
        except:
            pass
        
        # Retry logic
        if self.request.retries < self.max_retries:
            countdown = 60 * (2 ** self.request.retries)  # Exponential backoff
            raise self.retry(countdown=countdown, exc=e)
        
        raise