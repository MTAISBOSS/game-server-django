from .models import Player

class DeviceBackend:
    def authenticate(self, request, device_id=None, **kwargs):
        if not device_id:
            return None
        try:
            return Player.objects.get(device_id=device_id)
        except Player.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return Player.objects.get(pk=user_id)
        except Player.DoesNotExist:
            return None
