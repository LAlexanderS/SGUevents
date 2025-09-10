(function () {
    function formatMB(bytes) {
        return (bytes / (1024 * 1024)).toFixed(2)
    }

    function updateIndicator(indicator, usedBytes, maxBytes) {
        if (!indicator) return
        indicator.dataset.usedBytes = String(usedBytes)
        indicator.dataset.maxBytes = String(maxBytes)
        var usedMb = formatMB(usedBytes)
        var maxMb = formatMB(maxBytes)
        indicator.textContent = 'Размер изображений: использовано ' + usedMb + ' МБ из ' + maxMb + ' МБ'
    }

    function markIndicatorError(message) {
        var indicator = document.getElementById('gallery-usage')
        if (!indicator) return
        indicator.style.color = '#b94a48' // bootstrap-like error color
        indicator.style.fontWeight = '600'
        // Add explanation once
        if (!document.getElementById('gallery-usage-error-note')) {
            var note = document.createElement('div')
            note.id = 'gallery-usage-error-note'
            note.style.color = '#b94a48'
            note.style.marginTop = '4px'
            note.textContent = message || 'Превышен размер загружаемых файлов'
            indicator.parentNode.insertBefore(note, indicator.nextSibling)
        }
    }

    function attachToInlines() {
        var indicator = document.getElementById('gallery-usage')
        if (!indicator) return
        var usedBytes = parseInt(indicator.getAttribute('data-used-bytes') || '0', 10)
        var maxBytes = parseInt(indicator.getAttribute('data-max-bytes') || (8 * 1024 * 1024), 10)
        // initial baseline from server for per-file sizes
        var sizesNode = document.getElementById('gallery-sizes')
        var sizesData = null
        try { sizesData = sizesNode ? JSON.parse(sizesNode.textContent || '{}') : null } catch (e) { sizesData = null }

        // Track current known sizes for single-file fields to adjust on change
        var singleCurrent = { qr: 0, image: 0, documents: 0 }
        if (sizesData && sizesData.singles) {
            ;['qr', 'image', 'documents'].forEach(function (k) {
                var v = sizesData.singles[k]
                if (v && typeof v.size === 'number') singleCurrent[k] = v.size
            })
        }

        // If server-side validation fired, admin will render an error block.
        // Detect it and highlight the indicator in red with an explanation.
        var errorBlocks = Array.from(document.querySelectorAll('.errornote, ul.errorlist'))
        var hasQuotaError = errorBlocks.some(function (el) {
            return /Превышен размер загружаемых файлов/.test(el.textContent || '')
        })
        if (hasQuotaError) {
            markIndicatorError('Превышен размер загружаемых файлов')
        }

        // Watch file inputs in gallery inlines
        var inlineContainer = document.querySelectorAll('div.inline-group')
        inlineContainer.forEach(function (group) {
            if (!/Галерея|Gallery/i.test(group.textContent || '')) return
            group.addEventListener('change', function (e) {
                var target = e.target
                if (!(target instanceof HTMLInputElement)) return
                if (target.type !== 'file') return

                var files = target.files
                if (!files || files.length === 0) return

                var totalAdded = 0
                for (var i = 0; i < files.length; i++) {
                    totalAdded += files[i].size
                }

                var projected = usedBytes + totalAdded
                if (projected > maxBytes) {
                    // Try to compress images and re-check
                    compressFiles(Array.from(files), maxBytes - usedBytes).then(function (result) {
                        if (result.compressedBlobs.length) {
                            // Replace the input's FileList via DataTransfer
                            var dt = new DataTransfer()
                            result.compressedBlobs.forEach(function (blob, idx) {
                                var name = files[idx] ? files[idx].name : ('image_' + idx + '.jpg')
                                dt.items.add(new File([blob], name, { type: blob.type || 'image/jpeg' }))
                            })
                            target.files = dt.files
                            var nowAdded = 0
                            for (var j = 0; j < target.files.length; j++) nowAdded += target.files[j].size
                            usedBytes += nowAdded // optimistic — real used updates after save
                            updateIndicator(indicator, usedBytes, maxBytes)
                            alert('Изображения были сжаты для соответствия лимиту.')
                        } else {
                            alert('Превышен лимит ' + formatMB(maxBytes) + ' МБ. Уберите часть файлов.')
                            target.value = ''
                        }
                    })
                } else {
                    usedBytes = projected // optimistic until save
                    updateIndicator(indicator, usedBytes, maxBytes)
                }
            })

            // handle delete/clear checkboxes in inlines
            group.addEventListener('click', function (e) {
                var el = e.target
                if (!(el instanceof HTMLInputElement)) return
                // Django inline delete toggle
                if (el.name && /-DELETE$/.test(el.name)) {
                    // find image preview near this inline row and estimate size deduction using server data if possible
                    var row = el.closest('div.inline-related, tr.form-row')
                    var url = ''
                    if (row) {
                        var img = row.querySelector('a[href*="/media/"]') || row.querySelector('img')
                        if (img) { url = img.getAttribute('href') || img.getAttribute('src') || '' }
                    }
                    var deduct = 0
                    if (sizesData && sizesData.gallery && url) {
                        var item = sizesData.gallery.find(function (g) { return g.url === url })
                        if (item && item.size) deduct = item.size
                    }
                    // Fallback: approximate 0 if unknown
                    if (el.checked) usedBytes = Math.max(0, usedBytes - deduct)
                    else usedBytes = usedBytes + deduct
                    updateIndicator(indicator, usedBytes, maxBytes)
                }
                // ClearableFileInput checkbox for single-file fields (qr/image/documents)
                if (el.name && /(qr|image|documents)-clear/.test(el.name)) {
                    var key = (/(qr|image|documents)-clear/.exec(el.name) || [])[1]
                    var prev = singleCurrent[key] || 0
                    if (el.checked) usedBytes = Math.max(0, usedBytes - prev)
                    else usedBytes = usedBytes + prev
                    updateIndicator(indicator, usedBytes, maxBytes)
                }
            })
        })

            // Top-level single-file inputs (outside inlines): adjust usedBytes when user selects files
            ;['qr', 'image', 'documents'].forEach(function (key) {
                var input = document.querySelector('input[type=file][name=' + key + ']')
                if (!input) return
                input.addEventListener('change', function () {
                    var newTotal = 0
                    var files = input.files || []
                    for (var i = 0; i < files.length; i++) newTotal += (files[i].size || 0)
                    // Replace previous size contribution with new one
                    usedBytes = Math.max(0, usedBytes - (singleCurrent[key] || 0)) + newTotal
                    singleCurrent[key] = newTotal
                    updateIndicator(indicator, usedBytes, maxBytes)
                })
            })
    }

    function compressFiles(files, budgetBytes) {
        // Compress sequentially until under budget; simple heuristic
        var compressedBlobs = []
        var total = 0
        return files.reduce(function (chain, file) {
            return chain.then(function () {
                return compressImage(file, 0.8, 1600) // initial quality/size
                    .then(function (blob) {
                        if (!blob) return null
                        if (total + blob.size > budgetBytes) {
                            return compressImage(file, 0.7, 1400)
                                .then(function (b2) {
                                    if (!b2) return null
                                    if (total + b2.size > budgetBytes) {
                                        return compressImage(file, 0.6, 1200)
                                            .then(function (b3) { return b3 })
                                    }
                                    return b2
                                })
                        }
                        return blob
                    })
                    .then(function (finalBlob) {
                        if (finalBlob) {
                            compressedBlobs.push(finalBlob)
                            total += finalBlob.size
                        }
                    })
            })
        }, Promise.resolve()).then(function () {
            return { compressedBlobs: total <= budgetBytes ? compressedBlobs : [] }
        })
    }

    function compressImage(file, quality, maxSize) {
        return new Promise(function (resolve) {
            if (!/^image\//.test(file.type)) {
                // Non-image: return as-is (will likely fail quota)
                resolve(file)
                return
            }
            var img = new Image()
            var reader = new FileReader()
            reader.onload = function (e) {
                img.onload = function () {
                    var w = img.width; var h = img.height
                    if (w > h && w > maxSize) { h = Math.round(h * (maxSize / w)); w = maxSize }
                    else if (h > w && h > maxSize) { w = Math.round(w * (maxSize / h)); h = maxSize }
                    else if (w > maxSize) { h = Math.round(h * (maxSize / w)); w = maxSize }
                    var canvas = document.createElement('canvas')
                    canvas.width = w; canvas.height = h
                    var ctx = canvas.getContext('2d')
                    ctx.drawImage(img, 0, 0, w, h)
                    canvas.toBlob(function (blob) { resolve(blob) }, 'image/jpeg', quality)
                }
                img.onerror = function () { resolve(null) }
                img.src = e.target.result
            }
            reader.onerror = function () { resolve(null) }
            reader.readAsDataURL(file)
        })
    }


    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', attachToInlines)
    } else {
        attachToInlines()
    }
})();


