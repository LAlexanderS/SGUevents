// Определяем функции для показа и скрытия дива
function toggleSortSection() {
    const sortSectionDiv = document.getElementById('sort-section');

    // Проверяем текущее состояние и переключаем его
    if (sortSectionDiv.style.display === 'none' || sortSectionDiv.style.display === '') {
        sortSectionDiv.style.display = 'block'; // Показываем
    } else {
        sortSectionDiv.style.display = 'none';  // Скрываем
    }
}

// Добавляем обработчик события на кнопку
document.getElementById('sort-toggle').addEventListener('click', toggleSortSection);

// Скрываем див по умолчанию
document.getElementById('sort-section').style.display = 'none';