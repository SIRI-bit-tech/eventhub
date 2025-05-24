from django.conf import settings

def site_url(request):
    """
    Add the site URL to the context for use in templates
    """
    return {'site_url': settings.SITE_URL}

def uploadcare_public_key(request):
    """
    Add the Uploadcare public key to the context for use in templates
    """
    # Access the pub_key directly from settings.UPLOADCARE dictionary
    return {'UPLOADCARE_PUBLIC_KEY': settings.UPLOADCARE.get('pub_key', '')}