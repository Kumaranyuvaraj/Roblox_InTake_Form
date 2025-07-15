from django.urls import path

from roblex_app.views import IntakeFormAPIView
# from roblex_app.views import generate_pdf

urlpatterns = [
    path('api/intake-form/', IntakeFormAPIView.as_view(), name='intake-form'),
    # path('intake-form/<int:pk>/pdf/', IntakeFormPDFView.as_view(), name='intake-form-pdf'),
]