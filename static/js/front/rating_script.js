// Получаем средний рейтинг из контекста Django
const averageRating = parseFloat("{{ average_rating|default:0 }}"); 
// пример получения рейтинга, на который опирается этот скрипт, в файле README.md

// Функция для установки рейтинга
function setRating(rating) {
    const ratingInputs = document.querySelectorAll('.half-stars input[type="radio"]');
    ratingInputs.forEach(input => {
        if (parseFloat(input.value) === rating) {
            input.checked = true;
        }
    });
}

// Устанавливаем рейтинг при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    setRating(averageRating);
});