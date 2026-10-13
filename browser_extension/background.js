// AURXON Chrome Extension - Background Service Worker
chrome.sidePanel
  .setPanelBehavior({ openPanelOnActionClick: true })
  .catch((error) => console.error(error));

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'AURXON_DETECTED_TICKER') {
    chrome.storage.local.set({ lastDetectedTicker: message.ticker });
    sendResponse({ status: 'ACKNOWLEDGED' });
  }
});
