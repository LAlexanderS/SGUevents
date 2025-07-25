document.addEventListener('DOMContentLoaded', function () {
    initializeRegistrationButtons()

    // Обработка кнопки "Оставить отзыв"
    document.querySelectorAll('.btn-comment').forEach(function (button) {
        button.addEventListener('click', function () {
            const eventId = this.getAttribute('data-event-id')

            const modelType = this.getAttribute('data-model-type')
            console.log('data-event-id', eventId)
            console.log('data-model-type', modelType)



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
        console.log('ID log ', eventId)

        let url = ''
        if (modelType === 'offline' || modelType === 'online') {
            url = `/events_available/submit_review/${eventId}/`
        } else {
            url = `/events_cultural/submit_review/${eventId}/`
        }
        console.log('URL log ', url)

        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            },
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                console.log('[DEBUG] Ответ от сервера:', data)

                if (data.success) {
                    showNotification(`Отзыв добавлен: ${data.formatted_date}`)
                    document.getElementById('commentForm').reset()

                    const modal = bootstrap.Modal.getInstance(document.getElementById('commentModal'))
                    if (modal) modal.hide()
                    // Удаляем backdrop Bootstrap
                    document.querySelectorAll('.modal-backdrop').forEach(el => el.remove())
                    // Убираем класс show и display у всех модалок
                    document.querySelectorAll('.modal').forEach(el => {
                        el.classList.remove('show')
                        el.style.display = 'none'
                    })
                    // Убираем overlay, если есть
                    const overlay = document.getElementById('overlay')
                    if (overlay) overlay.style.display = 'none'
                    // Убираем modal-open с body
                    document.body.classList.remove('modal-open')

                    addReviewToAppropriateBlock(eventId, data.review, data.formatted_date)

                    // 1. Обновляем средний рейтинг
                    const ratingText = document.querySelector(`.rating-overlay[data-event-id="${eventId}"] .ranting-count`)
                    console.log('OAOAOOAOAOOAOAOAOOAO', ratingText)
                    console.log('ZZZZZZZZZZZZZZZZZZZZ', data.new_avg)

                    if (ratingText && data.new_avg) {
                        ratingText.innerText = parseFloat(data.new_avg).toFixed(1).replace('.', ',')
                    }

                    // 2. Перекрашиваем звёзды
                    updateStarsForEvent(eventId)

                } else {
                    showNotification(data.message, true)
                }
            })
            .catch(error => console.error('[ERROR] Отправка отзыва:', error))
    })

    // Получение CSRF-токена
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

    // Уведомление
    function showNotification(message, isError = false) {
        const notification = document.getElementById('reviewNotification')
        if (!notification) return

        notification.querySelector('p').textContent = message
        notification.style.display = 'block'
        notification.style.backgroundColor = isError ? '#f44336' : '#4caf50'
        setTimeout(() => {
            notification.classList.add('fade-in')
        }, 10)

        setTimeout(() => {
            notification.classList.remove('fade-in')
            notification.classList.add('fade-out')
            setTimeout(() => {
                notification.style.display = 'none'
                notification.classList.remove('fade-out')
            }, 500)
        }, 2000)
    }

    // Универсальная обёртка
    function addReviewToAppropriateBlock(eventId, review, formattedDate) {
        const reviewsBlock = document.querySelector(`.reviews[data-event-id="${eventId}"]`)
        if (reviewsBlock) {
            addReviewToPage(eventId, review, formattedDate)
        }

        const cardBlock = document.querySelector('.items')
        if (cardBlock) {
            addReviewToCardPage(eventId, review, formattedDate)
        }

        addReviewToMobile(review)
    }

    // Добавление отзыва на главной
    function addReviewToPage(eventId, review, formattedDate) {
        let reviewsDiv = document.querySelector(`.reviews[data-event-id="${eventId}"]`)
        if (!reviewsDiv) {
            console.warn('[DEBUG] Контейнер отзывов не найден для eventId:', eventId)
            return
        }

        const newReview = document.createElement('div')
        newReview.classList.add('existent-comment')

        // путь к аватарке
        const profilePhotoUrl = review.profile_photo
        newReview.innerHTML = `
                                                            <div class="existent-review">
                                                                <div class="user-info-existent-review">
                                                                    <div class="user-icon-existent-review"> 
                                                                        <img src="${profilePhotoUrl}" alt="">
                                                                    </div>
                                 
                                                                    <div class="username-existent-review">
                                                                        <div class="user-lastname">${review.user.username}</div>
                                                                    </div>
                                                                    <div class="full-stars-com">
                                                                        <div class="rating-group-com">
                                                                            <!-- по умолчанию 0 -->
                                                                            <input name="fst" value="0" type="radio" disabled checked />
                        
                                                                            <!-- рейтинг 1 -->
                                                                            <label for="fst-1">
                                                                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 576 512">
                                                                                    <path
                                                                                        d="M259.3 17.8L194 150.2 47.9 171.5c-26.2 3.8-36.7 36.1-17.7 54.6l105.7 103-25 145.5c-4.5 26.3 23.2 46 46.4 33.7L288 439.6l130.7 68.7c23.2 12.2 50.9-7.4 46.4-33.7l-25-145.5 105.7-103c19-18.5 8.5-50.8-17.7-54.6L382 150.2 316.7 17.8c-11.7-23.6-45.6-23.9-57.4 0z" />
                                                                                </svg>
                                                                            </label>
                                                                            <input name="fst" id="fst-1" value="1" type="radio" />
                        
                                                                            <!-- рейтинг 2 -->
                                                                            <label for="fst-2">
                                                                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 576 512">
                                                                                    <path
                                                                                        d="M259.3 17.8L194 150.2 47.9 171.5c-26.2 3.8-36.7 36.1-17.7 54.6l105.7 103-25 145.5c-4.5 26.3 23.2 46 46.4 33.7L288 439.6l130.7 68.7c23.2 12.2 50.9-7.4 46.4-33.7l-25-145.5 105.7-103c19-18.5 8.5-50.8-17.7-54.6L382 150.2 316.7 17.8c-11.7-23.6-45.6-23.9-57.4 0z" />
                                                                                </svg>
                                                                            </label>
                                                                            <input name="fst" id="fst-2" value="2" type="radio" />
                        
                                                                            <!-- рейтинг 3 -->
                                                                            <label for="fst-3">
                                                                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 576 512">
                                                                                    <path
                                                                                        d="M259.3 17.8L194 150.2 47.9 171.5c-26.2 3.8-36.7 36.1-17.7 54.6l105.7 103-25 145.5c-4.5 26.3 23.2 46 46.4 33.7L288 439.6l130.7 68.7c23.2 12.2 50.9-7.4 46.4-33.7l-25-145.5 105.7-103c19-18.5 8.5-50.8-17.7-54.6L382 150.2 316.7 17.8c-11.7-23.6-45.6-23.9-57.4 0z" />
                                                                                </svg>
                                                                            </label>
                                                                            <input name="fst" id="fst-3" value="3" type="radio" />
                        
                                                                            <!-- рейтинг 4 -->
                                                                            <label for="fst-4">
                                                                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 576 512">
                                                                                    <path
                                                                                        d="M259.3 17.8L194 150.2 47.9 171.5c-26.2 3.8-36.7 36.1-17.7 54.6l105.7 103-25 145.5c-4.5 26.3 23.2 46 46.4 33.7L288 439.6l130.7 68.7c23.2 12.2 50.9-7.4 46.4-33.7l-25-145.5 105.7-103c19-18.5 8.5-50.8-17.7-54.6L382 150.2 316.7 17.8c-11.7-23.6-45.6-23.9-57.4 0z" />
                                                                                </svg>
                                                                            </label>
                                                                            <input name="fst" id="fst-4" value="4" type="radio" />
                        
                                                                            <!-- рейтинг 5 -->
                                                                            <label for="fst-5">
                                                                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 576 512">
                                                                                    <path
                                                                                        d="M259.3 17.8L194 150.2 47.9 171.5c-26.2 3.8-36.7 36.1-17.7 54.6l105.7 103-25 145.5c-4.5 26.3 23.2 46 46.4 33.7L288 439.6l130.7 68.7c23.2 12.2 50.9-7.4 46.4-33.7l-25-145.5 105.7-103c19-18.5 8.5-50.8-17.7-54.6L382 150.2 316.7 17.8c-11.7-23.6-45.6-23.9-57.4 0z" />
                                                                                </svg>
                                                                            </label>
                                                                            <input name="fst" id="fst-5" value="5" type="radio" />
                                                                        </div>
                                                                    </div>
                                                                    <div class="review-date-submitted">
                                                                        ${getFormattedNow()}
                                                                    </div> 
                                                                </div>
                                                                <div class="review-block review-block-existent-review">
                                                                    <div class="review-text review-text-existent-review">
                                                                        ${review.comment}
                                                                    </div>
                                                                </div>
                                                            </div>   

                                                            <hr class="review-divider">     
        `
        reviewsDiv.prepend(newReview)

    }

    // Текущая дата + форматирование
    function getFormattedNow() {
        const now = new Date()

        const formatted = now.toLocaleString("ru-RU", {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).replace(',', '')

        return formatted
    }

    // Добавление отзыва в карточке мероприятия
    function addReviewToCardPage(eventId, review, formattedDate) {
        document.querySelector('.comment-title')?.style.setProperty('display', 'block')
        document.querySelector('.half-stars')?.style.setProperty('display', 'block')
        document.querySelector('.prev-reviews')?.style.setProperty('display', 'block')
        document.querySelector('.next-reviews')?.style.setProperty('display', 'block')


        const itemsDiv = document.querySelector('.items')
        if (!itemsDiv) {
            console.warn('[DEBUG] Блок .items не найден для карточки мероприятия')
            return
        }

        const itemCount = itemsDiv.querySelectorAll('.item').length + 1

        const item = document.createElement('div')
        item.classList.add('item', `item${itemCount}`)

        const now = new Date()

        // путь к аватарке
        const profilePhotoUrl = review.profile_photo

        item.innerHTML = `
            <div class="review">
                <div class="col-lg-4 user-info">
                    <div class="user-icon">
                        <img src="${profilePhotoUrl}" alt="">
                    </div>
                    <div class="username">${review.user.last_name} <br> ${review.user.first_name}</div>
                    <div class="review-date-submitted">${getFormattedNow()}</div>
                                                        <div class="full-stars-com">
                                                            <div class="rating-group-com">
                                                                <!-- по умолчанию 0 -->
                                                                <input name="fst" value="0" type="radio" disabled checked />
            
                                                                <!-- рейтинг 1 -->
                                                                <label for="fst-1">
                                                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 576 512">
                                                                        <path
                                                                            d="M259.3 17.8L194 150.2 47.9 171.5c-26.2 3.8-36.7 36.1-17.7 54.6l105.7 103-25 145.5c-4.5 26.3 23.2 46 46.4 33.7L288 439.6l130.7 68.7c23.2 12.2 50.9-7.4 46.4-33.7l-25-145.5 105.7-103c19-18.5 8.5-50.8-17.7-54.6L382 150.2 316.7 17.8c-11.7-23.6-45.6-23.9-57.4 0z" />
                                                                    </svg>
                                                                </label>
                                                                <input name="fst" id="fst-1" value="1" type="radio" />
            
                                                                <!-- рейтинг 2 -->
                                                                <label for="fst-2">
                                                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 576 512">
                                                                        <path
                                                                            d="M259.3 17.8L194 150.2 47.9 171.5c-26.2 3.8-36.7 36.1-17.7 54.6l105.7 103-25 145.5c-4.5 26.3 23.2 46 46.4 33.7L288 439.6l130.7 68.7c23.2 12.2 50.9-7.4 46.4-33.7l-25-145.5 105.7-103c19-18.5 8.5-50.8-17.7-54.6L382 150.2 316.7 17.8c-11.7-23.6-45.6-23.9-57.4 0z" />
                                                                    </svg>
                                                                </label>
                                                                <input name="fst" id="fst-2" value="2" type="radio" />
            
                                                                <!-- рейтинг 3 -->
                                                                <label for="fst-3">
                                                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 576 512">
                                                                        <path
                                                                            d="M259.3 17.8L194 150.2 47.9 171.5c-26.2 3.8-36.7 36.1-17.7 54.6l105.7 103-25 145.5c-4.5 26.3 23.2 46 46.4 33.7L288 439.6l130.7 68.7c23.2 12.2 50.9-7.4 46.4-33.7l-25-145.5 105.7-103c19-18.5 8.5-50.8-17.7-54.6L382 150.2 316.7 17.8c-11.7-23.6-45.6-23.9-57.4 0z" />
                                                                    </svg>
                                                                </label>
                                                                <input name="fst" id="fst-3" value="3" type="radio" />
            
                                                                <!-- рейтинг 4 -->
                                                                <label for="fst-4">
                                                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 576 512">
                                                                        <path
                                                                            d="M259.3 17.8L194 150.2 47.9 171.5c-26.2 3.8-36.7 36.1-17.7 54.6l105.7 103-25 145.5c-4.5 26.3 23.2 46 46.4 33.7L288 439.6l130.7 68.7c23.2 12.2 50.9-7.4 46.4-33.7l-25-145.5 105.7-103c19-18.5 8.5-50.8-17.7-54.6L382 150.2 316.7 17.8c-11.7-23.6-45.6-23.9-57.4 0z" />
                                                                    </svg>
                                                                </label>
                                                                <input name="fst" id="fst-4" value="4" type="radio" />
            
                                                                <!-- рейтинг 5 -->
                                                                <label for="fst-5">
                                                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 576 512">
                                                                        <path
                                                                            d="M259.3 17.8L194 150.2 47.9 171.5c-26.2 3.8-36.7 36.1-17.7 54.6l105.7 103-25 145.5c-4.5 26.3 23.2 46 46.4 33.7L288 439.6l130.7 68.7c23.2 12.2 50.9-7.4 46.4-33.7l-25-145.5 105.7-103c19-18.5 8.5-50.8-17.7-54.6L382 150.2 316.7 17.8c-11.7-23.6-45.6-23.9-57.4 0z" />
                                                                    </svg>
                                                                </label>
                                                                <input name="fst" id="fst-5" value="5" type="radio" />
                                                            </div>
                                                        </div>
                    
                </div>
                <div class="col-lg-8 review-block">
                    <div class="col-lg-11 review-text" style="overflow-wrap: break-word; white-space: normal;">
                        ${review.comment}
                    </div>
                </div>
            </div>
        `

        itemsDiv.prepend(item)
    }

    // Добавление отзыва в мобильную версию
    function addReviewToMobile(review) {
        document.querySelector('.comment-title')?.style.setProperty('display', 'block')
        document.querySelector('.half-stars')?.style.setProperty('display', 'block')
        document.querySelector('.prev-reviews')?.style.setProperty('display', 'block')
        document.querySelector('.next-reviews')?.style.setProperty('display', 'block')
        document.querySelector('.comments-mobile')?.style.setProperty('display', 'block')

        const mobileContainer = document.querySelector('.comments-mobile')
        if (!mobileContainer) {
            console.warn('[DEBUG] Мобильный контейнер отзывов не найден')
            return
        }

        // Отображаем блок, если он был скрыт
        mobileContainer.style.display = 'block'

        const reviewMobile = document.createElement('div')
        reviewMobile.classList.add('review-container-mobile')

        // путь к аватарке
        console.log("URL", review.user.profile_photo)
        console.log("PHOTO", review.user.profile_photo.url)

        const profilePhotoUrl = review.profile_photo

        reviewMobile.innerHTML = `
        <div class="user-info-mobile">
            <div class="user-icon-mobile">
                <img src="${profilePhotoUrl}" alt="">
            </div>
            <div class="username-mobile">${review.user.last_name} ${review.user.first_name}</div>
            <div class="review-date-submitted-mobile">${getFormattedNow()}</div> 
            
            <div class="full-stars-com">
                <div class="rating-group-com">
                                                        <!-- по умолчанию 0 -->
                                                        <input name="fst" value="0" type="radio" disabled checked />
            
                                                        <!-- рейтинг 1 -->
                                                        <label for="fst-1">
                                                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 576 512">
                                                                <path
                                                                    d="M259.3 17.8L194 150.2 47.9 171.5c-26.2 3.8-36.7 36.1-17.7 54.6l105.7 103-25 145.5c-4.5 26.3 23.2 46 46.4 33.7L288 439.6l130.7 68.7c23.2 12.2 50.9-7.4 46.4-33.7l-25-145.5 105.7-103c19-18.5 8.5-50.8-17.7-54.6L382 150.2 316.7 17.8c-11.7-23.6-45.6-23.9-57.4 0z" />
                                                            </svg>
                                                        </label>
                                                        <input name="fst" id="fst-1" value="1" type="radio" />
            
                                                        <!-- рейтинг 2 -->
                                                        <label for="fst-2">
                                                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 576 512">
                                                                <path
                                                                    d="M259.3 17.8L194 150.2 47.9 171.5c-26.2 3.8-36.7 36.1-17.7 54.6l105.7 103-25 145.5c-4.5 26.3 23.2 46 46.4 33.7L288 439.6l130.7 68.7c23.2 12.2 50.9-7.4 46.4-33.7l-25-145.5 105.7-103c19-18.5 8.5-50.8-17.7-54.6L382 150.2 316.7 17.8c-11.7-23.6-45.6-23.9-57.4 0z" />
                                                            </svg>
                                                        </label>
                                                        <input name="fst" id="fst-2" value="2" type="radio" />
            
                                                        <!-- рейтинг 3 -->
                                                        <label for="fst-3">
                                                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 576 512">
                                                                <path
                                                                    d="M259.3 17.8L194 150.2 47.9 171.5c-26.2 3.8-36.7 36.1-17.7 54.6l105.7 103-25 145.5c-4.5 26.3 23.2 46 46.4 33.7L288 439.6l130.7 68.7c23.2 12.2 50.9-7.4 46.4-33.7l-25-145.5 105.7-103c19-18.5 8.5-50.8-17.7-54.6L382 150.2 316.7 17.8c-11.7-23.6-45.6-23.9-57.4 0z" />
                                                            </svg>
                                                        </label>
                                                        <input name="fst" id="fst-3" value="3" type="radio" />
            
                                                        <!-- рейтинг 4 -->
                                                        <label for="fst-4">
                                                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 576 512">
                                                                <path
                                                                    d="M259.3 17.8L194 150.2 47.9 171.5c-26.2 3.8-36.7 36.1-17.7 54.6l105.7 103-25 145.5c-4.5 26.3 23.2 46 46.4 33.7L288 439.6l130.7 68.7c23.2 12.2 50.9-7.4 46.4-33.7l-25-145.5 105.7-103c19-18.5 8.5-50.8-17.7-54.6L382 150.2 316.7 17.8c-11.7-23.6-45.6-23.9-57.4 0z" />
                                                            </svg>
                                                        </label>
                                                        <input name="fst" id="fst-4" value="4" type="radio" />
            
                                                        <!-- рейтинг 5 -->
                                                        <label for="fst-5">
                                                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 576 512">
                                                                <path
                                                                    d="M259.3 17.8L194 150.2 47.9 171.5c-26.2 3.8-36.7 36.1-17.7 54.6l105.7 103-25 145.5c-4.5 26.3 23.2 46 46.4 33.7L288 439.6l130.7 68.7c23.2 12.2 50.9-7.4 46.4-33.7l-25-145.5 105.7-103c19-18.5 8.5-50.8-17.7-54.6L382 150.2 316.7 17.8c-11.7-23.6-45.6-23.9-57.4 0z" />
                                                            </svg>
                                                        </label>
                                                        <input name="fst" id="fst-5" value="5" type="radio" />
                                                    </div>
            </div>
        </div>
        <div class="review-content-mobile">
            <div class="review-text review-text-mobile">${review.comment}</div>
        </div>
    `

        mobileContainer.prepend(reviewMobile)
    }

})


function updateStarsForEvent(eventId) {
    const overlay = document.querySelector(`.rating-overlay[data-event-id="${eventId}"]`)
    if (!overlay) return

    const ratingText = overlay.querySelector('.ranting-count')
    if (!ratingText) return

    const rawText = ratingText.innerText.trim().replace(',', '.')
    const raw = parseFloat(rawText) || 0
    const rounded = Math.round(raw * 2) / 2

    const inputs = overlay.querySelectorAll('.rating-group input[type="radio"]')
    const labels = overlay.querySelectorAll('.rating-group label')

    labels.forEach(label => label.classList.remove('filled'))

    inputs.forEach(input => {
        const val = parseFloat(input.value)
        const label = overlay.querySelector(`label[for="${input.id}"]`)
        if (val <= rounded && label) {
            label.classList.add('filled')
        }
    })
}
