document.addEventListener('DOMContentLoaded', function () {
	var events = JSON.parse(document.getElementById('calendar').dataset.events)
	console.log(events)

	$('#calendar').fullCalendar({
		locale: 'ru',  // Указываем локаль
		events: events,
		height: 'auto',
		contentHeight: 'auto',
		aspectRatio: 1.35,
		eventRender: function (event, element) {
			element.css('background-color', 'green') // Задний фон под мероприятием зеленый
			element.find('.fc-title').append('<br/><b>' + event.time + '</b><br/><i>' + event.category + '</i>')
		},
		dayRender: function (date, cell) {
			if (date.isSame(new Date(), "day")) {
				cell.css("background-color", "yellow") // Сегодняшняя дата выделена желтым
			}
		}
	})
})
