from django.urls import path

from roblex_app.views import IntakeFormAPIView, IntakeFormView,SubmitIntakeIfValidAPIView,UserDetailCreateView,\
QuestionListAPIView, SubmitAnswerAPIView,LandingPage,IndexPage,SendEmailAPIView,EmailTemplateAPIView,\
CreateDocumentSubmissionAPIView, DocumentWebhookAPIView, CheckDocumentStatusAPIView

from .views import validate_roblox_username,get_client_ip,email_view,retainer_form,thanks,read_docx_file
urlpatterns = [
    path('', LandingPage.as_view(), name='intake-form-page'), 
    path('index/', IndexPage.as_view(), name='index-form-page'),
    path('intake-form/', IntakeFormView.as_view(), name='intake-form-page'), 
    path('api/intake-form/', IntakeFormAPIView.as_view(), name='intake-form'),
    path('api/validate-roblox/', validate_roblox_username, name='validate_roblox'),
    path("api/submit-validated-intake/", SubmitIntakeIfValidAPIView.as_view(), name="submit_validated_intake"),

    
    path('api/user-details/', UserDetailCreateView.as_view(), name='user-details-create'),
    path('api/questions/', QuestionListAPIView.as_view(), name='question-list'),
    path('api/answers/submit/', SubmitAnswerAPIView.as_view(), name='submit-answer'),

    path('get-ip', get_client_ip, name='get_client_ip'),

    path('send-email/', SendEmailAPIView.as_view(), name='send-email'),#Rest API
    path('send-email-form/', email_view, name='send-email-form'),

    path('api/email-template/<str:template_type>/',EmailTemplateAPIView.as_view(),name='email-template'),
   
    # DocuSeal Document Signing API endpoints
    path('api/create-document-submission/', CreateDocumentSubmissionAPIView.as_view(), name='create-document-submission'),
    path('api/check-document-status/', CheckDocumentStatusAPIView.as_view(), name='check-document-status'),
    path('api/document-webhook/', DocumentWebhookAPIView.as_view(), name='document-webhook'),

    path('retainer-form/', retainer_form, name='retainer-form'),

    path('gratitude/', thanks, name='gratitude'),


    path('read-doc/<str:filename>/', read_docx_file, name='read_docx'),

]