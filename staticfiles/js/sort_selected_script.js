function setSortFilter() {
    // Получаем элементы для отображения выбранного значения и сообщения
    const filterValueSpan = document.getElementById('filter-sort-value')
    const filterSortMessageDiv = document.getElementById('filter-sort-message')

    // Получаем выбранный радио-элемент сортировки
    const selectedSortRadio = document.querySelector('input[name="order_by"]:checked')

    if (!selectedSortRadio) {
        // Если вообще ничего не выбрано, просто скрываем фильтр
        filterValueSpan.textContent = ''
        filterSortMessageDiv.classList.add('hidden')
        localStorage.removeItem('filterSortBy')
        return
    }

    let displayValue

    switch (selectedSortRadio.value) {
        case "default":
            // Если выбрано "default", чистим сортировку
            filterValueSpan.textContent = ''
            filterSortMessageDiv.classList.add('hidden')
            localStorage.removeItem('filterSortBy')
            // Очищаем скрытые input'ы в форме (если есть)
            const hiddenInputs = document.querySelectorAll('#sort-form input[type="hidden"]')
            hiddenInputs.forEach(input => input.value = '')
            // Отправляем форму без сортировки
            document.getElementById('sort-form').submit()
            return
        case "time_start":
            displayValue = "Раньше"
            break
        case "-time_start":
            displayValue = "Позже"
            break
        case "date":
            displayValue = "Сначала старые"
            break
        case "-date":
            displayValue = "Сначала новые"
            break
        default:
            displayValue = "Неизвестная сортировка"
    }

    filterValueSpan.textContent = displayValue
    filterSortMessageDiv.classList.remove('hidden')

    localStorage.setItem('filterSortBy', selectedSortRadio.value)
    document.getElementById('sort-form').submit()
}


function clearSortFilter() {
    // Получаем все радио-кнопки и элементы для отображения
    const radioButtons = document.querySelectorAll('input[name="order_by"]')
    const filterValueSpan = document.getElementById('filter-sort-value')
    const filterMessageDiv = document.getElementById('filter-sort-message')

    // Сбрасываем выбор на сортировку по умолчанию
    radioButtons.forEach(radio => radio.checked = radio.id === 'sort-time-default')

    // Очищаем текст и скрываем сообщение
    filterValueSpan.textContent = ''
    filterMessageDiv.classList.add('hidden')

    // Удаляем сохраненную сортировку из localStorage и отправляем форму
    localStorage.removeItem('filterSortBy')
    document.getElementById('sort-form').submit()
}

// Назначаем обработчики событий для кнопок "Применить" и "Сбросить"
document.getElementById('apply-sort-button').addEventListener('click', setSortFilter)
document.getElementById('delete-sort-filter').addEventListener('click', clearSortFilter)