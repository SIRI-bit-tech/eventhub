from pyuploadcare.dj.storage import UploadCareStorage

class EventFileStorage(UploadCareStorage):
    """
    Custom Uploadcare storage class for event files.
    This can be extended with custom behaviors if needed.
    
    Usage example in models:
    image = models.ImageField(storage=EventFileStorage(), blank=True, null=True)
    """
    pass
