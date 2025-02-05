document.addEventListener('DOMContentLoaded', function () {
    var events = [];
    console.log(events);

    $('#calendar').fullCalendar({
        locale: 'ru',
        height: 'parent',
        events: events,
        eventRender: function (event, element) {
            element.addClass(event.css_class);

            element.find('.fc-title').html(event.time + '  ' + event.category + '<br/><b> <a href="' + event.url + '" style="color:white;">' + event.title + '</a>');

        },
        dayRender: function (date, cell) {
            if (date.isSame(new Date(), "day")) {
                cell.css("background-color", "yellow"); // Сегодняшняя дата выделена желтым
            }
        }
    });
});