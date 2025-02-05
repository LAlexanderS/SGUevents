let currentPage = 1; // Текущая страница
const cardsPerPage = 2; // Количество карточек на странице
let allCards = []; // Массив для хранения всех карточек

// Функция для инициализации карточек
function initializeCards() {
    allCards = document.querySelectorAll('.card'); // Получаем все карточки
    updateArrows(); // Обновляем видимость стрелок
    displayCards(currentPage); // Отображаем карточки для текущей страницы
}

// Функция для отображения карточек на текущей странице
function displayCards(page) {
    const startIndex = (page - 1) * cardsPerPage;
    const endIndex = startIndex + cardsPerPage;

    // Скрываем все карточки
    allCards.forEach(card => card.style.display = 'none');

    // Показываем карточки для текущей страницы
    for (let i = startIndex; i < endIndex && i < allCards.length; i++) {
        allCards[i].style.display = 'block';
    }
}

// Функция для обновления видимости стрелок
function updateArrows() {
    const arrowLeft = document.querySelector('.arrow-nav-left');
    const arrowRight = document.querySelector('.arrow-nav-right');

    // Скрываем стрелку влево на первой странице
    if (currentPage === 1) {
        arrowLeft.style.display = 'none';
    } else {
        arrowLeft.style.display = 'block';
    }

    // Скрываем стрелку вправо на последней странице
    if (currentPage === Math.ceil(allCards.length / cardsPerPage)) {
        arrowRight.style.display = 'none';
    } else {
        arrowRight.style.display = 'block';
    }
}

// Функция для перехода на предыдущую страницу
function prevPage() {
    if (currentPage > 1) {
        currentPage--;
        displayCards(currentPage);
        updateArrows();
    }
}

// Функция для перехода на следующую страницу
function nextPage() {
    if (currentPage < Math.ceil(allCards.length / cardsPerPage)) {
        currentPage++;
        displayCards(currentPage);
        updateArrows();
    }
}

// Назначаем обработчики событий для стрелок
document.querySelector('.arrow-nav-left').addEventListener('click', prevPage);
document.querySelector('.arrow-nav-right').addEventListener('click', nextPage);

// Инициализация при загрузке страницы
window.addEventListener('load', initializeCards);

//Функция для обновления пагинации
// function updatePagination() {
//     const pagination = document.getElementById('pagination');
//     pagination.innerHTML = ''; // Очищаем пагинацию

//     const totalPages = Math.ceil(allCards.length / cardsPerPage);
// }

function goToPage(page) {
    if (page < 1 || page > Math.ceil(allCards.length / cardsPerPage)) return;
    currentPage = page;
    displayCards(currentPage);
    updateArrows();
    updatePagination(); // Обновляем состояние пагинации
}

// Функция обновления пагинации
function updatePagination() {
    const pagination = document.querySelector('pagination');
    pagination.innerHTML = '';
    
    const totalPages = Math.ceil(allCards.length / cardsPerPage);
    const ul = document.createElement('ul');
    ul.className = 'pagination';

    // Кнопка "Назад"
    const prevLi = document.createElement('li');
    prevLi.className = `pagination__item pagination__item--prev ${currentPage === 1 ? 'disabled' : ''}`;
    prevLi.innerHTML = '<a href="#" class="pagination__link">Назад</a>';
    prevLi.addEventListener('click', (e) => {
        e.preventDefault();
        if (currentPage > 1) goToPage(currentPage - 1);
    });
    ul.appendChild(prevLi);

    // Номера страниц
    for (let i = 1; i <= totalPages; i++) {
        const li = document.createElement('li');
        li.className = `pagination__item ${currentPage === i ? 'pagination__item--active' : ''}`;
        li.innerHTML = `<a href="#" class="pagination__link">${i}</a>`;
        li.addEventListener('click', (e) => {
            e.preventDefault();
            goToPage(i);
        });
        ul.appendChild(li);
    }

    // Кнопка "Следующая"
    const nextLi = document.createElement('li');
    nextLi.className = `pagination__item pagination__item--next ${currentPage === totalPages ? 'disabled' : ''}`;
    nextLi.innerHTML = '<a href="#" class="pagination__link">Следующая</a>';
    nextLi.addEventListener('click', (e) => {
        e.preventDefault();
        if (currentPage < totalPages) goToPage(currentPage + 1);
    });
    ul.appendChild(nextLi);

    pagination.appendChild(ul);
}

function prevPage() {
    goToPage(currentPage - 1);
}

function nextPage() {
    goToPage(currentPage + 1);let currentPage = 1;
    const cardsPerPage = 2;
    let allCards = [];
    
    function initializeCards() {
        allCards = document.querySelectorAll('.card');
        updateArrows();
        updatePagination();
        displayCards(currentPage);
    }
    
    function displayCards(page) {
        const startIndex = (page - 1) * cardsPerPage;
        const endIndex = startIndex + cardsPerPage;
    
        allCards.forEach(card => card.style.display = 'none');
        for (let i = startIndex; i < endIndex && i < allCards.length; i++) {
            allCards[i].style.display = 'block';
        }
    }
    
    function updateArrows() {
        const arrowLeft = document.querySelector('.arrow-nav-left');
        const arrowRight = document.querySelector('.arrow-nav-right');
    
        arrowLeft.style.display = currentPage === 1 ? 'none' : 'block';
        arrowRight.style.display = currentPage === Math.ceil(allCards.length / cardsPerPage) ? 'none' : 'block';
    }
    
    function prevPage() {
        goToPage(currentPage - 1);
    }
    
    function nextPage() {
        goToPage(currentPage + 1);
    }
    
    function goToPage(page) {
        if (page < 1 || page > Math.ceil(allCards.length / cardsPerPage)) return;
        currentPage = page;
        displayCards(currentPage);
        updateArrows();
        updatePagination();
    }
    
    function updatePagination() {
        const pagination = document.querySelector('.pagination');
        if (!pagination) return;
        pagination.innerHTML = '';
        
        const totalPages = Math.ceil(allCards.length / cardsPerPage);
        const ul = document.createElement('ul');
        ul.className = 'pagination';
    
        // Кнопка "Назад"
        const prevLi = document.createElement('li');
        prevLi.className = `pagination__item pagination__item--prev ${currentPage === 1 ? 'disabled' : ''}`;
        prevLi.innerHTML = '<a href="#" class="pagination__link">Назад</a>';
        prevLi.addEventListener('click', (e) => {
            e.preventDefault();
            if (currentPage > 1) goToPage(currentPage - 1);
        });
        ul.appendChild(prevLi);
    
        // Номера страниц
        for (let i = 1; i <= totalPages; i++) {
            const li = document.createElement('li');
            li.className = `pagination__item ${currentPage === i ? 'pagination__item--active' : ''}`;
            li.innerHTML = `<a href="#" class="pagination__link">${i}</a>`;
            li.addEventListener('click', (e) => {
                e.preventDefault();
                goToPage(i);
            });
            ul.appendChild(li);
        }
    
        // Кнопка "Следующая"
        const nextLi = document.createElement('li');
        nextLi.className = `pagination__item pagination__item--next ${currentPage === totalPages ? 'disabled' : ''}`;
        nextLi.innerHTML = '<a href="#" class="pagination__link">Следующая</a>';
        nextLi.addEventListener('click', (e) => {
            e.preventDefault();
            if (currentPage < totalPages) goToPage(currentPage + 1);
        });
        ul.appendChild(nextLi);
    
        pagination.appendChild(ul);
    }
    
    // Назначаем обработчики для стрелок
    document.querySelector('.arrow-nav-left').addEventListener('click', prevPage);
    document.querySelector('.arrow-nav-right').addEventListener('click', nextPage);

    // Инициализация при загрузке страницы
window.addEventListener('load', initializeCards);
    
    // Инициализация при готовности DOM
    document.addEventListener('DOMContentLoaded', initializeCards);
}


function initializeCards() {
    allCards = document.querySelectorAll('.card');
    updateArrows();
    updatePagination();
    displayCards(currentPage);
}

// Инициализация при готовности DOM
document.addEventListener('DOMContentLoaded', initializeCards);