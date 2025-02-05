
// Определяем функции для показа и скрытия дива
function toggleFilters() {
    const filterDiv = document.getElementById('rools');

    // Проверяем текущее состояние и переключаем его
    if (filterDiv.style.display === 'none' || filterDiv.style.display === '') {
        filterDiv.style.display = 'block'; // Показываем
        localStorage.setItem('rools-visible', 'true'); // Сохраняем состояние как показано
    } else {
        filterDiv.style.display = 'none';  // Скрываем
        localStorage.setItem('rools-visible', 'false'); // Сохраняем состояние как скрыто
    }
}

// Добавляем обработчик события на кнопку
document.getElementById('filter-toggle').addEventListener('click', toggleFilters);

