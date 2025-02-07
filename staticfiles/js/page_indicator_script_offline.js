const textContainer = document.querySelector('.text-container');
const prevBtn = document.querySelector('.prev-btn');
const nextBtn = document.querySelector('.next-btn');
const indicatorsContainer = document.querySelector('.indicators');
let currentPageIndex = 0;
let pages = [];

// Полный текст пока написан просто текстом, потом заменится на подгружаемый
const fullText = `Банк России по результатам проведенных проверок установил факты манипулирования рынком 
при совершении сделок с фьючерсными контрактами на организованных торгах.Тарасов Александр Владимирович и 
Тарасова Людмила Александровна в период с 01.11.2022 по 15.11.2022 совершали взаимные сделки с фьючерсными 
контрактами на алюминий (ALMN-2.23), цинк (Zn-2.23, Zn-1.23), курс евро — канадский доллар (ECAD-3.23), 
курс доллар США — турецкая лира (UTRY-3.23), курс евро — японская иена (EJPY-3.23).Касымов Парвиз Эркинович 
и Касымова Фарангис Илхомовна в период с 18.11.2022 по 08.12.2022 совершали взаимные сделки с фьючерсными 
контрактами на медь (Co-12.22), никель (Nl-12.22), индексы финансов (FNI-12.22), металлов и добычи (MMI-12.22, 
MMI-3.23), нефти и газа (OGI-3.23), акции инвестиционного фонда iShares Core EURO STOXX 50 UCITS ETF EUR (Dist) 
(STOX-6.23)`;

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