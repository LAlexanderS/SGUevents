from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class TelegramAuthBackend(BaseBackend):
    def authenticate(self, request, telegram_id=None):
        if telegram_id is None:
            return None
            
        try:
            user = User.objects.get(telegram_id=telegram_id)
            return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None 