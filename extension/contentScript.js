// contentScript.js
// This script checks if the user is on the TCGplayer login page and notifies the extension.
(function() {
    const loginHeader = document.querySelector('h1.sr-only');
    if (loginHeader && loginHeader.textContent.includes('TCGplayer - Login')) {
        // Notify background or popup that login is required
        chrome.runtime.sendMessage({ action: 'tcgplayer_login_required' });
    } else {
        chrome.runtime.sendMessage({ action: 'tcgplayer_logged_in' });
    }
})();
