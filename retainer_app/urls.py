from django.urls import path
from . import views

app_name = 'retainer_app'

urlpatterns = [
    # Webhook endpoint for NextKeySign
    path('webhook/nextkeysign/', views.DocumentWebhookAPIView.as_view(), name='nextkeysign_webhook'),
    
    # API endpoints for future expansion
    path('api/upload-status/<int:upload_id>/', views.UploadStatusAPIView.as_view(), name='upload_status'),
    path('api/retry-failed/<int:recipient_id>/', views.RetryFailedSubmissionAPIView.as_view(), name='retry_failed'),
]
