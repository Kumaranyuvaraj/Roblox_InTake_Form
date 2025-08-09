from django.http import Http404
from django.shortcuts import get_object_or_404
from roblex_app.models import LawFirm


class SubdomainMiddleware:
    """
    Middleware to detect law firm from subdomain and make it available throughout the request
    For URLs like: hilliard.roblox.nextkeylitigation.com or bullocklegal.roblox.nextkeylitigation.com
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract subdomain from the request
        host = request.get_host()
        subdomain = self.extract_subdomain(host)
        
        # Set the law firm on the request
        if subdomain:
            try:
                request.law_firm = LawFirm.objects.get(subdomain=subdomain, is_active=True)
            except LawFirm.DoesNotExist:
                # If subdomain doesn't match any law firm, use default
                try:
                    request.law_firm = LawFirm.objects.get(subdomain='default', is_active=True)
                except LawFirm.DoesNotExist:
                    # If no default either, raise 404
                    raise Http404("Law firm not found")
        else:
            # No subdomain detected, use default law firm
            try:
                request.law_firm = LawFirm.objects.get(subdomain='default', is_active=True)
            except LawFirm.DoesNotExist:
                # raise Http404("Default law firm not configured"
                pass

        response = self.get_response(request)
        return response

    def extract_subdomain(self, host):
        """
        Extract subdomain from host
        Examples:
        - hilliard.roblox.nextkeylitigation.com -> hilliard
        - bullocklegal.roblox.nextkeylitigation.com -> bullocklegal
        - roblox.nextkeylitigation.com -> None (no subdomain)
        - localhost:8000 -> None (development)
        """
        # Remove port if present
        host = host.split(':')[0]
        
        # Development/localhost handling
        if host in ['localhost', '127.0.0.1']:
            return None
            
        # Split by dots
        parts = host.split('.')
        
        # For production domains like hilliard.roblox.nextkeylitigation.com
        if len(parts) >= 3 and parts[-3:] == ['roblox', 'nextkeylitigation', 'com']:
            # If it's exactly roblox.nextkeylitigation.com (3 parts), no subdomain
            if len(parts) == 3:
                return None
            # If it's subdomain.roblox.nextkeylitigation.com (4+ parts), extract subdomain
            elif len(parts) >= 4:
                subdomain = parts[0]
                return subdomain if subdomain not in ['www'] else None
            
        # For staging/development domains like hilliard.localhost or hilliard.example.com
        if len(parts) >= 2:
            return parts[0] if parts[0] not in ['www'] else None
            
        return None


class LawFirmContextMiddleware:
    """
    Middleware to add law firm context to all templates
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_template_response(self, request, response):
        """Add law firm context to template responses"""
        if hasattr(response, 'context_data') and hasattr(request, 'law_firm'):
            if response.context_data is None:
                response.context_data = {}
            response.context_data['current_law_firm'] = request.law_firm
        return response
