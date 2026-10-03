const departmentMenus = [...document.querySelectorAll('.department-menu')];

for (const menu of departmentMenus) {
    menu.addEventListener('toggle', () => {
        if (!menu.open) return;
        for (const sibling of departmentMenus) {
            if (sibling !== menu) sibling.open = false;
        }
    });
}

document.addEventListener('click', (event) => {
    for (const menu of departmentMenus) {
        if (!menu.contains(event.target)) menu.open = false;
    }
});

document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    for (const menu of departmentMenus) {
        if (menu.open) {
            menu.open = false;
            menu.querySelector('summary').focus();
        }
    }
});

const searchDialog = document.querySelector('#search-dialog');
for (const trigger of document.querySelectorAll('[data-search-open]')) {
    trigger.addEventListener('click', () => searchDialog.showModal());
}
searchDialog.querySelector('[data-dialog-close]').addEventListener('click', () => searchDialog.close());
searchDialog.addEventListener('click', (event) => {
    const bounds = searchDialog.getBoundingClientRect();
    if (event.target === searchDialog && (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom)) {
        searchDialog.close();
    }
});

const mobileLayout = window.matchMedia('(max-width: 900px)');
mobileLayout.addEventListener('change', () => {
    for (const menu of departmentMenus) menu.open = false;
});

for (const image of document.querySelectorAll('main img')) {
    const showFallback = () => {
        const placeholder = document.createElement('span');
        placeholder.className = 'image-placeholder';
        placeholder.textContent = image.alt || 'Image coming soon';
        image.replaceWith(placeholder);
    };
    image.addEventListener('error', showFallback, { once: true });
    if (image.complete && image.naturalWidth === 0) showFallback();
}
