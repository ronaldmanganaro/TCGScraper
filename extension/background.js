chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'openAndClick') {
      chrome.tabs.create({ url: 'https://store.tcgplayer.com/admin/pricing', active: true }, (tab) => {
        const tabId = tab.id;
  
        // Wait for the tab to finish loading
        chrome.tabs.onUpdated.addListener(function listener(updatedTabId, info) {
          if (updatedTabId === tabId && info.status === 'complete') {
            chrome.tabs.onUpdated.removeListener(listener);
  
            // Now inject the script to click the button
            chrome.scripting.executeScript({
              target: { tabId: tabId },
              func: () => {
                const interval = setInterval(() => {
                  const buttons = Array.from(document.querySelectorAll('button, input, .info-icon'));
                  const target = buttons.find(
                    (btn) =>
                      btn.innerText.includes('Export From Live') ||
                      (btn.value && btn.value.includes('Export From Live')) ||
                      (btn.title && btn.title.includes('Export From Live'))
                  );
  
                  if (target) {
                    target.click();
                    console.log('✅ Clicked Export From Live button');
                    clearInterval(interval);
                  }
                }, 500);
              }
            });
          }
        });
      });
    }
  });
  