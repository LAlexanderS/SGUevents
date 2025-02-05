const slider = document.querySelector('.items');
const prevButton = document.querySelector('.prev-reviews');
const nextButton = document.querySelector('.next-reviews');

let isDown = false;
let startX;
let scrollLeft;

//прокрутка влево
function scrollToPrev() {
  const itemWidth = slider.querySelector('.item').offsetWidth; // Ширина одного отзыва
  slider.scrollBy({
    left: -itemWidth, // Прокручиваем на ширину одного отзыва влево
    behavior: 'smooth' // Плавная прокрутка
  });
}

// прокрутка вправо
function scrollToNext() {
  const itemWidth = slider.querySelector('.item').offsetWidth; // Ширина одного отзыва
  slider.scrollBy({
    left: itemWidth, // Прокручиваем на ширину одного отзыва вправо
    behavior: 'smooth' // Плавная прокрутка
  });
}

// Обработчики для кнопок
prevButton.addEventListener('click', scrollToPrev);
nextButton.addEventListener('click', scrollToNext);

// Логика для перетаскивания мышью
slider.addEventListener('mousedown', (e) => {
  isDown = true;
  slider.classList.add('active');
  startX = e.pageX - slider.offsetLeft;
  scrollLeft = slider.scrollLeft;
});

slider.addEventListener('mouseleave', () => {
  isDown = false;
  slider.classList.remove('active');
});

slider.addEventListener('mouseup', () => {
  isDown = false;
  slider.classList.remove('active');
});

slider.addEventListener('mousemove', (e) => {
  if (!isDown) return;
  e.preventDefault();
  const x = e.pageX - slider.offsetLeft;
  const walk = (x - startX) * 3;
  slider.scrollLeft = scrollLeft - walk;
});