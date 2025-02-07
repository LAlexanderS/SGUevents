document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('event-name-search');
    const resultsContainer = document.getElementById('autocomplete-results');
    const form = input.closest('form');  

    input.addEventListener('input', function() {
        const query = input.value;

        // Определяем, находимся ли мы на странице оффлайн или онлайн мероприятий
        const isOnline = window.location.pathname.includes('online'); // Определяем по URL

        if (query.length >= 2) {  // Автокомплит начинает работать после ввода двух символов
            fetch(`/events_available/autocomplete/event-name/?term=${query}&is_online=${isOnline}`)
                .then(response => response.json())
                .then(data => {
                    resultsContainer.innerHTML = '';  // Очищаем старые результаты
                    if (data.length === 0) {
                        resultsContainer.innerHTML = '<div class="autocomplete-item">No results found</div>';
                    } else {
                        data.forEach(eventName => {
                            const option = document.createElement('div');
                            option.classList.add('autocomplete-item');
                            option.innerHTML = eventName;
                            option.addEventListener('click', function() {
                                input.value = eventName;  // При выборе названия заполняем поле
                                resultsContainer.innerHTML = '';  // Очищаем результаты
                                form.submit();  // Автоматически отправляем форму
                            });
                            resultsContainer.appendChild(option);
                        });
                    }
                });
        } else {
            resultsContainer.innerHTML = '';  // Если меньше двух символов, очищаем результаты
        }
    });
});