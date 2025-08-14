from django.db.models.signals import post_save, pre_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from .telegram_utils import send_message_to_user, send_custom_notification_with_toggle
from events_available.models import Events_online, Events_offline, EventOfflineCheckList
from events_cultural.models import Attractions, Events_for_visiting
from bookmarks.models import Registered
from .models import SupportRequest, AdminRightRequest, User
import logging
from users.middleware import CurrentUserMiddleware
import threading
from django.utils import timezone

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
            from users.telegram_utils import get_event_url, create_event_hyperlink
            
            # Создаем гиперссылку для мероприятия
            event_url = get_event_url(instance)
            event_hyperlink = create_event_hyperlink(instance.name, event_url)
            
            # Формируем сообщение в зависимости от изменённых полей
            messages = []
            for field in fields_changed:
                if field == 'start_datetime':
                    messages.append(
                        f"Изменилось время начала мероприятия {event_hyperlink}. Новое время: {instance.start_datetime.strftime('%d.%m.%Y %H:%M')}."
                    )
                # Добавьте обработку других полей по необходимости

            # Объединяем сообщения
            message = " ".join(messages) if messages else f"Изменились детали мероприятия {event_hyperlink}."

            try:
                send_custom_notification_with_toggle(
                    registration.user.telegram_id, message, instance.unique_id, registration.notifications_enabled
                )
                logger.info(f"Уведомление отправлено пользователю {registration.user.username}")
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления пользователю {registration.user.username}: {e}")
        else:
            logger.warning(f"У пользователя {registration.user.username} нет telegram_id")

# ====== Чек-лист задач по офлайн-мероприятию ======

def _set_old_checklist(instance):
    try:
        old = EventOfflineCheckList.objects.get(pk=instance.pk)
    except EventOfflineCheckList.DoesNotExist:
        old = None
    _thread_locals.old_checklist = old


def _get_old_checklist():
    return getattr(_thread_locals, 'old_checklist', None)


def _is_valid_chat_id(chat_id):
    try:
        s = str(chat_id).strip()
        if not s:
            return False
        s = s.lstrip('-')
        return s.isdigit()
    except Exception:
        return False


@receiver(pre_save, sender=EventOfflineCheckList)
def store_old_checklist(sender, instance, **kwargs):
    if instance.pk:
        _set_old_checklist(instance)
    else:
        _thread_locals.old_checklist = None

@receiver(post_save, sender=EventOfflineCheckList)
def notify_task_assignee(sender, instance, created, **kwargs):
    from users.telegram_utils import send_message_to_telegram, get_event_url, create_event_hyperlink
    try:
        responsible = instance.responsible
        if not responsible:
            return
        if not responsible.telegram_id:
            return
        if not _is_valid_chat_id(responsible.telegram_id):
            return

        old = _get_old_checklist()

        should_notify = False
        reasons = []
        if created:
            should_notify = True
            reasons.append('создана и назначена вам')
        else:
            if old and old.responsible != instance.responsible:
                should_notify = True
                reasons.append('назначена вам')
            if old and old.planned_date != instance.planned_date:
                should_notify = True
                reasons.append('обновлён срок')
        if not should_notify:
            return

        event = instance.event
        event_url = get_event_url(event)
        event_link = create_event_hyperlink(event.name, event_url)
        task_name = str(instance.task_name) if instance.task_name else 'Задача'
        deadline = instance.planned_date.strftime('%d.%m.%Y') if instance.planned_date else 'не указан'
        message = (
            f"\U0001F4CB Вам назначена задача: <b>{task_name}</b>\n"
            f"Мероприятие: {event_link}\n"
            f"Срок: {deadline}\n"
            f"Статус: {'выполнено' if instance.completed else 'в работе'}\n"
            f"Причина уведомления: {', '.join(reasons)}"
        )
        send_message_to_telegram(responsible.telegram_id, message)
        logger.info(f"Отправлено уведомление о задаче '{task_name}' пользователю {responsible.username}")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления по чек-лист задаче: {e}")

# ====== Чек-лист: оповещение в чат поддержки при завершении ======
@receiver(post_save, sender=EventOfflineCheckList)
def notify_support_on_task_completion(sender, instance, created, **kwargs):
    try:
        # интересует только смена на completed=True
        if not instance.completed:
            return
        event = instance.event
        # только офлайн мероприятия с заданным чатом поддержки
        support_chat_id = getattr(event, 'support_chat_id', None)
        if not support_chat_id:
            return
        task_name = str(instance.task_name) if instance.task_name else 'Задача'
        executor = str(instance.responsible) if instance.responsible else '—'
        done_date = (instance.actual_date.strftime('%d.%m.%Y') if instance.actual_date else timezone.now().strftime('%d.%m.%Y'))
        text = (
            f"✅ Задача \"{task_name}\"\n"
            f"Исполнитель: {executor}\n"
            f"По мероприятию: {event.name}\n"
            f"Отмечена выполненной {done_date}"
        )
        from users.telegram_utils import send_text_to_chat
        send_text_to_chat(support_chat_id, text, parse_html=False)
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления в чат поддержки о завершении задачи: {e}")

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

@receiver(post_save, sender=User)
def assign_staff_view_permissions(sender, instance, created, **kwargs):
    """Автоматически выдаём права на просмотр модели User когда пользователь становится staff"""
    logger.info(f'Сигнал post_save для пользователя {instance.username}: is_staff={instance.is_staff}, is_superuser={instance.is_superuser}, created={created}')
    
    if instance.is_staff and not instance.is_superuser:
        try:
            # Создаем или получаем группу Staff
            staff_group, group_created = Group.objects.get_or_create(name='Staff')
            if group_created:
                logger.info('Создана группа Staff')
            
            # Добавляем пользователя в группу Staff
            if not instance.groups.filter(name='Staff').exists():
                instance.groups.add(staff_group)
                logger.info(f'Пользователь {instance.username} добавлен в группу Staff')
            
            content_type = ContentType.objects.get_for_model(User)
            
            # Выдаем право на просмотр пользователей
            view_permission, perm_created = Permission.objects.get_or_create(
                codename='view_user',
                name='Can view user',
                content_type=content_type,
            )
            logger.info(f'Permission view_user: существует={not perm_created}, id={view_permission.id}')
            
            # Добавляем право в группу
            if not staff_group.permissions.filter(id=view_permission.id).exists():
                staff_group.permissions.add(view_permission)
                logger.info(f'Право view_user добавлено в группу Staff')
            
            # Также добавляем право напрямую пользователю (на всякий случай)
            has_permission = instance.user_permissions.filter(id=view_permission.id).exists()
            logger.info(f'Пользователь {instance.username} уже имеет право view_user: {has_permission}')
            
            if not has_permission:
                instance.user_permissions.add(view_permission)
                logger.info(f'✅ Выдано право view_user пользователю {instance.username}')
            else:
                logger.info(f'ℹ️ Пользователь {instance.username} уже имеет право view_user')
                
        except Exception as e:
            logger.error(f'❌ Ошибка при выдаче прав пользователю {instance.username}: {e}')
    else:
        logger.info(f'Пользователь {instance.username} не подходит под условия (is_staff={instance.is_staff}, is_superuser={instance.is_superuser})')

# ====== Автосоздание Registered при добавлении участника в админке (member m2m) ======

def _notify_registered_user(user: User, event_obj, event_type: str, registered_obj: Registered):
    try:
        if not user.telegram_id:
            return
        from users.telegram_utils import get_event_url, create_event_hyperlink, send_message_to_user_with_toggle_button
        event_url = get_event_url(event_obj)
        event_hyperlink = create_event_hyperlink(event_obj.name, event_url)
        message = f"✅ Вы зарегистрированы на мероприятие: {event_hyperlink}."
        chat_url = None
        if event_type in ('online', 'offline'):
            try:
                if getattr(event_obj, 'users_chat_id', None) and getattr(event_obj, 'users_chat_link', None):
                    chat_url = event_obj.users_chat_link
            except AttributeError:
                chat_url = None
        send_message_to_user_with_toggle_button = send_message_to_user_with_toggle_button  # noqa: F821
        send_message_to_user_with_toggle_button(
            user.telegram_id,
            message,
            registered_obj.id,
            registered_obj.notifications_enabled,
            chat_url=chat_url
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления о регистрации пользователю {user.username}: {e}")


def _ensure_registered(user_id: int, event_obj, event_type: str):
    try:
        user = User.objects.get(id=user_id)
        created = False
        reg = None
        if event_type == 'online':
            reg, created = Registered.objects.get_or_create(user=user, online=event_obj)
        elif event_type == 'offline':
            reg, created = Registered.objects.get_or_create(user=user, offline=event_obj)
        elif event_type == 'attractions':
            reg, created = Registered.objects.get_or_create(user=user, attractions=event_obj)
        elif event_type == 'for_visiting':
            reg, created = Registered.objects.get_or_create(user=user, for_visiting=event_obj)
        if created:
            _notify_registered_user(user, event_obj, event_type, reg)
    except User.DoesNotExist:
        pass
    except Exception as e:
        logger.error(f"Ошибка создания Registered: {e}")


@receiver(m2m_changed, sender=Events_online.member.through)
def sync_registered_on_online_member(sender, instance: Events_online, action, pk_set, **kwargs):
    if action == 'post_add' and pk_set:
        for user_id in pk_set:
            _ensure_registered(user_id, instance, 'online')

@receiver(m2m_changed, sender=Events_offline.member.through)
def sync_registered_on_offline_member(sender, instance: Events_offline, action, pk_set, **kwargs):
    if action == 'post_add' and pk_set:
        for user_id in pk_set:
            _ensure_registered(user_id, instance, 'offline')

@receiver(m2m_changed, sender=Attractions.member.through)
def sync_registered_on_attractions_member(sender, instance: Attractions, action, pk_set, **kwargs):
    if action == 'post_add' and pk_set:
        for user_id in pk_set:
            _ensure_registered(user_id, instance, 'attractions')

@receiver(m2m_changed, sender=Events_for_visiting.member.through)
def sync_registered_on_visiting_member(sender, instance: Events_for_visiting, action, pk_set, **kwargs):
    if action == 'post_add' and pk_set:
        for user_id in pk_set:
            _ensure_registered(user_id, instance, 'for_visiting')
