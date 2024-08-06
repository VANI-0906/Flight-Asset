import json
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now
from .models import APIUsageLog
from django.conf import settings
from rest_framework.authtoken.models import Token
 
class APILogMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        user = None
 
        # Handle token-based authentication
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Token '):
            token_key = auth_header.split(' ')[1]
            try:
                token = Token.objects.get(key=token_key)
                user = token.user
            except Token.DoesNotExist:
                pass
 
        # Handle session-based authentication
        if request.user.is_authenticated:
            user = request.user
 
        APIUsageLog.objects.create(
            user=user,
            endpoint=request.path,
            method=request.method,
            status_code=response.status_code,
            request_data=json.dumps(request.data) if hasattr(request, 'data') else '',
            response_data=response.content.decode() if hasattr(response, 'content') else '',
            timestamp=now()
        )
 
        return response