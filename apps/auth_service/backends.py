from .models import Player


class AdminBackend:
    """
    Authenticates dashboard admin users by username + password.
    Used by Django's session-based login (the web dashboard).
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
        try:
            # Allow login by username field OR by UUID
            player = Player.objects.get(username=username)
            if player.check_password(password) and (player.is_staff or player.role == 'admin'):
                return player
        except Player.DoesNotExist:
            pass
        return None

    def get_user(self, user_id):
        try:
            return Player.objects.get(pk=user_id)
        except Player.DoesNotExist:
            return None


class DeviceBackend:
    """
    Authenticates game players by device_id.
    Used programmatically — not for the dashboard.
    """
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
