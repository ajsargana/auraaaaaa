"""
CORS Middleware – replaces Flask's @app.after_request CORS handler.
Handles OPTIONS preflight requests directly so browsers/WebViews
receive a 200 instead of a 405 Method Not Allowed.
"""
from django.http import HttpResponse

_CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-CSRFToken',
    'Access-Control-Allow-Methods': 'GET, PUT, POST, DELETE, OPTIONS, PATCH',
    'Access-Control-Max-Age': '86400',
}


class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Return immediately for preflight requests
        if request.method == 'OPTIONS':
            response = HttpResponse(status=200)
            for key, value in _CORS_HEADERS.items():
                response[key] = value
            return response

        response = self.get_response(request)
        for key, value in _CORS_HEADERS.items():
            response[key] = value
        return response
