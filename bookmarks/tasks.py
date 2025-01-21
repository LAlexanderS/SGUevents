from datetime import timedelta
from django.utils.timezone import localtime, now as tz_now, get_current_timezone
from celery import shared_task
from django.db.models import Q
from bookmarks.models import Registered
from users.models import User
from users.telegram_utils import send_message_to_user_with_toggle_button, send_message_to_user_with_review_buttons, send_event_notification_with_buttons
import logging

logger = logging.getLogger(__name__)

def round_to_minute(dt):
    """Округление времени до ближайшей минуты"""
    return dt.replace(second=0, microsecond=0)

@shared_task
def send_notification(event_registered_id, user_id, event_name, timeframe):
    try:
        user = User.objects.get(id=user_id)
        registered_event = Registered.objects.get(id=event_registered_id)
        if registered_event.notifications_enabled:
            message = f"\U0001F550 Напоминаем, что мероприятие '{event_name}' начнется через {timeframe}."
            if user.telegram_id:
                # Отправляем уведомление с кнопкой отмены регистрации
                send_event_notification_with_buttons(
                    user.telegram_id,
                    message,
                    event_registered_id,
                    notifications_enabled=True,
                    include_unregister_button=True
                )
            else:
                logger.warning(f"Пользователь {user.username} не имеет telegram_id, уведомление не отправлено.")
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist.")
    except Registered.DoesNotExist:
        logger.error(f"Registered event with id {event_registered_id} does not exist.")
    except Exception as e:
        logger.error(f"Error sending notification: {e}")

@shared_task
def send_review_request(event_unique_id, user_id, event_name, event_type):
    try:
        user = User.objects.get(id=user_id)
        message = f"Мероприятие '{event_name}' завершилось. Пожалуйста, оставьте отзыв."
        send_message_to_user_with_review_buttons(user.telegram_id, message, str(event_unique_id), event_type)
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist. Event Unique ID: {event_unique_id}, Event Type: {event_type}")
    except Exception as e:
        logger.error(f"Error sending review request for Event Unique ID: {event_unique_id}, Event Type: {event_type}. Exception: {e}")

def determine_event_type_and_object(registered_event):
    if registered_event.online:
        return "online", registered_event.online
    elif registered_event.offline:
        return "offline", registered_event.offline
    elif registered_event.attractions:
        return "attractions", registered_event.attractions
    elif registered_event.for_visiting:
        return "for_visiting", registered_event.for_visiting
    else:
        raise ValueError("Unknown event type")

@shared_task
def schedule_notifications():
    now = round_to_minute(localtime(tz_now()))
    current_tz = get_current_timezone()
    notification_window = timedelta(minutes=1)  # Окно для отправки уведомлений

    registered_events = Registered.objects.filter(
        Q(online__start_datetime__gte=now) |
        Q(offline__start_datetime__gte=now) |
        Q(attractions__start_datetime__gte=now) |
        Q(for_visiting__start_datetime__gte=now) |
        Q(online__end_datetime__gte=now) |  # Учитываем события, которые уже идут.
        Q(offline__end_datetime__gte=now) |
        Q(attractions__end_datetime__gte=now) |
        Q(for_visiting__end_datetime__gte=now)
    )

    for event in registered_events:
        try:
            event_type, event_obj = determine_event_type_and_object(event)
            event_name = event_obj.name

            # Временные промежутки для отправки уведомлений перед началом
            timeframes = {
                '1 день': timedelta(days=1),
                '1 час': timedelta(hours=1),
                '5 минут': timedelta(minutes=5)
            }

            # Отправляем уведомления только один раз за указанные промежутки
            for timeframe_label, delta in timeframes.items():
                notification_time = round_to_minute(event_obj.start_datetime.astimezone(current_tz) - delta)

                if now <= notification_time < now + notification_window:
                    send_notification.apply_async(
                        (event.id, event.user.id, event_name, timeframe_label),
                        eta=now + timedelta(seconds=10)
                    )

            # Если мероприятие закончится в ближайшую минуту, сразу планируем запрос на отзыв
            review_eta_time = round_to_minute(event_obj.end_datetime.astimezone(current_tz)) + timedelta(minutes=1)
            if review_eta_time > now and review_eta_time <= now + timedelta(minutes=1):
                logger.info(f"Запланирована отправка запроса на отзыв по мероприятию '{event_name}' (ID: {event_obj.unique_id}) на {review_eta_time}")
                send_review_request.apply_async(
                    (str(event_obj.unique_id), event.user.id, event_name, event_type),
                    eta=review_eta_time
                )

        except ValueError as e:
            logger.error(f"Error determining event type for event with Unique ID: {event_obj.unique_id}. Exception: {e}")
