document.addEventListener("DOMContentLoaded", function() {
    // Фильтр по названию
    const savedNameValue = localStorage.getItem('filterName');
    const filterNameValueSpan = document.getElementById('filter-name-value');
    const filterNameMessageDiv = document.getElementById('filter-name-message');
    const inputNameField = document.getElementById('event-name-search');
    const filterDiv = document.getElementById('rools');
    if (savedNameValue) {
      inputNameField.value = savedNameValue;
      filterNameValueSpan.textContent = savedNameValue;
      filterNameMessageDiv.style.display = savedNameValue ? 'block' : 'none';
    } else {
      filterNameMessageDiv.style.display = 'none';
    }
      // Фильтр по дате
    const savedStartValue = localStorage.getItem('filterStartDate');
    const savedEndValue = localStorage.getItem('filterEndDate');
    const filterStartSpan = document.getElementById('filter-start-date-value');
    const filterEndSpan = document.getElementById('filter-end-date-value');
    const filterDateMessageDiv = document.getElementById('filter-date-message');
    const inputStartField = document.getElementById('date_start');
    const inputEndField = document.getElementById('date_end');
  
    // Загрузка значений из localStorage и форматирование
    if (savedStartValue) {
      inputStartField.value = savedStartValue;
      filterStartSpan.textContent = formatDate(savedStartValue);
    }
    if (savedEndValue) {
      inputEndField.value = savedEndValue;
      filterEndSpan.textContent = formatDate(savedEndValue);
    }
  
    // Отображение блока фильтра по дате, если есть хоть одно значение
    filterDateMessageDiv.style.display = (savedStartValue || savedEndValue) ? 'block' : 'none';
  
    // Фильтр по времени
    const savedStartTimeValue = localStorage.getItem('filterStartTime');
    const savedEndTimeValue = localStorage.getItem('filterEndTime');
    const filterStartTimeSpan = document.getElementById('filter-start-time-value');
    const filterEndTimeSpan = document.getElementById('filter-end-time-value');
    const filterTimeMessageDiv = document.getElementById('filter-time-message');
    const inputStartTimeField = document.getElementById('time_to_start');
    const inputEndTimeField = document.getElementById('time_to_end');
    if (savedStartTimeValue || savedEndTimeValue) {
    if (savedStartTimeValue) {
      inputStartTimeField.value = savedStartTimeValue;
      filterStartTimeSpan.textContent = savedStartTimeValue;
    }
    if (savedEndTimeValue) {
      inputEndTimeField.value = savedEndTimeValue;
      filterEndTimeSpan.textContent = savedEndTimeValue;
    }
    filterTimeMessageDiv.style.display = 'block';
    } else {
    filterTimeMessageDiv.style.display = 'none';
    }
  
   // Фильтр по спикерам
   const storedSpeakers = localStorage.getItem('selectedSpeakers');
   if (storedSpeakers) {
    const speakers = JSON.parse(storedSpeakers);
    speakers.forEach(speaker => {
     const checkbox = document.querySelector(`input[value="${speaker}"]`);
     if (checkbox) {
      checkbox.checked = true;
     }
    });
   }
   displaySelectedSpeakers(); // Вызываем функцию для обновления отображения после загрузки из localStorage
  
   // Фильтр по тегам
  const storedTags = localStorage.getItem('selectedTags');
  if (storedTags) {
   const tags = JSON.parse(storedTags);
   tags.forEach(tag => {
    const checkboxes = document.querySelectorAll('input[name="f_tags[]"]'); // Выбираем все чекбоксы тегов
    checkboxes.forEach(checkbox => {
     if (checkbox.value === tag) { // Сравниваем значения
      checkbox.checked = true;
     }
    });
   });
  }
  displaySelectedTags();
  
   // Отображение сортировки
   const savedSortBy = localStorage.getItem('filterSortBy');
   const filterSortValueSpan = document.getElementById('filter-sort-value');
   const filterSortMessageDiv = document.getElementById('filter-sort-message');
  
   if (savedSortBy) {
      let displayValue;
      switch (savedSortBy) {
        case "default":
          displayValue = "По умолчанию";
          break;
        case "time_start":
          displayValue = "Раньше";
          break;
        case "-time_start":
          displayValue = "Позже";
          break;
        case "date":
          displayValue = "Сначала старые";
          break;
        case "-date":
          displayValue = "Сначала новые";
          break;
        default:
          displayValue = "Неизвестная сортировка";
      }
      document.querySelector(`input[name="order_by"][value="${savedSortBy}"]`).checked = true;
      filterSortValueSpan.textContent = displayValue;
      filterSortMessageDiv.classList.remove('hidden');
    }

    const elements = document.querySelectorAll('[data-event-slug]');

    elements.forEach(element => {
        const eventSlug = element.dataset.eventSlug; // Уникальный идентификатор
        const heartIcon = element.querySelector('.heart-icon');
        const heartRedIcon = element.querySelector('.heart-red-icon');
        const isLiked = localStorage.getItem(`event-${eventSlug}`) === 'liked';

        if (isLiked) {
            // Если элемент был "лайкнут", применяем соответствующие изменения
            heartIcon.classList.add('hidden');
            heartRedIcon.classList.remove('hidden');
            element.classList.remove('add-to-cart');
            element.classList.add('remove-from-favorites');
        } else {
            // Если элемент не был "лайкнут", сбрасываем состояние
            heartIcon.classList.remove('hidden');
            heartRedIcon.classList.add('hidden');
            element.classList.remove('remove-from-favorites');
            element.classList.add('add-to-cart');
        }
    });     
  
  
   // Отображение блока фильтров
   filterDiv.style.display = (savedNameValue !== null || savedStartValue !== null || savedEndValue !== null || savedStartTimeValue !== null || savedEndTimeValue !== null || storedSpeakers !== null && JSON.parse(storedSpeakers).length > 0 || storedTags !== null && JSON.parse(storedTags).length > 0 || localStorage.getItem('rools-visible') === 'true') ? 'block' : 'none';
  });