from .utils import AccessControlWithUser
from .settings import SUPER_USER_ID, DEFAULT_USER_ID


class AccessControlMiddleware(object):
    """
    This middleware gets current user from `HttpRequest`,
    which is applied throughout the whole running of the programme.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user

        if user.is_superuser:
            user = SUPER_USER_ID
        elif not user.is_authenticated:
            user = DEFAULT_USER_ID

        with AccessControlWithUser(user):
            response = self.get_response(request)

        return response
