(() => {
    const carousel = document.querySelector('[data-hero-carousel]');
    if (!carousel) return;
    const slides = [...carousel.querySelectorAll('[data-hero-slide]')];
    const selectors = [...carousel.querySelectorAll('[data-hero-select]')];
    const controls = carousel.querySelector('[data-hero-controls]');
    if (slides.length < 2 || !controls) return;

    const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
    let current = 0;
    let timer;
    let hovered = false;
    let focused = false;
    let inView = true;
    let request = 0;

    const stop = () => window.clearTimeout(timer);
    const schedule = () => {
        stop();
        if (motion.matches || hovered || focused || !inView || document.hidden) return;
        timer = window.setTimeout(() => show((current + 1) % slides.length), 2000);
    };
    const show = async (index) => {
        stop();
        const selectedRequest = ++request;
        const image = slides[index].querySelector('img');
        if (image) {
            image.loading = 'eager';
            try { await image.decode(); } catch { /* Shared image fallback remains available. */ }
        }
        if (selectedRequest !== request) return;
        current = index;
        for (const [position, slide] of slides.entries()) {
            const active = position === current;
            slide.classList.toggle('is-active', active);
            slide.setAttribute('aria-hidden', String(!active));
            selectors[position].setAttribute('aria-pressed', String(active));
        }
        const nextImage = slides[(current + 1) % slides.length].querySelector('img');
        if (nextImage) nextImage.loading = 'eager';
        schedule();
    };

    for (const [index, selector] of selectors.entries()) {
        selector.addEventListener('click', () => show(index));
    }
    controls.addEventListener('keydown', (event) => {
        if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
        event.preventDefault();
        const index = (current + (event.key === 'ArrowRight' ? 1 : -1) + slides.length) % slides.length;
        selectors[index].focus();
        show(index);
    });
    carousel.addEventListener('pointerenter', (event) => {
        if (event.pointerType !== 'mouse') return;
        hovered = true;
        stop();
    });
    carousel.addEventListener('pointerleave', () => { hovered = false; schedule(); });
    carousel.addEventListener('focusin', () => { focused = true; stop(); });
    carousel.addEventListener('focusout', (event) => { focused = carousel.contains(event.relatedTarget); schedule(); });
    document.addEventListener('visibilitychange', schedule);
    motion.addEventListener('change', schedule);
    if ('IntersectionObserver' in window) {
        new IntersectionObserver(([entry]) => { inView = entry.isIntersecting; schedule(); }).observe(carousel);
    }
    controls.hidden = false;
    const nextImage = slides[1].querySelector('img');
    if (nextImage) nextImage.loading = 'eager';
    schedule();
})();
