function toggleSpeakers() {
    const popup = document.querySelector('.speaker-popup')
    const card = document.querySelector('.card')
    popup.classList.toggle('active')
    card.classList.toggle('blur')
}

function toggleTags() {
    const popup = document.querySelector('.tag-popup')
    const card = document.querySelector('.card')
    popup.classList.toggle('active')
    card.classList.toggle('blur')
}

function closePopup() {
    const popups = document.querySelectorAll('.overlay-popup')
    const card = document.querySelector('.card')
    popups.forEach(popup => popup.classList.remove('active'))
    card.classList.remove('blur')
}

// Закрытие попапа по клику вне его области
document.addEventListener('click', function (e) {
    const popups = document.querySelectorAll('.overlay-popup')
    const card = document.querySelector('.card')
    if (!e.target.closest('.popup-content') && !e.target.closest('.preview-speakers') && !e.target.closest('.preview-tags')) {
        popups.forEach(popup => popup.classList.remove('active'))
        card.classList.remove('blur')
    }
})