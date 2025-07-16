import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from roblex_app.serializers import IntakeFormSerializer
from django.shortcuts import render

# from django.http import Http404, HttpResponse
# from django.template.loader import render_to_string
# from weasyprint import HTML
# from roblex_app.models import IntakeForm

class IntakeFormView(APIView):
    """
    Serves the intake form HTML page
    """
    def get(self, request):
        return render(request, 'forms.html')

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
    
