// Получаем CSRF-токен из cookies (глобально один раз)
function getCookie(name) {
    let cookieValue = null
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';')
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim()
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
                break
            }
        }
    }
    return cookieValue
}

window.csrftoken = getCookie('csrftoken')  // Объявляем глобально, чтобы не было конфликта между скриптами

// всплывающее уведомление
function showNotification(message) {
    const notification = document.getElementById('favoriteNotification')
    if (!notification) return

    const messageElement = notification.querySelector('p')
    if (messageElement) {
        messageElement.textContent = message
    }

    notification.style.display = 'block'
    setTimeout(() => {
        notification.classList.add('fade-in')
    }, 10)

    setTimeout(() => {
        notification.classList.remove('fade-in')
        notification.classList.add('fade-out')
        setTimeout(() => {
            notification.style.display = 'none'
            notification.classList.remove('fade-out')
        }, 700)
    }, 1000)
}

document.addEventListener('click', function (event) {
    const button = event.target.closest('.add-to-cart, .remove-from-favorites')
    if (!button) return

    event.preventDefault()

    const heartRedIconURL = '/static/icons/heart_red.png'
    const heartIconURL = '/static/icons/heart.svg'
    const icon = button.querySelector('.heart-icon')

    // ДОБАВИТЬ В ИЗБРАННОЕ
    if (button.classList.contains('add-to-cart')) {
        const eventSlug = button.getAttribute('data-event-slug')
        if (!eventSlug || !icon) return

        fetch(`/bookmarks/events_add/${eventSlug}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrftoken
            },
            body: JSON.stringify({ 'slug': eventSlug })
        })
            .then(response => response.json())
            .then(data => {
                if (data.added) {
                    icon.src = heartRedIconURL
                    button.classList.remove('add-to-cart')
                    button.classList.add('remove-from-favorites')
                    button.setAttribute('data-event-id', data.event_id)
                    localStorage.setItem(`event-${eventSlug}`, 'liked')
                    showNotification("Добавлено в избранное")
                }
            })
            .catch(error => console.error('Ошибка добавления в избранное:', error))

        // УДАЛИТЬ ИЗ ИЗБРАННОГО
    } else if (button.classList.contains('remove-from-favorites')) {
        const eventId = button.getAttribute('data-event-id')
        const eventSlug = button.getAttribute('data-event-slug')
        if (!eventId || !icon) return

        fetch(`/bookmarks/events_remove/${eventId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrftoken
            },
            body: JSON.stringify({ 'id': eventId })
        })
            .then(response => response.json())
            .then(data => {
                if (data.removed) {
                    icon.src = heartIconURL
                    button.classList.remove('remove-from-favorites')
                    button.classList.add('add-to-cart')
                    button.removeAttribute('data-event-id')
                    localStorage.removeItem(`event-${eventSlug}`)
                    showNotification("Удалено из избранного")
                }
            })
            .catch(error => console.error('Ошибка удаления из избранного:', error))
    }
})
