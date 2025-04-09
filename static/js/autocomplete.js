document.addEventListener('DOMContentLoaded', function () {
    const input = document.getElementById('event-name-search')
    const resultsContainer = document.getElementById('autocomplete-results')
    const form = input.closest('form')

    input.addEventListener('input', function () {
        const query = input.value.trim()

        // ===== 🧠 Определяем контекст категории из URL =====
        const url = window.location.href
        let fetchURL = ''
        let queryParams = ''

        if (url.includes('/online') || url.includes('/offline')) {
            // Доступные мероприятия (events_available)
            const isOnline = url.includes('/online')
            fetchURL = '/events_available/autocomplete/event-name/'
            queryParams = `term=${encodeURIComponent(query)}&is_online=${isOnline}`
        } else if (url.includes('/attractions') || url.includes('/events_for_visiting')) {
            // Культурные мероприятия (events_cultural)
            const isAttractions = url.includes('/attractions')
            fetchURL = '/events_cultural/autocomplete/event-name/'
            queryParams = `term=${encodeURIComponent(query)}&is_attractions=${isAttractions}`
        } else {
            // Непонятный тип страницы — выходим
            return
        }

        // ===== 🚀 Запрос на автокомплит =====
        if (query.length < 2) {
            resultsContainer.innerHTML = ''
            return
        }

        fetch(`${fetchURL}?${queryParams}`)
            .then(response => response.json())
            .then(data => {
                resultsContainer.innerHTML = ''

                if (data.length === 0) {
                    resultsContainer.innerHTML = '<div class="autocomplete-item">Нет совпадений</div>'
                    return
                }

                data.forEach(name => {
                    const item = document.createElement('div')
                    item.classList.add('autocomplete-item')
                    item.textContent = name

                    item.addEventListener('mousedown', function () {
                        input.value = name
                        resultsContainer.innerHTML = ''

                        // Вызов setNameFilter из filters_selected_script.js
                        if (typeof setNameFilter === 'function') {
                            setNameFilter()
                        }

                        setTimeout(() => {
                            form.submit()
                        }, 100)
                    })

                    resultsContainer.appendChild(item)
                })
            })
            .catch(error => {
                console.error('Ошибка при автокомплите:', error)
            })
    })

    // Закрытие подсказок при клике вне input/результатов
    document.addEventListener('click', function (e) {
        if (!input.contains(e.target) && !resultsContainer.contains(e.target)) {
            resultsContainer.innerHTML = ''
        }
    })

    resultsContainer.addEventListener('mousedown', function (e) {
        e.stopPropagation()
    })
})
