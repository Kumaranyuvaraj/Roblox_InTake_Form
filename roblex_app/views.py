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
