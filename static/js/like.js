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

window.csrftoken = getCookie('csrftoken')

function showNotification(message) {
    const notification = document.getElementById('favoriteNotification')
    if (!notification) return

    const messageElement = notification.querySelector('p')
    if (messageElement) {
        messageElement.textContent = message
    }

    notification.style.display = 'block'
    setTimeout(() => notification.classList.add('fade-in'), 10)
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

    const heartIcon = button.querySelector('.heart-icon')
    const heartRedIcon = button.querySelector('.heart-red-icon')
    const eventSlug = button.getAttribute('data-event-slug')
    const eventId = button.getAttribute('data-event-id')

    // ДОБАВИТЬ В ИЗБРАННОЕ
    if (button.classList.contains('add-to-cart')) {
        if (!eventSlug) return

        fetch(`/bookmarks/events_add/${eventSlug}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrftoken
            },
            body: JSON.stringify({ slug: eventSlug })
        })
            .then(response => response.json())
            .then(data => {
                if (data.added) {
                    if (heartIcon && heartRedIcon) {
                        heartIcon.classList.add('hidden')
                        heartRedIcon.classList.remove('hidden')
                    } else {
                        if (heartIcon) {
                            heartIcon.classList.add('hidden')
                            const redIcon = document.createElement('img')
                            redIcon.src = '/static/icons/heart_red.png'
                            redIcon.alt = 'Красное сердце'
                            redIcon.width = 32
                            redIcon.height = 32
                            redIcon.className = 'heart-red-icon'
                            heartIcon.after(redIcon)
                        }
                    }

                    button.classList.remove('add-to-cart')
                    button.classList.add('remove-from-favorites')
                    button.setAttribute('data-event-id', data.event_id)
                    showNotification("Добавлено в избранное")
                }
            })
            .catch(error => console.error('Ошибка добавления в избранное:', error))

        // УДАЛИТЬ ИЗ ИЗБРАННОГО
    } else if (button.classList.contains('remove-from-favorites')) {
        if (!eventSlug) return

        fetch(`/bookmarks/events_remove/${eventSlug}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrftoken
            },
            body: JSON.stringify({ slug: eventSlug })
        })
            .then(response => response.json())
            .then(data => {
                if (data.removed) {
                    if (heartIcon && heartRedIcon) {
                        heartIcon.classList.remove('hidden')
                        heartRedIcon.classList.add('hidden')
                    }
                    button.classList.remove('remove-from-favorites')
                    button.classList.add('add-to-cart')
                    button.removeAttribute('data-event-id')
                    showNotification("Удалено из избранного")
                }
            })
            .catch(error => console.error('Ошибка удаления из избранного:', error))
    }

})