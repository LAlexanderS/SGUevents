// Инициализация переменной для отслеживания текущего слайда
let currentSlide = 0;

// Получение всех слайдов и точек (индикаторов) на странице
const slides = document.querySelectorAll(".slide");
const dots = document.querySelectorAll(".dot");

// Функция для инициализации слайдера
const init = (n) => {
  // Скрываем все слайды и удаляем активный класс у всех точек
  slides.forEach((slide, index) => {
    slide.style.display = "none";
    dots.forEach((dot) => dot.classList.remove("active"));
  });
  
  // Показываем текущий слайд и активируем соответствующую точку
  slides[n].style.display = "block";
  dots[n].classList.add("active");
};

// Инициализация слайдера при загрузке страницы
document.addEventListener("DOMContentLoaded", () => init(currentSlide));

// Функция для перехода к следующему слайду
const next = () => {
  // Если текущий слайд последний, переходим к первому, иначе к следующему
  currentSlide = (currentSlide >= slides.length - 1) ? 0 : currentSlide + 1;
  init(currentSlide);
};

// Функция для перехода к предыдущему слайду
const prev = () => {
  // Если текущий слайд первый, переходим к последнему, иначе к предыдущему
  currentSlide = (currentSlide <= 0) ? slides.length - 1 : currentSlide - 1;
  init(currentSlide);
};

// Добавление обработчиков событий для кнопок "next" и "prev"
document.querySelector(".next").addEventListener("click", next);
document.querySelector(".prev").addEventListener("click", prev);

// Автоматическое перелистывание слайдов каждые 5 секунд
setInterval(() => {
  next();
}, 5000);

// Добавление обработчиков событий для точек
dots.forEach((dot, i) => {
  dot.addEventListener("click", () => {
    init(i); // Показываем слайд, соответствующий точке
    currentSlide = i; // Обновляем текущий слайд
  });
});

// Инициализация Hammer.js для обработки свайпов на мобильных устройствах
const sliderContainer = document.querySelector('.slide-container');
const hammer = new Hammer(sliderContainer);

// Обработка свайпов
hammer.on('swipeleft', next);
hammer.on('swiperight', prev);