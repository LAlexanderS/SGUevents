from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .telegram_utils import send_message_to_user, send_custom_notification_with_toggle
from events_available.models import Events_online, Events_offline
from events_cultural.models import Attractions, Events_for_visiting
from bookmarks.models import Registered
from .models import SupportRequest, AdminRightRequest
import logging
from users.middleware import CurrentUserMiddleware
import threading

logger = logging.getLogger(__name__)

# Потоково-локальное хранилище для хранения старого экземпляра
_thread_locals = threading.local()

def get_old_instance():
    return getattr(_thread_locals, 'old_instance', None)

@receiver(pre_save, sender=Events_online)
@receiver(pre_save, sender=Events_offline)
@receiver(pre_save, sender=Attractions)
@receiver(pre_save, sender=Events_for_visiting)
def store_old_instance(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            old = None
    else:
        old = None
    _thread_locals.old_instance = old

def has_field_changed(old_instance, new_instance, field_name):
    """
    Проверяет, изменилось ли указанное поле между старым и новым экземплярами.
    """
    if old_instance is None:
        # Объект только создаётся, изменения полей нет
        return False
    old_value = getattr(old_instance, field_name)
    new_value = getattr(new_instance, field_name)
    return old_value != new_value

# Уведомление автора о любых изменениях
@receiver(post_save, sender=Events_online)
@receiver(post_save, sender=Events_offline)
@receiver(post_save, sender=Attractions)
@receiver(post_save, sender=Events_for_visiting)
def notify_author_on_any_change(sender, instance, created, **kwargs):
    if created:
        # Если объект только создаётся, возможно, отправлять уведомление или нет
        logger.info(f"Создан новый объект {sender.__name__} с ID {instance.pk}")
        return

    user = CurrentUserMiddleware.get_current_user()

    # Проверяем, что текущий пользователь - это администратор или суперпользователь
    if not user or not (user.is_staff or user.is_superuser):
        logger.info(f"Изменения не требуют уведомления для пользователя {user.username if user else 'None'}")
        return

    # Исключаем уведомления при изменении участников (регистрация/отмена регистрации), количества мест и свободных мест
    updated_fields = kwargs.get('update_fields', None)
    if updated_fields and any(field in updated_fields for field in ['member', 'place_limit', 'place_free']):
        logger.info(f"Изменение полей {updated_fields} мероприятия {instance.name} не требует уведомления.")
        return

    # Уведомление автора о любых изменениях
    if user and hasattr(user, 'telegram_id') and user.telegram_id:
        message = f"\U0001F4BE Изменения в мероприятие '{instance.name}' были успешно сохранены."
        try:
            send_message_to_user(user.telegram_id, message)
            logger.info(f"Уведомление об изменениях отправлено пользователю {user.username}")
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления автору {user.username}: {e}")
    else:
        logger.warning("Пользователь, который вносит изменения, не был найден или у него нет telegram_id")
# Уведомление участников при изменении определённых полей
@receiver(post_save, sender=Events_online)
@receiver(post_save, sender=Events_offline)
@receiver(post_save, sender=Attractions)
@receiver(post_save, sender=Events_for_visiting)
def notify_participants_on_specific_field_change(sender, instance, created, **kwargs):
    if created:
        # Если объект только создаётся, уведомлять участников не нужно
        return

    old_instance = get_old_instance()
    if not old_instance:
        logger.warning(f"Не удалось найти старый экземпляр для {sender.__name__} с ID {instance.pk}")
        return

    # Укажите здесь поля, при изменении которых необходимо отправлять уведомления участникам
    fields_to_watch = ['start_datetime']  # Добавьте другие поля по необходимости

    fields_changed = [field for field in fields_to_watch if has_field_changed(old_instance, instance, field)]

    if not fields_changed:
        # Если ни одно из отслеживаемых полей не изменилось, не отправляем уведомления участникам
        logger.info(f"Изменений в отслеживаемых полях для {sender.__name__} с ID {instance.pk} не обнаружено.")
        return

    # Уведомление участников
    registered_users = Registered.objects.filter(
        online=instance if isinstance(instance, Events_online) else None,
        offline=instance if isinstance(instance, Events_offline) else None,
        attractions=instance if isinstance(instance, Attractions) else None,
        for_visiting=instance if isinstance(instance, Events_for_visiting) else None
    )

    for registration in registered_users:
        if registration.user.telegram_id:
            # Формируем сообщение в зависимости от изменённых полей
            messages = []
            for field in fields_changed:
                if field == 'start_datetime':
                    messages.append(
                        f"Изменилось время начала мероприятия '{instance.name}'. Новое время: {instance.start_datetime.strftime('%d.%m.%Y %H:%M')}."
                    )
                # Добавьте обработку других полей по необходимости

            # Объединяем сообщения
            message = " ".join(messages) if messages else f"Изменились детали мероприятия '{instance.name}'."

            try:
                send_custom_notification_with_toggle(
                    registration.user.telegram_id, message, instance.unique_id, registration.notifications_enabled
                )
                logger.info(f"Уведомление отправлено пользователю {registration.user.username}")
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления пользователю {registration.user.username}: {e}")
        else:
            logger.warning(f"У пользователя {registration.user.username} нет telegram_id")

@receiver(post_save, sender=SupportRequest)
def notify_user_on_support_request_update(sender, instance, created, **kwargs):
    if not created:
        # Проверяем, что запрос был помечен как решённый и имеет ответ
        if instance.is_resolved and instance.answer:
            user = instance.user
            if user.telegram_id:
                message = (
                    f"Здравствуйте, {user.first_name}!\n\n"
                    f"Получен ответ от технической поддержки\n\n"
                    f"**Ваш вопрос:** {instance.question}\n\n"
                    f"**Ответ:** {instance.answer}"
                )
                try:
                    send_message_to_user(user.telegram_id, message)
                    logger.info(f"Сообщение отправлено пользователю {user.username} (Telegram ID: {user.telegram_id})")
                except Exception as e:
                    logger.error(f"Ошибка при отправке сообщения пользователю {user.username}: {e}")
            else:
                logger.warning(f"У пользователя {user.username} отсутствует Telegram ID.")

@receiver(post_save, sender=AdminRightRequest)
def notify_user_on_admin_right_request_update(sender, instance, created, **kwargs):
    if not created:
        # Проверяем, что статус изменился на 'granted' или 'denied' и есть ответ
        if instance.status in ['granted', 'denied'] and instance.response:
            user = instance.user
            if user.telegram_id:
                status_message = 'одобрен' if instance.status == 'granted' else 'отклонён'
                message = (
                    f"Здравствуйте, {user.first_name}!\n\n"
                    f"Ваш запрос на админские права был {status_message}.\n\n"
                    f"**Ответ от техподдержки:** {instance.response}"
                )
                try:
                    send_message_to_user(user.telegram_id, message)
                    logger.info(
                        f"Сообщение отправлено пользователю {user.username} (Telegram ID: {user.telegram_id}) по запросу на админские права.")
                except Exception as e:
                    logger.error(
                        f"Ошибка при отправке сообщения пользователю {user.username} (Telegram ID: {user.telegram_id}): {e}")
            else:
                logger.warning(
                    f"У пользователя {user.username} отсутствует Telegram ID. Невозможно отправить уведомление.")
