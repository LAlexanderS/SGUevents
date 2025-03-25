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

// Всплывающее уведомление
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

// Обработка кликов на кнопки избранного
document.addEventListener('click', function (event) {
    const button = event.target.closest('.card-add-to-favorites, .card-remove-from-favorites')
    if (!button) return

    event.preventDefault()

    console.log('Клик по кнопке избранного:', button)

    const heartRedIconURL = '/static/icons/heart_red.png'
    const heartIconURL = '/static/icons/heart_blue.svg'
    const heartIcon = button.querySelector('.heart-icon')
    const heartRedIcon = button.querySelector('.heart-red-icon-card')

    // ДОБАВИТЬ В ИЗБРАННОЕ
    if (button.classList.contains('card-add-to-favorites')) {
        const eventSlug = button.getAttribute('data-event-slug')
        if (!eventSlug || !heartIcon) return

        console.log(`Добавляем в избранное событие с slug: ${eventSlug}`)

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
                console.log('Ответ от сервера на добавление в избранное:', data)
                if (data.added) {
                    if (heartIcon) heartIcon.src = heartRedIconURL
                    button.classList.remove('card-add-to-favorites')
                    button.classList.add('card-remove-from-favorites')
                    button.setAttribute('data-event-id', data.event_id)
                    localStorage.setItem(`event-${eventSlug}`, 'liked')
                    showNotification("Добавлено в избранное")

                    if (heartIcon && heartRedIcon) {
                        heartIcon.classList.add('hidden')
                        heartRedIcon.classList.remove('hidden')
                    }
                } else {
                    console.log('Ошибка: не удалось добавить в избранное', data.error)
                }
            })
            .catch(error => console.error('Ошибка добавления в избранное:', error))

        // УДАЛИТЬ ИЗ ИЗБРАННОГО
    } else if (button.classList.contains('card-remove-from-favorites')) {
        const eventId = button.getAttribute('data-event-id')
        const eventSlug = button.getAttribute('data-event-slug')
        if (!eventId || !heartIcon) return

        console.log(`Удаляем из избранного событие с id: ${eventId}`)

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
                console.log('Ответ от сервера на удаление из избранного:', data)
                if (data.removed) {
                    if (heartIcon) heartIcon.src = heartIconURL
                    button.classList.remove('card-remove-from-favorites')
                    button.classList.add('card-add-to-favorites')
                    button.removeAttribute('data-event-id')
                    localStorage.removeItem(`event-${eventSlug}`)
                    showNotification("Удалено из избранного")

                    if (heartIcon && heartRedIcon) {
                        heartIcon.classList.remove('hidden')
                        heartRedIcon.classList.add('hidden')
                    }
                } else {
                    console.log('Ошибка: не удалось удалить из избранного', data.error)
                }
            })
            .catch(error => console.error('Ошибка удаления из избранного:', error))
    }
})
