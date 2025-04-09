document.addEventListener('DOMContentLoaded', function () {
    const input = document.getElementById('event-name-search')
    const resultsContainer = document.getElementById('autocomplete-results')
    const form = input.closest('form')

    // Обработка ввода
    input.addEventListener('input', function () {
        const query = input.value.trim()
        const isOnline = window.location.href.includes('online')

        if (query.length < 2) {
            resultsContainer.innerHTML = ''
            return
        }

        fetch(`/events_available/autocomplete/event-name/?term=${encodeURIComponent(query)}&is_online=${isOnline}`)
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

                    // Используем mousedown и setTimeout, чтобы не конфликтовать с закрытием dropdown
                    item.addEventListener('mousedown', function () {
                        input.value = name
                        resultsContainer.innerHTML = ''

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

    // Закрытие подсказок при клике вне input
    document.addEventListener('click', function (e) {
        if (!input.contains(e.target) && !resultsContainer.contains(e.target)) {
            resultsContainer.innerHTML = ''
        }
    })

    // Не закрываем dropdown при клике по результатам
    resultsContainer.addEventListener('mousedown', function (e) {
        e.stopPropagation()
    })
})
