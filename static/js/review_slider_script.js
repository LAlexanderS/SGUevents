// КАРУСЕЛЬ ОТЗЫВОВ
let currentSlideReviews = 0
const slidesReviews = document.querySelectorAll(".slide-review")
const dotsReviews = document.querySelectorAll('.dot-reviews')

const initReviews = (n) => {
    slidesReviews.forEach((slide, index) => {
        slide.style.display = "none"
        dotsReviews.forEach((dot) => dot.classList.remove("active"))
    })
    slidesReviews[n].style.display = "block"
    dotsReviews[n].classList.add("active")
}

document.addEventListener("DOMContentLoaded", () => initReviews(currentSlideReviews))

const nextReviews = () => {
    currentSlideReviews = (currentSlideReviews >= slidesReviews.length - 1) ? 0 : currentSlideReviews + 1
    initReviews(currentSlideReviews)
}

const prevReviews = () => {
    currentSlideReviews = (currentSlideReviews <= 0) ? slidesReviews.length - 1 : currentSlideReviews - 1
    initReviews(currentSlideReviews)
}

document.querySelector(".next-reviews").addEventListener('click', nextReviews)
document.querySelector(".prev-reviews").addEventListener('click', prevReviews)

dotsReviews.forEach((dot, i) => {
    dot.addEventListener("click", () => {
        initReviews(i)
        currentSlideReviews = i
    })
})

// Добавляем Hammer.js для свайпов
const sliderReviewsContainer = document.querySelector('.review-container')

if (sliderReviewsContainer) {
    const hammerReviews = new Hammer(sliderReviewsContainer)
    hammerReviews.on('swipeleft', nextReviews)
    hammerReviews.on('swiperight', prevReviews)
}


//КАРУСЕЛЬ ИНФО-БЛОКОВ В ДЕСКТОП ВЕРСИИ
document.addEventListener("DOMContentLoaded", () => {
    // === DESKTOP ===
    const track = document.getElementById("carousel-track")
    if (track) {
        const infoBlocks = track.querySelectorAll('.info-block')

        if (infoBlocks.length < 4) {
            document.querySelector('.carousel-btn.left').style.display = 'none'
            document.querySelector('.carousel-btn.right').style.display = 'none'
        }

        track.style.justifyContent = infoBlocks.length < 3 ? 'center' : 'flex-start'

        let isMovingDesktop = false

        function moveLeftDesktop() {
            if (isMovingDesktop) return
            isMovingDesktop = true

            track.style.transition = 'transform 0.4s ease'
            track.style.transform = 'translateX(-33.3333%)'

            setTimeout(() => {
                track.appendChild(track.firstElementChild)
                track.style.transition = 'none'
                track.style.transform = 'translateX(0)'
                isMovingDesktop = false
            }, 400)
        }

        function moveRightDesktop() {
            if (isMovingDesktop) return
            isMovingDesktop = true

            track.insertBefore(track.lastElementChild, track.firstElementChild)
            track.style.transition = 'none'
            track.style.transform = 'translateX(-33.3333%)'

            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    track.style.transition = 'transform 0.4s ease'
                    track.style.transform = 'translateX(0)'
                })
            })

            setTimeout(() => {
                isMovingDesktop = false
            }, 400)
        }

        document.querySelector('.carousel-btn.right')?.addEventListener('click', moveLeftDesktop)
        document.querySelector('.carousel-btn.left')?.addEventListener('click', moveRightDesktop)
    }

})

//КАРУСЕЛЬ ИНФО-БЛОКОВ В МОБИЛЬНОЙ ВЕРСИИ
document.addEventListener("DOMContentLoaded", () => {
    const track = document.getElementById("carousel-track-mobile")
    const btnLeft = document.querySelector('.carousel-btn-mobile.left')
    const btnRight = document.querySelector('.carousel-btn-mobile.right')

    if (!track) return

    const slides = track.querySelectorAll('.info-slide')

    if (slides.length < 4) {
        btnLeft.style.display = 'none'
        btnRight.style.display = 'none'
        track.style.justifyContent = slides.length < 3 ? 'center' : 'flex-start'
        return
    }

    let isMoving = false

    function moveLeft() {
        if (isMoving) return
        isMoving = true

        track.style.transition = 'transform 0.4s ease'
        track.style.transform = 'translateX(-33.3333%)'

        setTimeout(() => {
            track.appendChild(track.firstElementChild)
            track.style.transition = 'none'
            track.style.transform = 'translateX(0)'
            isMoving = false
        }, 400)
    }

    function moveRight() {
        if (isMoving) return
        isMoving = true

        track.insertBefore(track.lastElementChild, track.firstElementChild)
        track.style.transition = 'none'
        track.style.transform = 'translateX(-33.3333%)'

        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                track.style.transition = 'transform 0.4s ease'
                track.style.transform = 'translateX(0)'
            })
        })

        setTimeout(() => {
            isMoving = false
        }, 400)
    }

    btnRight.addEventListener('click', moveLeft)
    btnLeft.addEventListener('click', moveRight)

    // Подключаем свайпы через Hammer.js
    const hammerMobile = new Hammer(track)
    hammerMobile.on('swipeleft', moveLeft)
    hammerMobile.on('swiperight', moveRight)
})