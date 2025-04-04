/**
 * Декодирует строки вида \uXXXX в обычные символы
 * Пример: "\u002D" → "-"
 */
function decodeUnicode(rawText) {
    return rawText.replace(/\\u([\dA-Fa-f]{4})/g, (_, code) =>
        String.fromCharCode(parseInt(code, 16))
    )
}

/**
 * Декодирует HTML-сущности (например, &nbsp;, &amp;, &#8212;)
 */
function decodeHtmlEntities(text) {
    const textarea = document.createElement('textarea')
    textarea.innerHTML = text
    return textarea.value
}

/**
 * Удаляет невидимые/управляющие символы из текста
 */
function removeControlChars(text) {
    return text.replace(/[\u0000-\u001F\u007F-\u009F]/g, '')
}

/**
 * Полная универсальная очистка текста:
 * - unicode \uXXXX → символ
 * - html-сущности → символ
 * - невидимые символы удаляются
 */
function cleanText(rawText) {
    return removeControlChars(
        decodeHtmlEntities(
            decodeUnicode(rawText)
        )
    ).trim()
}

// Глобальная доступность
window.textSanitizer = {
    cleanText,
    decodeHtmlEntities,
    decodeUnicode,
    removeControlChars,
}
