document.addEventListener('click', function(event) {
    const targetElement = event.target.closest('.add-to-cart, .remove-from-favorites');

    if (!targetElement) {
        return; // Если клик не по нужному элементу, выходим
    }

    event.preventDefault(); // Предотвращаем стандартное поведение ссылки

    const heartIcon = targetElement.querySelector('.heart-icon');
    const heartRedIcon = targetElement.querySelector('.heart-red-icon');
    const eventSlug = targetElement.dataset.eventSlug; // Уникальный идентификатор

    if (targetElement.classList.contains('add-to-cart')) {
        // Логика добавления в избранное
        heartIcon.classList.add('hidden');
        heartRedIcon.classList.remove('hidden');

        targetElement.classList.remove('add-to-cart');
        targetElement.classList.add('remove-from-favorites');
        // Сохраняем состояние в localStorage
        localStorage.setItem(`event-${eventSlug}`, 'liked');

    } else if (targetElement.classList.contains('remove-from-favorites')) {
        // Логика удаления из избранного
        heartIcon.classList.remove('hidden');
        heartRedIcon.classList.add('hidden');

        targetElement.classList.remove('remove-from-favorites');
        targetElement.classList.add('add-to-cart');
        // Удаляем состояние из localStorage
        localStorage.removeItem(`event-${eventSlug}`);
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const elements = document.querySelectorAll('[data-event-slug]');

    elements.forEach(element => {
        const eventSlug = element.dataset.eventSlug; // Уникальный идентификатор
        const heartIcon = element.querySelector('.heart-icon');
        const heartRedIcon = element.querySelector('.heart-red-icon');
        const isLiked = localStorage.getItem(`event-${eventSlug}`) === 'liked';

        if (isLiked) {
            // Если элемент был "лайкнут", применяем соответствующие изменения
            heartIcon.classList.add('hidden');
            heartRedIcon.classList.remove('hidden');
            element.classList.remove('add-to-cart');
            element.classList.add('remove-from-favorites');
        } else {
            // Если элемент не был "лайкнут", сбрасываем состояние
            heartIcon.classList.remove('hidden');
            heartRedIcon.classList.add('hidden');
            element.classList.remove('remove-from-favorites');
            element.classList.add('add-to-cart');
        }
    });
});