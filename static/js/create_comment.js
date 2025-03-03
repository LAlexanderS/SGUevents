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