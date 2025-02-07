const modal = document.getElementById("modal-qr");
const openModalLinks = document.querySelectorAll(".open-modal"); 
const closeModalButton = document.getElementById("closeModal");

// Добавляем обработчик для всех элементов с классом open-modal
openModalLinks.forEach(function (link) {
    link.addEventListener("click", function (event) {
        event.preventDefault();
        modal.style.display = "block";
    });
});

// Закрываем модальное окно при клике на крестик
closeModalButton.addEventListener("click", function () {
    modal.style.display = "none";
});

// Закрываем модальное окно при клике вне его области
window.addEventListener("click", function (event) {
    if (event.target === modal) {
        modal.style.display = "none";
    }
});