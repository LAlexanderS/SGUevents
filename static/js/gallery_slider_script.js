let currentSlide = 0
const slides = document.querySelectorAll(".slide")
const dots = document.querySelectorAll(".dot")

// Функция отображения нужного слайда
const init = (n) => {
  slides.forEach((slide, index) => {
    slide.style.display = "none"
    dots.forEach((dot) => dot.classList.remove("active"))
  })

  slides[n].style.display = "block"
  dots[n].classList.add("active")
}

// Сброс интервала
let interval = null
function resetInterval() {
  clearInterval(interval)
  interval = setInterval(() => {
    next()
  }, 5000)
}

// Инициализация слайдера
document.addEventListener("DOMContentLoaded", () => {
  init(currentSlide)
  resetInterval()  // Запуск таймера при загрузке
})

// Переключение вперёд
const next = () => {
  currentSlide = (currentSlide >= slides.length - 1) ? 0 : currentSlide + 1
  init(currentSlide)
  resetInterval()  // <--- сброс таймера при ручном переключении
}

// Переключение назад
const prev = () => {
  currentSlide = (currentSlide <= 0) ? slides.length - 1 : currentSlide - 1
  init(currentSlide)
  resetInterval()
}

// Обработчики стрелок
document.querySelector(".next").addEventListener("click", next)
document.querySelector(".prev").addEventListener("click", prev)

// Обработка точек
dots.forEach((dot, i) => {
  dot.addEventListener("click", () => {
    init(i)
    currentSlide = i
    resetInterval()
  })
})

// Свайпы
const sliderContainer = document.querySelector('.slide-container')
const hammer = new Hammer(sliderContainer)

hammer.on('swipeleft', next)
hammer.on('swiperight', prev)

// --- ⏸ Пауза при наведении ---
sliderContainer.addEventListener('mouseenter', () => {
  clearInterval(interval)  // Останавливаем автопрокрутку
})

sliderContainer.addEventListener('mouseleave', () => {
  resetInterval()  // Возобновляем автопрокрутку
})
