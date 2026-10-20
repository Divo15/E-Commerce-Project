(() => {
    const previews = [...document.querySelectorAll('[data-preview]')];
    const categoryLinks = [...document.querySelectorAll('[data-category]')];
    const previewButtons = [...document.querySelectorAll('[data-show-preview]')];
    const previewRegion = document.querySelector('#collection-preview');
    const previewStatus = document.querySelector('.landing-preview-status');
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    let previewRequest = 0;

    const showPreview = async (categoryId, bringIntoView = false) => {
        const selected = previews.find((preview) => preview.dataset.preview === categoryId);
        if (!selected) return;
        const request = ++previewRequest;
        const name = selected.querySelector('[data-preview-name]').textContent;
        const image = selected.querySelector('img');
        previewRegion.setAttribute('aria-busy', 'false');
        for (const button of previewButtons) button.classList.remove('is-loading');
        if (previewStatus) previewStatus.textContent = '';

        if (image && !image.complete) {
            previewRegion.setAttribute('aria-busy', 'true');
            for (const button of previewButtons) button.classList.toggle('is-loading', button.dataset.showPreview === categoryId);
            if (bringIntoView && previewStatus) previewStatus.textContent = `Loading ${name} preview.`;
            image.loading = 'eager';
            try {
                await image.decode();
            } catch {
                if (image.isConnected) image.dispatchEvent(new Event('error'));
            }
        }
        if (request !== previewRequest) return;
        const changed = selected.hidden;
        for (const preview of previews) {
            const active = preview === selected;
            preview.hidden = !active;
            preview.classList.toggle('is-active', active);
            preview.classList.toggle('is-changing', active && changed && !reducedMotion.matches);
        }
        for (const link of categoryLinks) link.classList.toggle('is-active', link.dataset.category === categoryId);
        for (const button of previewButtons) {
            button.setAttribute('aria-pressed', String(button.dataset.showPreview === categoryId));
            button.classList.remove('is-loading');
        }
        previewRegion.setAttribute('aria-busy', 'false');
        if (bringIntoView) {
            if (previewStatus) previewStatus.textContent = `${name} preview selected. Open the collection to see its pieces.`;
            selected.focus({ preventScroll: true });
        }
        if (bringIntoView && window.matchMedia('(max-width: 600px)').matches) {
            previewRegion.scrollIntoView({ behavior: reducedMotion.matches ? 'instant' : 'smooth', block: 'start' });
        }
    };

    for (const link of categoryLinks) {
        link.addEventListener('pointerenter', (event) => {
            if (event.pointerType === 'mouse') showPreview(link.dataset.category);
        });
        link.addEventListener('focus', () => showPreview(link.dataset.category));
    }
    for (const button of previewButtons) {
        button.addEventListener('click', () => showPreview(button.dataset.showPreview, true));
        button.hidden = false;
    }

    if ('IntersectionObserver' in window && !reducedMotion.matches) {
        const observer = new IntersectionObserver((entries) => {
            let sequence = 0;
            for (const entry of entries) {
                if (!entry.isIntersecting) continue;
                entry.target.style.setProperty('--arrival-delay', `${Math.min(sequence, 3) * 70}ms`);
                entry.target.classList.add('is-arriving');
                sequence += 1;
                observer.unobserve(entry.target);
            }
        }, { threshold: 0.08 });
        for (const element of document.querySelectorAll('[data-arrive]')) observer.observe(element);
    }
})();
