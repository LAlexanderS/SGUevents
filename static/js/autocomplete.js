// Фильтр по названию
document.addEventListener('DOMContentLoaded', function () {
    const input = document.getElementById('event-name-search')
    const resultsContainer = document.getElementById('autocomplete-results')
    const form = input.closest('form')

    input.addEventListener('input', function () {
        const query = input.value.trim()

        //  контекст категории из URL 
        const url = window.location.href
        let fetchURL = ''
        let queryParams = ''

        if (url.includes('/online') || url.includes('/offline')) {
            // events_available
            const isOnline = url.includes('/online')
            fetchURL = '/events_available/autocomplete/event-name/'
            queryParams = `term=${encodeURIComponent(query)}&is_online=${isOnline}`
        } else if (url.includes('/attractions') || url.includes('/events_for_visiting')) {
            // events_cultural
            const isAttractions = url.includes('/attractions')
            fetchURL = '/events_cultural/autocomplete/event-name/'
            queryParams = `term=${encodeURIComponent(query)}&is_attractions=${isAttractions}`
        } else {
            return
        }

        // Запрос на автокомплит
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

    // Закрытие при клике вне input/результатов
    document.addEventListener('click', function (e) {
        if (!input.contains(e.target) && !resultsContainer.contains(e.target)) {
            resultsContainer.innerHTML = ''
        }
    })

    resultsContainer.addEventListener('mousedown', function (e) {
        e.stopPropagation()
    })
})


// Фильтр по месту проведения (адресу)
document.addEventListener('DOMContentLoaded', function () {
    const input = document.getElementById('event-place-search')
    const resultsContainer = document.getElementById('place-autocomplete-results')
    const form = document.getElementById('place-form')

    if (input) {
        input.addEventListener('input', function () {
            const query = input.value.trim()

            if (query.length < 2) {
                resultsContainer.innerHTML = ''
                return
            }

            fetch(`/events_available/autocomplete/places/?term=${encodeURIComponent(query)}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })

                .then(response => response.json())
                .then(data => {
                    resultsContainer.innerHTML = ''

                    if (data.length === 0) {
                        resultsContainer.innerHTML = '<div class="autocomplete-item">Ничего не найдено</div>'
                        return
                    }

                    data.forEach(place => {
                        const item = document.createElement('div')
                        item.classList.add('autocomplete-item')
                        item.textContent = place
                        item.addEventListener('mousedown', function (e) {
                            e.preventDefault()
                            input.value = place
                            resultsContainer.innerHTML = ''
                            localStorage.setItem('filterPlace', place)

                            if (typeof setPlaceFilter === 'function') {
                                setPlaceFilter()
                            }

                            setTimeout(() => {
                                form.submit()
                            }, 100)
                        })
                        resultsContainer.appendChild(item)
                    })
                })
                .catch(error => {
                    console.error('Ошибка при автокомплите мест:', error)
                })
        })

        // Очистка автокомплита при клике вне
        document.addEventListener('click', function (e) {
            if (!input.contains(e.target)) {
                resultsContainer.innerHTML = ''
            }
        })
    }
})

