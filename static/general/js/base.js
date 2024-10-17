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

const csrftoken = getCookie('csrftoken')  // Получаем CSRF-токен из cookies


function initializeFavoriteButtons() {
    // Обработчик для добавления в избранное
    document.querySelectorAll('.add-to-cart').forEach(function (button) {
        button.addEventListener('click', function (event) {
            event.preventDefault()
            const heartRedIconURL = '/static/general/icons/heart_red.png'
            const heartIconURL = '/static/general/icons/heart.svg'
            const eventSlug = this.getAttribute('data-event-slug')
            const icon = this.querySelector('.heart-icon')
            const button = this

            fetch(`/bookmarks/events_add/${eventSlug}/`, {
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
                        icon.src = heartRedIconURL
                        button.classList.remove('add-to-cart')
                        button.classList.add('remove-from-favorites')
                        button.setAttribute('data-event-id', data.event_id)
                        showNotification("Добавлено в избранное")
                    } else {
                        icon.src = heartIconURL
                        button.classList.remove('remove-from-favorites')
                        button.classList.add('add-to-cart')
                        button.removeAttribute('data-event-id')
                        showNotification("Удалено из избранного")
                    }
                })
                .catch(error => console.error('Error:', error))
        })
    })

    // Обработчик для удаления из избранного
    document.querySelectorAll('.remove-from-favorites').forEach(function (button) {
        button.addEventListener('click', function (event) {
            event.preventDefault()
            const eventId = this.getAttribute('data-event-id')
            const buttonElement = this
            const icon = this.querySelector('.heart-icon')
            const heartIconURL = '/static/general/icons/heart.svg'

            fetch(`/bookmarks/events_remove/${eventId}/`, {
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
                        icon.src = heartIconURL
                        buttonElement.classList.remove('remove-from-favorites')
                        buttonElement.classList.add('add-to-cart')
                        buttonElement.removeAttribute('data-event-id')
                        showNotification("Удалено из избранного")
                    } else {
                        console.error('Ошибка:', data.error)
                    }
                })
                .catch(error => console.error('Ошибка:', error))
        })
    })
}

function showNotification(message) {
    const notification = document.getElementById('favoriteNotification')
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
    initializeFavoriteButtons()
})

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
    const eventUnId = this.getAttribute('data-event-unique-id')
    const buttonElement = this

    fetch(`/bookmarks/events_registered/${eventUnId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({ 'id': eventUnId })

    })
        .then(response => response.json())
        .then(data => {
            if (data.added) {
                buttonElement.classList.remove('btn-danger', 'btn-sent_app')
                buttonElement.classList.add('btn-light', 'btn-remove_app')
                buttonElement.innerHTML = 'Отмена регистрации'
                buttonElement.setAttribute('data-event-id', data.event_id)
                buttonElement.removeAttribute('data-event-slug')

                // Обновляем количество свободных мест
                // Обновите количество свободных мест
                const freePlacesElement = document.getElementById(`free-places-${data.event_slug}`)
                if (freePlacesElement) {
                    freePlacesElement.textContent = data.place_free  // Обновляем свободные места
                }

                showRegistrationNotification("Зарегистрировано")
                initializeRegistrationButtons()
            } else {
                console.error('Ошибка при регистрации:', data.error)
            }
        })
        .catch(error => console.error('Error:', error))
}


function handleUnregister(event) {
    event.preventDefault()
    const eventId = this.getAttribute('data-event-unique-id')
    const buttonElement = this

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
                buttonElement.classList.remove('btn-light', 'btn-remove_app')
                buttonElement.classList.add('btn-danger', 'btn-sent_app')
                buttonElement.innerHTML = 'Регистрация'
                buttonElement.setAttribute('data-event-slug', data.event_slug)
                buttonElement.removeAttribute('data-event-id')

                // Обновите количество свободных мест
                const freePlacesElement = document.getElementById(`free-places-${data.event_slug}`)
                if (freePlacesElement) {
                    freePlacesElement.textContent = data.place_free  // Обновляем свободные места
                }

                showRegistrationNotification("Регистрация отменена")
                initializeRegistrationButtons()
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


document.addEventListener('DOMContentLoaded', function () {
    // Обработка кнопки "Оставить отзыв"
    document.querySelectorAll('.btn-comment').forEach(function (button) {
        button.addEventListener('click', function () {
            const eventId = this.getAttribute('data-event-id')
            const modelType = this.getAttribute('data-model-type')
            document.getElementById('eventId').value = eventId
            document.getElementById('modelType').value = modelType
            const modal = new bootstrap.Modal(document.getElementById('commentModal'))
            modal.show()
        })
    })

    // Обработка отправки формы отзыва
    document.getElementById('commentForm').addEventListener('submit', function (event) {
        event.preventDefault()
        const formData = new FormData(this)
        const csrftoken = getCookie('csrftoken')
        const eventId = document.getElementById('eventId').value
        const modelType = document.getElementById('modelType').value

        let url = ''
        if (modelType === 'offline' || modelType === 'online') {
            url = `/events_available/submit_review/${eventId}/`
        } else {
            url = `/events_cultural/submit_review/${eventId}/`
        }

        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            },
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification(`Отзыв добавлен: ${data.formatted_date}`)
                    document.getElementById('commentForm').reset()
                    const modal = bootstrap.Modal.getInstance(document.getElementById('commentModal'))
                    modal.hide()

                    // Вызов функции для добавления нового отзыва в правильный блок
                    addReviewToPage(eventId, data.review, data.formatted_date)

                } else {
                    showNotification(data.message, true)
                }
            })
            .catch(error => console.error('Error:', error))
    })

    // Функция получения CSRF-токена
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

    // Функция показа уведомления
    function showNotification(message, isError = false) {
        const notification = document.getElementById('reviewNotification')
        notification.querySelector('p').textContent = message
        notification.style.display = 'block'
        notification.style.backgroundColor = isError ? '#f44336' : '#4caf50'
        setTimeout(() => {
            notification.classList.add('fade-in')
        }, 10)

        setTimeout(function () {
            notification.classList.remove('fade-in')
            notification.classList.add('fade-out')

            setTimeout(function () {
                notification.style.display = 'none'
                notification.classList.remove('fade-out')
            }, 500)
        }, 2000)
    }

    // Функция добавления нового отзыва на страницу в правильный блок
    function addReviewToPage(eventId, review, formattedDate) {
        const reviewList = document.querySelector(`.reviews[data-event-id="${eventId}"] ul`)
        if (!reviewList) {
            // Если списка отзывов еще нет, создаем его
            const reviewsDiv = document.querySelector(`.reviews[data-event-id="${eventId}"]`)
            const ul = document.createElement('ul')
            reviewsDiv.appendChild(ul)
        }

        const newReview = document.createElement('li')
        newReview.innerHTML = `
            <h5>Отзыв:</h5>
            <p><strong>${review.user.last_name} ${review.user.first_name}</strong> (${formattedDate}):</p>
            <p>${review.comment}</p>
        `
        reviewList.appendChild(newReview)
    }
})



// Скрипты с дочерних шаблонов

// {% comment %} ФОРМАТ ВВОДА ДАТЫ {% endcomment %}
document.addEventListener('DOMContentLoaded', function () {
    flatpickr("#date_start", {
        dateFormat: "d/m/Y",  // Формат отображения
    })
    flatpickr("#date_end", {
        dateFormat: "d/m/Y",  // Формат отображения
    })
})

// {% comment %} ПОСИК В СПИКЕРАХ {% endcomment %}

document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('search-speakers')
    const speakerItems = document.querySelectorAll('.speaker-item')

    searchInput.addEventListener('input', function () {
        const searchQuery = searchInput.value.toLowerCase()

        speakerItems.forEach(function (item) {
            const speakerName = item.textContent.toLowerCase()

            if (speakerName.includes(searchQuery)) {
                item.style.display = 'block'  // Показываем, если совпадает
            } else {
                item.style.display = 'none'   // Скрываем, если нет совпадений
            }
        })
    })
})

// {% comment %} ПОИСК В ТЕГАХ {% endcomment %}
document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('search-tags')
    const tagItems = document.querySelectorAll('#tags-list .tag-item')

    // Функция для фильтрации тегов
    searchInput.addEventListener('input', function () {
        const filter = searchInput.value.toLowerCase()

        tagItems.forEach(function (item) {
            const label = item.querySelector('label').textContent.toLowerCase()

            if (label.includes(filter)) {
                item.style.display = ''
            } else {
                item.style.display = 'none'
            }
        })
    })
})


// {% comment %} Фильтры и сортировка: {% endcomment %}
document.addEventListener('DOMContentLoaded', function () {
    const sortToggle = document.getElementById('sort-toggle')
    const sortSection = document.getElementById('sort-section')
    const filterToggle = document.getElementById('filter-toggle')
    const filterSection = document.getElementById('filter-section')
    const resetFiltersContainer = document.getElementById('reset-filters-container')

    const queryString = new URLSearchParams(window.location.search)

    const filtersApplied = queryString.has('q') ||
        queryString.has('name_search') ||
        queryString.has('date_start') ||
        queryString.has('date_end') ||
        queryString.has('f_speakers') ||
        queryString.has('f_tags') ||
        queryString.has('time_to_start') ||
        queryString.has('time_to_end')
    const sortApplied = queryString.has('order_by')

    if (filtersApplied || sortApplied) {
        resetFiltersContainer.style.display = 'block'
    } else {
        resetFiltersContainer.style.display = 'none'
    }

    if (filtersApplied) {
        filterSection.style.display = 'flex'
    } else {
        filterSection.style.display = 'none'
    }

    sortToggle.addEventListener('click', function () {
        if (sortSection.style.display === 'none' || sortSection.style.display === '') {
            sortSection.style.display = 'block'
        } else {
            sortSection.style.display = 'none'
        }
    })

    filterToggle.addEventListener('click', function () {
        if (filterSection.style.display === 'none' || filterSection.style.display === '') {
            filterSection.style.display = 'flex'
        } else {
            filterSection.style.display = 'none'
        }
    })
})


//{% comment %} Обработка взаимодействия с календарем: {% endcomment %}
document.addEventListener('DOMContentLoaded', function () {
    const flatpickrContainers = document.querySelectorAll('.flatpickr-calendar')

    document.addEventListener('click', function (event) {
        const isCalendarClick = Array.from(flatpickrContainers).some(container =>
            container.contains(event.target) ||
            event.target.closest('.flatpickr-prev-month') ||
            event.target.closest('.flatpickr-next-month')
        )

        const sortToggle = document.getElementById('sort-toggle')
        const sortSection = document.getElementById('sort-section')

        if (!sortToggle.contains(event.target) && !sortSection.contains(event.target) && !isCalendarClick) {
            sortSection.style.display = 'none'
        }
    })

    document.querySelectorAll('.flatpickr-calendar').forEach(function (calendar) {
        calendar.addEventListener('click', function (event) {
            if (!event.target.classList.contains('flatpickr-prev-month') &&
                !event.target.classList.contains('flatpickr-next-month')) {
                event.stopPropagation()
            }
        })
    })
})