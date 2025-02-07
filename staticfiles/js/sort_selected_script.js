function setSortFilter() {
  // Получаем элементы для отображения выбранного значения и сообщения
  const filterValueSpan = document.getElementById('filter-sort-value');
  const filterSortMessageDiv = document.getElementById('filter-sort-message');
  
  // Получаем выбранный радио-элемент сортировки
  const selectedSortRadio = document.querySelector('input[name="order_by"]:checked');
  let displayValue;

  // Определяем текст для отображения в зависимости от выбранной сортировки
  switch (selectedSortRadio.value) {
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

  // Устанавливаем текст в элемент для отображения
  filterValueSpan.textContent = displayValue;

  // Показываем или скрываем сообщение в зависимости от выбранной сортировки
  if (selectedSortRadio.value !== "default") {
      filterSortMessageDiv.classList.remove('hidden');
  } else {
      filterSortMessageDiv.classList.add('hidden');
  }

  // Сохраняем выбранную сортировку в localStorage и отправляем форму
  localStorage.setItem('filterSortBy', selectedSortRadio.value);
  document.getElementById('sort-form').submit();
}

function clearSortFilter() {
  // Получаем все радио-кнопки и элементы для отображения
  const radioButtons = document.querySelectorAll('input[name="order_by"]');
  const filterValueSpan = document.getElementById('filter-sort-value');
  const filterMessageDiv = document.getElementById('filter-sort-message');

  // Сбрасываем выбор на сортировку по умолчанию
  radioButtons.forEach(radio => radio.checked = radio.id === 'sort-time-default');

  // Очищаем текст и скрываем сообщение
  filterValueSpan.textContent = '';
  filterMessageDiv.classList.add('hidden');

  // Удаляем сохраненную сортировку из localStorage и отправляем форму
  localStorage.removeItem('filterSortBy');
  document.getElementById('sort-form').submit();
}

// Назначаем обработчики событий для кнопок "Применить" и "Сбросить"
document.getElementById('apply-sort-button').addEventListener('click', setSortFilter);
document.getElementById('delete-sort-filter').addEventListener('click', clearSortFilter);