document.addEventListener('DOMContentLoaded', function () {
    const isOffline = window.location.href.includes('/offline')

    if (isOffline) {
        const rootRow = document.querySelector('#rools .row.filter-events-row')

        // 1. Удаляем левый отступ
        const leftCol = rootRow.querySelector('.feed-left-column')
        if (leftCol) leftCol.remove()

        // 2. Собираем все col-lg-2 фильтры
        const col2Blocks = rootRow.querySelectorAll('.col-lg-2')

        // 3. Создаём новый .row для col-lg-2 фильтров
        const newRow = document.createElement('div')
        newRow.className = 'row'
        col2Blocks.forEach(block => newRow.appendChild(block))

        // 4. Создаём обёртку col-lg-10 и добавляем туда новый .row
        const wrapperCol10 = document.createElement('div')
        wrapperCol10.className = 'col-lg-10'
        wrapperCol10.appendChild(newRow)

        // 5. Вставляем финальную структуру
        rootRow.innerHTML = '' // очищаем .filter-events-row
        rootRow.appendChild(document.createElement('div')).className = 'col-lg-1' // левый отступ
        rootRow.appendChild(wrapperCol10) // центральный блок
        rootRow.appendChild(document.createElement('div')).className = 'col-lg-1' // правый отступ

        // 6. Добавляем фильтр "Место проведения"
        const placeCol = document.createElement('div')
        placeCol.classList.add('col-lg-2')
        placeCol.innerHTML = `
    <div class="dropdown dropdown-button">
        <button class="btn btn-secondary dropdown-toggle w-100" type="button"
            data-bs-toggle="dropdown" aria-expanded="false">
            Место
        </button>
        <form action="" method="get" class="dropdown-menu dropdown-filter w-100"
            data-bs-theme="dark" id="place-form">
            <div class="form-check">
                <input class="form-control me-3" type="search" id="event-place-search" name="f_place" placeholder="Введите адрес">
            </div>
            <div id="place-autocomplete-results" class="autocomplete-results"></div>
            <div class="text-center">
                <button class="btn btn-outline-success" type="submit" id="apply-place-button"
                    style="margin-top: 10px;">Применить</button>
            </div>
        </form>
    </div>
    `

        // Вставляем после фильтра "Время"
        const newCols = wrapperCol10.querySelectorAll('.col-lg-2')
        for (let i = 0; i < newCols.length; i++) {
            if (newCols[i].innerText.includes('Время')) {
                newCols[i].after(placeCol)
                break
            }
        }
    }
})
