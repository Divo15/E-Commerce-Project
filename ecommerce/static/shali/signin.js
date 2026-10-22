(() => {
    const toggle = document.querySelector('.signin-password-toggle');
    const password = document.getElementById('login-password');
    if (!toggle || !password) return;

    toggle.hidden = false;
    toggle.addEventListener('click', () => {
        const reveal = password.type === 'password';
        password.type = reveal ? 'text' : 'password';
        toggle.textContent = reveal ? 'Hide' : 'Show';
        toggle.setAttribute('aria-label', reveal ? 'Hide password' : 'Show password');
        toggle.setAttribute('aria-pressed', String(reveal));
    });
})();
