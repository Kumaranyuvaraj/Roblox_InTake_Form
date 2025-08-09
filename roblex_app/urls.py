from django.urls import path

from roblex_app.views import IntakeFormAPIView, intake_form_view,SubmitIntakeIfValidAPIView,UserDetailCreateView,\
QuestionListAPIView, SubmitAnswerAPIView,landing_page,index_page,SendEmailAPIView,EmailTemplateAPIView,\
CreateDocumentSubmissionAPIView, DocumentWebhookAPIView, CheckDocumentStatusAPIView, CheckIntakeStatusAPIView

from .views import validate_roblox_username,get_client_ip,email_view,retainer_form,thanks,about_us_view,disclaimer_view,\
participating_firms_view,privacy_policy_view,terms_of_service_view
urlpatterns = [
    path('', landing_page, name='landing-page'),
    path('index/', index_page, name='index-page'),
    path('intake-form/<int:user_detail_id>/', intake_form_view, name='intake-form-page'), 
    path('api/intake-form/', IntakeFormAPIView.as_view(), name='intake-form'),
    path('api/validate-roblox/', validate_roblox_username, name='validate_roblox'),
    path("api/submit-validated-intake/", SubmitIntakeIfValidAPIView.as_view(), name="submit_validated_intake"),
    path('api/check-intake-status/', CheckIntakeStatusAPIView.as_view(), name='check-intake-status'),

    
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


    # path('read-doc/<str:filename>/', read_docx_file, name='read_docx'),
     path('about-us/', about_us_view, name='about_us'),
    #  path('consent-box/', consent_box_view, name='consent_box'),
    path('disclaimer/', disclaimer_view, name='disclaimer'),
    path('participating-firms/', participating_firms_view, name='participating_firms'),
    path('privacy-policy/', privacy_policy_view, name='privacy_policy'),
    path('terms-of-service/', terms_of_service_view, name='terms_of_service'),


]