from django.urls import path

from roblex_app.views import IntakeFormAPIView, IntakeFormView
# from roblex_app.views import generate_pdf

urlpatterns = [
    path('', IntakeFormView.as_view(), name='intake-form-page'),  # Serves the form page
    path('api/intake-form/', IntakeFormAPIView.as_view(), name='intake-form'),
    # path('api/intake-form-smart-advocate/', IntakeForm_SmartAdvocateAPIView.as_view(), name='intake-form-smart-advocat'),
    # path('intake-form/<int:pk>/pdf/', IntakeFormPDFView.as_view(), name='intake-form-pdf'),
]