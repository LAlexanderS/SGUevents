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

const csrftoken = getCookie('csrftoken')


function initializeRegistrationButtons() {
    document.querySelectorAll('.btn-sent_app').forEach(function (button) {
        button.removeEventListener('click', handleRegister)
        button.addEventListener('click', handleRegister)
    })

    document.querySelectorAll('.btn-remove_app').forEach(function (button) {
        button.removeEventListener('click', handleUnregister)
        button.addEventListener('click', handleUnregister)
    })
}

function handleRegister(event) {
    event.preventDefault()
    const eventSlug = this.getAttribute('data-event-slug')
    const buttonElement = this
    const card = buttonElement.closest('.card')

    fetch(`/bookmarks/events_registered/${eventSlug}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({ 'slug': eventSlug })
    })
        .then(response => response.json())
        .then(data => {
            if (data.added) {
                // Создаём кнопку "Отмена регистрации"
                const removeAppButton = document.createElement('a')
                removeAppButton.href = "#"
                removeAppButton.classList.add('btn', 'btn-remove_app')
                removeAppButton.setAttribute('data-event-id', data.event_id)
                removeAppButton.innerText = 'Отмена регистрации'

                // Назначаем обработчик
                removeAppButton.addEventListener('click', handleUnregister)

                // Меняем кнопку "Регистрация" на "Отмена регистрации"
                buttonElement.replaceWith(removeAppButton)

                // Сохраняем состояние в localStorage
                localStorage.setItem(`event-${eventSlug}-app`, 'sent')

                // Обновляем количество свободных мест
                const freePlacesElement = document.getElementById(`free-places-${data.event_slug}`)
                if (freePlacesElement) {
                    freePlacesElement.textContent = data.place_free
                }

                const freePlacesElementMobile = document.getElementById(`free-places-mobile-${data.event_slug}`)
                if (freePlacesElement) {
                    freePlacesElementMobile.textContent = data.place_free
                }

                showRegistrationNotification("Зарегистрировано")
            } else {
                console.error('Ошибка при регистрации:', data.error)
            }
        })
        .catch(error => console.error('Error:', error))
}


function handleUnregister(event) {
    event.preventDefault()
    const eventId = this.getAttribute('data-event-id')
    const buttonElement = this
    const card = buttonElement.closest('.card')

    fetch(`/bookmarks/registered_remove/${eventId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({ 'id': eventId })
    })
        .then(response => response.json())
        .then(data => {
            if (data.removed) {
                // Создаём кнопку "Регистрация"
                const sentAppButton = document.createElement('a')
                sentAppButton.href = "#"
                sentAppButton.classList.add('btn', 'btn-sent_app', 'card-button')
                sentAppButton.setAttribute('data-event-slug', data.event_slug)
                sentAppButton.innerText = 'Регистрация'

                // Назначаем обработчик
                sentAppButton.addEventListener('click', handleRegister)

                // Меняем кнопку "Отмена регистрации" обратно на "Регистрация"
                buttonElement.replaceWith(sentAppButton)

                // Удаляем запись из localStorage
                localStorage.removeItem(`event-${data.event_slug}-app`)

                // Обновляем количество свободных мест
                const freePlacesElement = document.getElementById(`free-places-${data.event_slug}`)
                if (freePlacesElement) {
                    freePlacesElement.textContent = data.place_free
                }

                const freePlacesElementMobile = document.getElementById(`free-places-mobile-${data.event_slug}`)
                if (freePlacesElement) {
                    freePlacesElementMobile.textContent = data.place_free
                }

                showRegistrationNotification("Регистрация отменена")
            } else {
                console.error('Ошибка при отмене регистрации:', data.error)
            }
        })
        .catch(error => console.error('Ошибка:', error))
}




function showRegistrationNotification(message) {
    const notification = document.getElementById('registrationNotification')
    notification.querySelector('p').textContent = message
    notification.style.display = 'block'
    setTimeout(() => {
        notification.classList.add('fade-in')
    }, 10)

    setTimeout(function () {
        notification.classList.remove('fade-in')
        notification.classList.add('fade-out')

        setTimeout(function () {
            notification.style.display = 'none'
            notification.classList.remove('fade-out')
        }, 700)
    }, 1000)
}

document.addEventListener('DOMContentLoaded', function () {
    initializeRegistrationButtons()
})

// document.addEventListener('click', function (event) {
//     // Обработка кнопок "Отправить заявку" и "Удалить заявку"
//     if (event.target.closest('.btn-sent_app')) {
//         const card = event.target.closest('.card')
//         const sentAppButton = card.querySelector('.btn-sent_app')
//         const removeAppButton = card.querySelector('.btn-remove_app')

//         sentAppButton.classList.add('hidden')
//         removeAppButton.classList.remove('hidden')
//         localStorage.setItem(`event-${card.dataset.eventSlug}-app`, 'sent')
//     } else if (event.target.closest('.btn-remove_app')) {
//         const card = event.target.closest('.card')
//         const sentAppButton = card.querySelector('.btn-sent_app')
//         const removeAppButton = card.querySelector('.btn-remove_app')

//         removeAppButton.classList.add('hidden')
//         sentAppButton.classList.remove('hidden')
//         localStorage.removeItem(`event-${card.dataset.eventSlug}-app`)
//     }

//     // Обработка добавления/удаления из избранного
//     const targetElement = event.target.closest('.add-to-cart, .remove-from-favorites')

//     if (!targetElement) {
//         return // Если клик не по нужному элементу, выходим
//     }

//     event.preventDefault() // Предотвращаем стандартное поведение ссылки

//     const heartIcon = targetElement.querySelector('.heart-icon')
//     const heartRedIcon = targetElement.querySelector('.heart-red-icon')
//     const eventSlug = targetElement.dataset.eventSlug // Уникальный идентификатор

//     if (targetElement.classList.contains('add-to-cart')) {
//         // Логика добавления в избранное
//         heartIcon.classList.add('hidden')
//         heartRedIcon.classList.remove('hidden')

//         targetElement.classList.remove('add-to-cart')
//         targetElement.classList.add('remove-from-favorites')
//         // Сохраняем состояние в localStorage
//         localStorage.setItem(`event-${eventSlug}`, 'liked')

//     } else if (targetElement.classList.contains('remove-from-favorites')) {
//         // Логика удаления из избранного
//         heartIcon.classList.remove('hidden')
//         heartRedIcon.classList.add('hidden')

//         targetElement.classList.remove('remove-from-favorites')
//         targetElement.classList.add('add-to-cart')
//         // Удаляем состояние из localStorage
//         localStorage.removeItem(`event-${eventSlug}`)
//     }
// })

// document.addEventListener('DOMContentLoaded', function () {
//     const cards = document.querySelectorAll('.card')

//     cards.forEach(card => {
//         const eventSlug = card.dataset.eventSlug // Уникальный идентификатор
//         const sentAppButton = card.querySelector('.btn-sent_app')
//         const removeAppButton = card.querySelector('.btn-remove_app')
//         const isAppSent = localStorage.getItem(`event-${eventSlug}-app`) === 'sent'

//         if (isAppSent) {
//             // Если заявка была отправлена, применяем соответствующие изменения
//             sentAppButton.classList.add('hidden')
//             removeAppButton.classList.remove('hidden')
//         } else {
//             // Если заявка не была отправлена, сбрасываем состояние
//             sentAppButton.classList.remove('hidden')
//             removeAppButton.classList.add('hidden')
//         }

//         const heartElement = card.querySelector('[data-event-slug]')
//         if (heartElement) {
//             const heartIcon = heartElement.querySelector('.heart-icon')
//             const heartRedIcon = heartElement.querySelector('.heart-red-icon')
//             const isLiked = localStorage.getItem(`event-${eventSlug}`) === 'liked'

//             if (isLiked) {
//                 // Если элемент был "лайкнут", применяем соответствующие изменения
//                 heartIcon.classList.add('hidden')
//                 heartRedIcon.classList.remove('hidden')
//                 heartElement.classList.remove('add-to-cart')
//                 heartElement.classList.add('remove-from-favorites')
//             } else {
//                 // Если элемент не был "лайкнут", сбрасываем состояние
//                 heartIcon.classList.remove('hidden')
//                 heartRedIcon.classList.add('hidden')
//                 heartElement.classList.remove('remove-from-favorites')
//                 heartElement.classList.add('add-to-cart')
//             }
//         }
//     })
// })