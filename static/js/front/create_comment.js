const commentButtons = document.querySelectorAll('.btn-comment');

const commentModal = document.querySelector('#commentModal');

const closeButton = commentModal.querySelector('.button-close');

// Функция для открытия модального окна
const openModal = () => {
    commentModal.style.display = 'block';
};

// Функция для закрытия модального окна
const closeModal = () => {
    commentModal.style.display = 'none';
};

// Добавляем обработчик событий для каждой кнопки
commentButtons.forEach(button => {
    button.addEventListener('click', openModal);
});

// Если есть кнопка закрытия, добавляем обработчик для нее
if (closeButton) {
    closeButton.addEventListener('click', closeModal);
}

// Закрытие модального окна при клике вне его содержимого
window.addEventListener('click', (event) => {
    if (event.target === commentModal) {
        closeModal();
    }
});