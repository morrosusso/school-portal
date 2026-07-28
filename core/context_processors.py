from django.conf import settings


def school_info(request):
    """Makes school name/motto/session available in every template without repeating queries."""
    return {
        "SCHOOL_NAME": settings.SCHOOL_NAME,
        "SCHOOL_MOTTO": settings.SCHOOL_MOTTO,
        "CURRENT_SESSION": settings.CURRENT_SESSION,
    }
