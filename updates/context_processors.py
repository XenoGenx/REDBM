from .constants import DEPARTMENTS


def site_context(request):
    return {'departments': DEPARTMENTS}