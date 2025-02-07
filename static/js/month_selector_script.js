// Получаем элемент для выбора года
const yearSelect = document.getElementById('yearSelect');
const currentYear = new Date().getFullYear();

// Заполняем выпадающий список годами от 5 лет назад до 5 лет вперед
for (let year = currentYear - 5; year <= currentYear + 5; year++) {
    let option = document.createElement('option');
    option.value = year;  // Устанавливаем значение опции равным текущему году в цикле
    option.text = year;
    yearSelect.appendChild(option);
}