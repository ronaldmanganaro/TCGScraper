document.addEventListener('DOMContentLoaded', () => {
    const button = document.getElementById('interact');
  
    button.addEventListener('click', () => {
      chrome.runtime.sendMessage({ action: 'openAndClick' }, (response) => {
        if (chrome.runtime.lastError) {
          console.error('Error sending message:', chrome.runtime.lastError.message);
        } else {
          console.log('Message sent successfully:', response);
        }
      });
    });
  });
  
  // Listen for messages from the content script
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'tcgplayer_login_required') {
      const statusDiv = document.getElementById('status');
      if (statusDiv) {
        statusDiv.textContent = 'Please log in to TCGplayer before exporting inventory.';
        statusDiv.style.color = '#d32f2f'; // red
      }
    } else if (message.action === 'tcgplayer_logged_in') {
      const statusDiv = document.getElementById('status');
      if (statusDiv) {
        statusDiv.textContent = '';
        statusDiv.style.color = '#388e3c'; // green
      }
    }
  });
