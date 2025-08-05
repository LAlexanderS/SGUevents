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
    return text.replace(/[\u0000-\u0009\u000B-\u000C\u000E-\u001F\u007F-\u009F]/g, '')
}

function formatMarkdown(text) {
    return text
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')  // жирный
        .replace(/\*(.+?)\*/g, '<em>$1</em>')              // *курсив*
}

/**
 * Полная универсальная очистка текста:
 * - unicode \uXXXX → символ
 * - html-сущности → символ
 * - невидимые символы удаляются
 */

function sanitizeAllowedTags(text) {
    const div = document.createElement('div')
    div.innerHTML = text

    const allowedTags = ['STRONG', 'EM']
    const elements = div.querySelectorAll('*')

    elements.forEach(el => {
        if (!allowedTags.includes(el.tagName)) {
            el.replaceWith(...el.childNodes)
        }
    })

    return div.innerHTML
}

function cleanText(rawText) {
    const cleaned = removeControlChars(
        decodeHtmlEntities(
            decodeUnicode(rawText)
        )
    ).trim()

    return sanitizeAllowedTags(formatMarkdown(cleaned))
}
// Глобальная доступность
window.textSanitizer = {
    cleanText,
    decodeHtmlEntities,
    decodeUnicode,
    removeControlChars,
}
