const textContainer = document.querySelector('.text-container');
const prevBtn = document.querySelector('.prev-btn');
const nextBtn = document.querySelector('.next-btn');
const indicatorsContainer = document.querySelector('.indicators');
let currentPageIndex = 0;
let pages = [];

// Полный текст пока написан просто текстом, потом заменится на подгружаемый
const fullText = `Форум инновационных финансовых технологий FINOPOLIS в этом году вернется в Сочи. 
Он пройдет на территории Образовательного центра «Сириус». FINOPOLIS традиционно станет площадкой для обсуждения 
тенденций и возможностей современных технологий в финансовом секторе.
На форуме будет представлена широкая деловая программа с пленарными и секционными дискуссиями, 
а также выставочная зона с передовыми сервисами, инновационными технологическими решениями, мастер-классами и различными 
интерактивными мероприятиями от партнеров. Кроме того, лучшие команды региональных кейс-чемпионатов Молодежной программы 
FINOPOLIS.365 покажут экспертам финансового рынка свои проекты и поборются за звание суперфиналиста и денежный приз.`;

// Максимальное количество символов на странице
const maxCharsPerPage = 490;

// Функция для разбиения текста на страницы по количеству символов
function splitTextIntoPages(text, maxChars) {
    const words = text.split(' ');
    const pages = [];
    let currentPage = '';
    let currentPageLength = 0;

    words.forEach((word) => {
        // Если добавление текущего слова не превышает лимит символов
        if (currentPageLength + word.length + (currentPageLength > 0 ? 1 : 0) <= maxChars) {
            if (currentPageLength > 0) {
                currentPage += ' ';
                currentPageLength += 1;
            }
            currentPage += word;
            currentPageLength += word.length;
        } else {
            // Если превышает, сохраняем текущую страницу и начинаем новую
            pages.push(currentPage);
            currentPage = word;
            currentPageLength = word.length;
        }
    });

    // Добавляем последнюю страницу, если она не пустая
    if (currentPageLength > 0) {
        pages.push(currentPage);
    }

    return pages;
}

// Создаем страницы на основе текста
function createPages() {
    pages = splitTextIntoPages(fullText, maxCharsPerPage);

    pages.forEach((pageText) => {
        const page = document.createElement('div');
        page.classList.add('page');
        page.textContent = pageText;
        textContainer.appendChild(page);
    });

    showPage(0);
}



// Функция для создания индикаторов
function createIndicators() {
    for (let i = 0; i < pages.length; i++) {
        const indicator = document.createElement('div');
        indicator.classList.add('indicator');
        indicator.dataset.index = i;
        indicator.addEventListener('click', function () {
            showPage(parseInt(this.dataset.index, 10));
        });
        if (i === 0) {
            indicator.classList.add('active');
        }
        indicatorsContainer.appendChild(indicator);
    }
}

// Функция для обновления индикаторов
function updateIndicators() {
    const indicators = document.querySelectorAll('.indicator');
    indicators.forEach((indicator, i) => {
        indicator.classList.toggle('active', i === currentPageIndex);
    });
}

// Функция для обновления состояния кнопок
function updateButtonStates() {
    prevBtn.disabled = currentPageIndex === 0;
    nextBtn.disabled = currentPageIndex === pages.length - 1;
}

// Функция для отображения страницы
function showPage(index) {
    const pageElements = document.querySelectorAll('.page');
    pageElements.forEach((page, i) => {
        page.classList.toggle('active', i === index);
    });
    currentPageIndex = index;
    updateIndicators();
    updateButtonStates();
}

// Обработчики для кнопок
prevBtn.addEventListener('click', () => {
    const prevIndex = (currentPageIndex - 1 + pages.length) % pages.length;
    showPage(prevIndex);
});

nextBtn.addEventListener('click', () => {
    const nextIndex = (currentPageIndex + 1) % pages.length;
    showPage(nextIndex);
});

// Инициализация
createPages();
createIndicators();
updateButtonStates();