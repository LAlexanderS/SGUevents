let currentSlideReviews = 0;
const slidesReviews = document.querySelectorAll(".slide-review");
const dotsReviews = document.querySelectorAll('.dot-reviews');

const initReviews = (n) => {
    slidesReviews.forEach((slide, index) => {
        slide.style.display = "none";
        dotsReviews.forEach((dot) => dot.classList.remove("active")); 
    });
    slidesReviews[n].style.display = "block";
    dotsReviews[n].classList.add("active");
};

document.addEventListener("DOMContentLoaded", () => initReviews(currentSlideReviews));

const nextReviews = () => {
    currentSlideReviews = (currentSlideReviews >= slidesReviews.length - 1) ? 0 : currentSlideReviews + 1;
    initReviews(currentSlideReviews);
};

const prevReviews = () => {
    currentSlideReviews = (currentSlideReviews <= 0) ? slidesReviews.length - 1 : currentSlideReviews - 1;
    initReviews(currentSlideReviews);
};

document.querySelector(".next-reviews").addEventListener('click', nextReviews);
document.querySelector(".prev-reviews").addEventListener('click', prevReviews);

dotsReviews.forEach((dot, i) => {
    dot.addEventListener("click", () => {
        initReviews(i);
        currentSlideReviews = i;
    });
});

// Добавляем Hammer.js для свайпов
const sliderReviewsContainer = document.querySelector('.review-container');

if (sliderReviewsContainer) { 
    const hammerReviews = new Hammer(sliderReviewsContainer);
    hammerReviews.on('swipeleft', nextReviews);
    hammerReviews.on('swiperight', prevReviews);
}