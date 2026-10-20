for (const gallery of document.querySelectorAll('[data-product-gallery]')) {
    const track = gallery.querySelector('[data-gallery-track]');
    const slides = [...gallery.querySelectorAll('[data-gallery-slide]')];
    const previous = gallery.querySelector('[data-gallery-prev]');
    const next = gallery.querySelector('[data-gallery-next]');
    const current = gallery.querySelector('[data-gallery-current]');

    if (!track || slides.length < 2 || !previous || !next || !current) continue;

    let activeIndex = 0;
    let frame = 0;
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

    const update = (index) => {
        activeIndex = Math.max(0, Math.min(slides.length - 1, index));
        current.textContent = String(activeIndex + 1);
        previous.disabled = activeIndex === 0;
        next.disabled = activeIndex === slides.length - 1;
    };

    const goTo = (index) => {
        const target = Math.max(0, Math.min(slides.length - 1, index));
        track.scrollTo({
            left: slides[target].offsetLeft - track.offsetLeft,
            behavior: reducedMotion.matches ? 'auto' : 'smooth',
        });
        update(target);
    };

    previous.addEventListener('click', () => goTo(activeIndex - 1));
    next.addEventListener('click', () => goTo(activeIndex + 1));
    track.addEventListener('keydown', (event) => {
        if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
        event.preventDefault();
        goTo(activeIndex + (event.key === 'ArrowRight' ? 1 : -1));
    });
    track.addEventListener('scroll', () => {
        cancelAnimationFrame(frame);
        frame = requestAnimationFrame(() => {
            const nearest = slides.reduce((best, slide, index) => {
                const distance = Math.abs(slide.offsetLeft - track.offsetLeft - track.scrollLeft);
                return distance < best.distance ? { index, distance } : best;
            }, { index: 0, distance: Number.POSITIVE_INFINITY });
            update(nearest.index);
        });
    }, { passive: true });

    update(0);
}
