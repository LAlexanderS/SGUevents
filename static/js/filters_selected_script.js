function setNameFilter() {
  const filterValueSpan = document.getElementById('filter-name-value');
  const filterNameMessageDiv = document.getElementById('filter-name-message');
  const searchValue = document.getElementById('event-name-search').value.trim();
  // Устанавливаем значение в span
  filterValueSpan.textContent = searchValue;
  // Проверяем значение и отображаем или скрываем div с фильтром
  if (searchValue !== "") {
      filterNameMessageDiv.style.display = 'block'; // Показываем
  } else {
      filterNameMessageDiv.style.display = 'none'; // Скрываем
  }
  // Сохраняем значение в localStorage
  localStorage.setItem('filterName', searchValue);
}
// Обработчик события для кнопки
document.getElementById('apply-name-button').addEventListener('click', setNameFilter);


function clearNameFilter() {
  const inputField = document.getElementById('event-name-search');
  const filterValueSpan = document.getElementById('filter-name-value');
  const filterMessageDiv = document.getElementById('filter-name-message');
  // Очищаем поле ввода
  inputField.value = '';
  filterValueSpan.textContent = ''; // Очищаем значение в span
  filterMessageDiv.style.display = 'none'; // Скрываем сообщение
  // Удаляем значение из localStorage
  localStorage.removeItem('filterName');
  // Отправляем форму
  document.getElementById('name-form').submit();
}
// Обработчик события для кнопки удаления фильтра
document.getElementById('delete-name-filter').addEventListener('click', clearNameFilter);



function formatDate(date) {
  if (!date) return "";
  const options = { year: 'numeric', month: '2-digit', day: '2-digit' };
  const dateObj = new Date(date);
  if (isNaN(dateObj.getTime())) return "";
  return dateObj.toLocaleDateString('ru-RU', options);
 }
 


function setDateFilter() {
  const startInput = document.getElementById('date_start');
  const endInput = document.getElementById('date_end');
  const filterStartSpan = document.getElementById('filter-start-date-value');
  const filterEndSpan = document.getElementById('filter-end-date-value');
  const filterDateMessageDiv = document.getElementById('filter-date-message');

  const startDate = startInput.value ? new Date(startInput.value) : null;
  const endDate = endInput.value ? new Date(endInput.value) : null;


  filterStartSpan.textContent = startDate ? formatDate(startDate) : "";
  filterEndSpan.textContent = endDate ? formatDate(endDate) : "";

  if (startInput.value || endInput.value) {
    filterDateMessageDiv.style.display = 'block';
  } else {
    filterDateMessageDiv.style.display = 'none';
  }

  // Сохранение в localStorage (в формате гггг-мм-дд, если нужно)
  localStorage.setItem('filterStartDate', startInput.value);
  localStorage.setItem('filterEndDate', endInput.value);
}


document.getElementById('apply-date-button').addEventListener('click', setDateFilter);



function clearDateFilter() {
  const inputStartField = document.getElementById('date_start');
  const inputEndField = document.getElementById('date_end');
  const filterStartSpan = document.getElementById('filter-start-date-value');
  const filterEndSpan = document.getElementById('filter-end-date-value');
  const filterDateMessageDiv = document.getElementById('filter-date-message');
  // Очищаем поля ввода
  inputStartField.value = '';
  inputEndField.value = '';
  // Очищаем значения в span
  filterStartSpan.textContent = '';
  filterEndSpan.textContent = '';
  // Скрываем сообщение
  filterDateMessageDiv.style.display = 'none';
  // Удаляем значения из localStorage
  localStorage.removeItem('filterStartDate');
  localStorage.removeItem('filterEndDate');
  // Отправляем форму
  document.getElementById('dateDropdown').submit(); 
}
// Обработчик события для кнопки удаления фильтра по дате
document.getElementById('delete-date-filter').addEventListener('click', clearDateFilter);



function setTimeFilter() {
  const filterStartTimeSpan = document.getElementById('filter-start-time-value');
  const filterEndTimeSpan = document.getElementById('filter-end-time-value');
  const filterTimeMessageDiv = document.getElementById('filter-time-message');
  const searchStartTimeValue = document.getElementById('time_to_start').value;
  const searchEndTimeValue = document.getElementById('time_to_end').value;
  // Устанавливаем значение в span
  filterStartTimeSpan.textContent = searchStartTimeValue;
  filterEndTimeSpan.textContent = searchEndTimeValue;
  // Проверяем значение и отображаем или скрываем div с фильтром
  if (searchStartTimeValue  !== "" || searchEndTimeValue !== "") {
      filterTimeMessageDiv.style.display = 'block'; // Показываем
  } else {
      filterTimeMessageDiv.style.display = 'none'; // Скрываем
  }
  // Сохраняем значение в localStorage
  localStorage.setItem('filterStartTime', searchStartTimeValue);
  localStorage.setItem('filterEndTime', searchEndTimeValue);
}
// Обработчик события для кнопки
document.getElementById('apply-time-button').addEventListener('click', setTimeFilter);


function clearTimeFilter() {
  const inputStartTimeField = document.getElementById('time_to_start');
  const inputEndTimeField = document.getElementById('time_to_end');
  const filterStartTimeSpan = document.getElementById('filter-start-time-value');
  const filterEndTimeSpan = document.getElementById('filter-end-time-value');
  const filterTimeMessageDiv = document.getElementById('filter-time-message');
  // Очищаем поля ввода
  inputStartTimeField.value = '';
  inputEndTimeField.value = '';
  // Очищаем значения в span
  filterStartTimeSpan.textContent = '';
  filterEndTimeSpan.textContent = '';
  // Скрываем сообщение
  filterTimeMessageDiv.style.display = 'none';
  // Удаляем значения из localStorage
  localStorage.removeItem('filterStartTime');
  localStorage.removeItem('filterEndTime');
  // Отправляем форму
  document.getElementById('timeDropdown').submit(); 
}
// Обработчик события для кнопки удаления фильтра по времени
document.getElementById('delete-time-filter').addEventListener('click', clearTimeFilter); 



function displaySelectedSpeakers() {
  const filterSpeakersValueSpan = document.getElementById('filter-speakers-value');
  const filterSpeakersMessageDiv = document.getElementById('filter-speakers-message');
  const selectedSpeakers = [];
 
  const checkboxes = document.querySelectorAll('input[name="f_speakers[]"]');
  checkboxes.forEach(checkbox => {
   if (checkbox.checked) {
    selectedSpeakers.push(checkbox.value);
   }
  });
 
  filterSpeakersValueSpan.textContent = selectedSpeakers.join(', ');
  filterSpeakersMessageDiv.classList.toggle('hidden', selectedSpeakers.length === 0);
  localStorage.setItem('selectedSpeakers', JSON.stringify(selectedSpeakers));
 }
 
 document.getElementById('apply-speakers-button').addEventListener('click', displaySelectedSpeakers);


 function clearSpeakersFilter() {
  const filterSpeakersValueSpan = document.getElementById('filter-speakers-value');
  const filterSpeakersMessageDiv = document.getElementById('filter-speakers-message');
  const checkboxes = document.querySelectorAll('input[name="f_speakers[]"]');
 
  checkboxes.forEach(checkbox => checkbox.checked = false);
  filterSpeakersValueSpan.textContent = '';
  filterSpeakersMessageDiv.classList.add('hidden');
  localStorage.removeItem('selectedSpeakers');

  document.getElementById('speaker-form').submit();
 }
 
 document.getElementById('delete-speakers-filter').addEventListener('click', clearSpeakersFilter);



 function displaySelectedTags() {
  const filterTagsValueSpan = document.getElementById('filter-tags-value');
  const filterTagsMessageDiv = document.getElementById('filter-tags-message');
  const selectedTags = [];
 
  const checkboxes = document.querySelectorAll('input[name="f_tags[]"]');
  checkboxes.forEach(checkbox => {
   if (checkbox.checked) {
    selectedTags.push(checkbox.value);
   }
  });
 
  filterTagsValueSpan.textContent = selectedTags.join(', ');
  filterTagsMessageDiv.classList.toggle('hidden', selectedTags.length === 0);
  localStorage.setItem('selectedTags', JSON.stringify(selectedTags));
 }

 document.getElementById('apply-tags-button').addEventListener('click', displaySelectedTags);
 
 function clearTagsFilter() {
  const filterTagsValueSpan = document.getElementById('filter-tags-value');
  const filterTagsMessageDiv = document.getElementById('filter-tags-message');
  const checkboxes = document.querySelectorAll('input[name="f_tags[]"]');
 
  checkboxes.forEach(checkbox => checkbox.checked = false);
  filterTagsValueSpan.textContent = '';
  filterTagsMessageDiv.classList.add('hidden');
  localStorage.removeItem('selectedTags');
  document.getElementById('tags-form').submit();
 }

 document.getElementById('delete-tags-filter').addEventListener('click', clearTagsFilter);


  
