// Получаем кнопки "Отправить заявку" и "Удалить заявку"
const sentAppButton = document.querySelector('.btn-sent_app');
const removeAppButton = document.querySelector('.btn-remove_app');

// Обработчик для кнопки "Отправить заявку"
sentAppButton.addEventListener('click', () => {
    sentAppButton.classList.add('hidden'); // Скрываем кнопку "Отправить"
    removeAppButton.classList.remove('hidden'); // Показываем кнопку "Удалить"
});

// Обработчик для кнопки "Удалить заявку"
removeAppButton.addEventListener('click', () => {
    removeAppButton.classList.add('hidden'); 
    sentAppButton.classList.remove('hidden'); 
});