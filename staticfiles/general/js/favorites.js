function initializeFavoriteButtons() {
	// Обработчик для добавления в избранное
	document.querySelectorAll('.add-to-cart').forEach(function (button) {
		button.addEventListener('click', function (event) {
			event.preventDefault()
			const eventSlug = this.getAttribute('data-event-slug')
			const icon = this.querySelector('.heart-icon')
			const button = this

			fetch(`/bookmarks/events_add/${eventSlug}/`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'X-CSRFToken': '{{ csrf_token }}'
				},
				body: JSON.stringify({ 'slug': eventSlug })
			})
				.then(response => response.json())
				.then(data => {
					if (data.added) {
						icon.src = "{% static 'general/icons/heart_red.png' %}"
						button.classList.remove('add-to-cart')
						button.classList.add('remove-from-favorites')
						button.setAttribute('data-event-id', data.event_id)
						showNotification("Добавлено в избранное")
					} else {
						icon.src = "{% static 'general/icons/heart.svg' %}"
						button.classList.remove('remove-from-favorites')
						button.classList.add('add-to-cart')
						button.removeAttribute('data-event-id')
						showNotification("Удалено из избранного")
					}
				})
				.catch(error => console.error('Error:', error))
		})
	})

	// Обработчик для удаления из избранного
	document.querySelectorAll('.remove-from-favorites').forEach(function (button) {
		button.addEventListener('click', function (event) {
			event.preventDefault()
			const eventId = this.getAttribute('data-event-id')
			const buttonElement = this
			const icon = this.querySelector('.heart-icon')

			fetch(`/bookmarks/events_remove/${eventId}/`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'X-CSRFToken': '{{ csrf_token }}'
				},
				body: JSON.stringify({ 'id': eventId })
			})
				.then(response => response.json())
				.then(data => {
					if (data.removed) {
						icon.src = "{% static 'general/icons/heart.svg' %}"
						buttonElement.classList.remove('remove-from-favorites')
						buttonElement.classList.add('add-to-cart')
						buttonElement.removeAttribute('data-event-id')
						showNotification("Удалено из избранного")
					} else {
						console.error('Ошибка:', data.error)
					}
				})
				.catch(error => console.error('Ошибка:', error))
		})
	})
}

function showNotification(message) {
	const notification = document.getElementById('favoriteNotification')
	notification.querySelector('p').textContent = message
	notification.style.display = 'block'
	setTimeout(() => {
		notification.classList.add('fade-in')
	}, 10)

	setTimeout(function () {
		notification.classList.remove('fade-in')
		notification.classList.add('fade-out')

		setTimeout(function () {
			notification.style.display = 'none'
			notification.classList.remove('fade-out')
		}, 700)
	}, 1000)
}

document.addEventListener('DOMContentLoaded', function () {
	initializeFavoriteButtons()
})