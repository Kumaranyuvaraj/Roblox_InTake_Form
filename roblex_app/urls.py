from django.urls import path

from roblex_app.views import IntakeFormAPIView, IntakeFormView,SubmitIntakeIfValidAPIView

from .views import validate_roblox_username

# from roblex_app.views import generate_pdf

urlpatterns = [
    path('', IntakeFormView.as_view(), name='intake-form-page'),  # Serves the form page
    path('api/intake-form/', IntakeFormAPIView.as_view(), name='intake-form'),
    path('api/validate-roblox/', validate_roblox_username, name='validate_roblox'),
    path("api/submit-validated-intake/", SubmitIntakeIfValidAPIView.as_view(), name="submit_validated_intake"),
    # path('intake-form/<int:pk>/pdf/', IntakeFormPDFView.as_view(), name='intake-form-pdf'),
]