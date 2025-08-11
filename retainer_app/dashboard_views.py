from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.db import models
from django.contrib import admin
from django.template.response import TemplateResponse
from .models import (
    LawFirm, LawFirmUser, DocumentSubmission, RetainerRecipient, 
    ExcelUpload, DocumentTemplate, EmailTemplate
)


@staff_member_required
def dashboard_view(request):
    """Dashboard view that integrates with Django admin"""
    
    def get_user_law_firm(request):
        """Get the law firm associated with the current user"""
        if request.user.is_superuser:
            return None
        
        try:
            # Try retainer app law firm user first (direct association)
            try:
                law_firm_user = LawFirmUser.objects.get(user=request.user)
                return law_firm_user.law_firm
            except LawFirmUser.DoesNotExist:
                pass
            
            # Import here to avoid circular imports
            from roblex_app.models import LawFirmUser as RoblexLawFirmUser
            try:
                roblex_law_firm_user = RoblexLawFirmUser.objects.get(user=request.user)
                roblex_firm_name = roblex_law_firm_user.law_firm.name
                
                # Try exact match first
                try:
                    retainer_law_firm = LawFirm.objects.get(name=roblex_firm_name)
                    return retainer_law_firm
                except LawFirm.DoesNotExist:
                    pass
                
                # Try partial match (for cases like "Bullock Legal" vs "Bullock Legal Group")
                # Look for retainer law firm containing the roblex firm name
                retainer_firms = LawFirm.objects.filter(name__icontains=roblex_firm_name)
                if retainer_firms.exists():
                    return retainer_firms.first()
                
                # Try the reverse - roblex firm name containing retainer firm name
                retainer_firms = LawFirm.objects.all()
                for firm in retainer_firms:
                    if firm.name.lower() in roblex_firm_name.lower() or roblex_firm_name.lower() in firm.name.lower():
                        return firm
                
                return None
                
            except RoblexLawFirmUser.DoesNotExist:
                return None
                
        except Exception as e:
            # Log the error for debugging but don't crash
            return None
    
    user_law_firm = get_user_law_firm(request)
    
    # Filter querysets based on user's law firm
    if request.user.is_superuser:
        submissions = DocumentSubmission.objects.all()
        recipients = RetainerRecipient.objects.all()
        uploads = ExcelUpload.objects.all()
        law_firms = LawFirm.objects.all()
    else:
        if user_law_firm:
            submissions = DocumentSubmission.objects.filter(recipient__excel_upload__law_firm=user_law_firm)
            recipients = RetainerRecipient.objects.filter(excel_upload__law_firm=user_law_firm)
            uploads = ExcelUpload.objects.filter(law_firm=user_law_firm)
            law_firms = LawFirm.objects.none()
        else:
            submissions = DocumentSubmission.objects.none()
            recipients = RetainerRecipient.objects.none()
            uploads = ExcelUpload.objects.none()
            law_firms = LawFirm.objects.none()
    
    # Calculate statistics
    total_submissions = submissions.count()
    total_recipients = recipients.count()
    total_uploads = uploads.count()
    total_law_firms = law_firms.count() if request.user.is_superuser else 0
    
    # Calculate success rate
    completed_submissions = submissions.filter(status='completed').count()
    success_rate = round((completed_submissions / total_submissions * 100) if total_submissions > 0 else 0, 1)
    
    # Document submission status cards
    submission_status_cards = []
    status_colors = {
        'pending': {'color': '#6c757d', 'icon': '⏳'},
        'sent': {'color': '#17a2b8', 'icon': '📤'},
        'opened': {'color': '#6f42c1', 'icon': '👁️'},
        'completed': {'color': '#28a745', 'icon': '✅'},
        'declined': {'color': '#dc3545', 'icon': '❌'},
        'expired': {'color': '#ffc107', 'icon': '⏰'}
    }
    
    for status, details in status_colors.items():
        count = submissions.filter(status=status).count()
        submission_status_cards.append({
            'title': status.replace('_', ' ').title(),
            'count': count,
            'color': details['color'],
            'icon': details['icon']
        })
    
    # Recipient status cards
    recipient_status_cards = []
    recipient_status_colors = {
        'pending': {'color': '#6c757d', 'icon': '⏳'},
        'submitted': {'color': '#17a2b8', 'icon': '📝'},
        'completed': {'color': '#28a745', 'icon': '✅'},
        'failed': {'color': '#dc3545', 'icon': '❌'},
        'skipped': {'color': '#ffc107', 'icon': '⏭️'}
    }
    
    for status, details in recipient_status_colors.items():
        count = recipients.filter(status=status).count()
        recipient_status_cards.append({
            'title': status.replace('_', ' ').title(),
            'count': count,
            'color': details['color'],
            'icon': details['icon']
        })
    
    # Upload status cards
    upload_status_cards = []
    upload_status_colors = {
        'uploaded': {'color': '#6c757d', 'icon': '📁'},
        'processing': {'color': '#ffc107', 'icon': '⚙️'},
        'completed': {'color': '#28a745', 'icon': '✅'},
        'failed': {'color': '#dc3545', 'icon': '❌'}
    }
    
    for status, details in upload_status_colors.items():
        count = uploads.filter(status=status).count()
        upload_status_cards.append({
            'title': status.replace('_', ' ').title(),
            'count': count,
            'color': details['color'],
            'icon': details['icon']
        })
    
    # Recent activity
    recent_submissions = submissions.order_by('-created_at')[:5]
    recent_uploads = uploads.order_by('-created_at')[:5]
    
    context = {
        'title': 'Retainer Dashboard',
        'user_law_firm': user_law_firm,
        'is_superuser': request.user.is_superuser,
        'total_submissions': total_submissions,
        'total_recipients': total_recipients,
        'total_uploads': total_uploads,
        'total_law_firms': total_law_firms,
        'success_rate': success_rate,
        'submission_status_cards': submission_status_cards,
        'recipient_status_cards': recipient_status_cards,
        'upload_status_cards': upload_status_cards,
        'recent_submissions': recent_submissions,
        'recent_uploads': recent_uploads,
        # Django admin context
        'site_header': admin.site.site_header,
        'site_title': admin.site.site_title,
        'index_title': admin.site.index_title,
        'available_apps': admin.site.get_app_list(request),
        'has_permission': True,
    }
    
    return TemplateResponse(request, 'admin/retainer_dashboard.html', context)
