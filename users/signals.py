from django.db.models.signals import post_save
from django.dispatch import receiver
from .telegram_utils import send_message_to_user, send_custom_notification_with_toggle
from events_available.models import Events_online, Events_offline
from events_cultural.models import Attractions, Events_for_visiting
from bookmarks.models import Registered
from .models import SupportRequest, AdminRightRequest
import logging
from users.middleware import CurrentUserMiddleware

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Events_online)
@receiver(post_save, sender=Events_offline)
@receiver(post_save, sender=Attractions)
@receiver(post_save, sender=Events_for_visiting)
def notify_author_and_participants_on_event_update(sender, instance, **kwargs):
    user = CurrentUserMiddleware.get_current_user()

    # Уведомление автора
    if user and hasattr(user, 'telegram_id') and user.telegram_id:
        message = f"\U0001F4BE Изменения в мероприятие '{instance.name}' были успешно сохранены."
        send_message_to_user(user.telegram_id, message)
        logger.info(f"Уведомление об изменениях отправлено пользователю {user.username}")
    else:
        logger.warning("Пользователь, который вносит изменения, не был найден или у него нет telegram_id")

    # Уведомление участников
    registered_users = Registered.objects.filter(
        online=instance if isinstance(instance, Events_online) else None,
        offline=instance if isinstance(instance, Events_offline) else None,
        attractions=instance if isinstance(instance, Attractions) else None,
        for_visiting=instance if isinstance(instance, Events_for_visiting) else None
    )

    old_instance = sender.objects.filter(pk=instance.pk).first()

    for registration in registered_users:
        if registration.user.telegram_id:
            # Проверка, изменилось ли время начала мероприятия
            if old_instance and old_instance.start_datetime != instance.start_datetime:
                message = f"Изменилось время начала мероприятия '{instance.name}'. Новое время: {instance.start_datetime.strftime('%d.%m.%Y %H:%M')}."
            else:
                # Всегда включаем время в сообщение, даже если оно не изменилось
                message = f"Изменились детали мероприятия '{instance.name}'. Текущее время начала: {instance.start_datetime.strftime('%d.%m.%Y %H:%M')}."

            send_custom_notification_with_toggle(
                registration.user.telegram_id, message, instance.unique_id, registration.notifications_enabled
            )
        else:
            logger.warning(f"У пользователя {registration.user.username} нет telegram_id")

def send_update_notification(user, event, new_start_time):
    message = f"Изменились детали мероприятия: дата и время начала изменилось на {new_start_time.strftime('%d.%m.%Y %H:%M')}."
    user_telegram_id = user.telegram_id

    # Проверка наличия и корректности Telegram ID
    if user_telegram_id and len(user_telegram_id) > 0:
        try:
            logger.info(f"Пробуем отправить уведомление пользователю {user.username} с telegram_id: {user_telegram_id}")
            response = send_custom_notification_with_toggle(user_telegram_id, message, event.unique_id, True)
            if not response.ok:
                logger.error(f"Ошибка отправки сообщения пользователю с telegram_id {user_telegram_id}: {response.text}")
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения пользователю с telegram_id {user_telegram_id}: {e}")
    else:
        logger.warning(f"У пользователя {user.username} нет корректного telegram_id, пропускаем отправку.")

def handle_event_update(event_model, instance):
    if not instance.pk:
        return

    try:
        old_instance = event_model.objects.get(pk=instance.pk)
    except event_model.DoesNotExist:
        return

    # Проверяем, изменилось ли время начала мероприятия
    if old_instance.start_datetime != instance.start_datetime:
        registered_users = Registered.objects.filter(
            online=instance if isinstance(instance, Events_online) else None,
            offline=instance if isinstance(instance, Events_offline) else None,
            attractions=instance if isinstance(instance, Attractions) else None,
            for_visiting=instance if isinstance(instance, Events_for_visiting) else None
        )

        for registration in registered_users:
            send_update_notification(registration.user, instance, instance.start_datetime)

# Обработчик для всех типов событий
@receiver(post_save, sender=Events_online)
@receiver(post_save, sender=Events_offline)
@receiver(post_save, sender=Attractions)
@receiver(post_save, sender=Events_for_visiting)
def handle_event_update_signal(sender, instance, **kwargs):
    handle_event_update(sender, instance)

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
                status_message = 'одобрен' if instance.status == 'granted' else 'отклонен'
                message = (
                    f"Здравствуйте, {user.first_name}!\n\n"
                    f"Ваш запрос на админские права был {status_message}.\n\n"
                    f"**Ответ от техподдержки:** {instance.response}"
                )
                try:
                    send_message_to_user(user.telegram_id, message)
                    logger.info(f"Сообщение отправлено пользователю {user.username} (Telegram ID: {user.telegram_id}) по запросу на админские права.")
                except Exception as e:
                    logger.error(f"Ошибка при отправке сообщения пользователю {user.username} (Telegram ID: {user.telegram_id}): {e}")
            else:
                logger.warning(f"У пользователя {user.username} отсутствует Telegram ID. Невозможно отправить уведомление.")
