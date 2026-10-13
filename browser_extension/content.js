// AURXON Chrome Extension - Content Script
// Extracts stock symbols strictly without collecting cookies, credentials, or personal data.
(function () {
  const KNOWN_SYMBOLS = [
    'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'BHARTIARTL',
    'ITC', 'KOTAKBANK', 'LT', 'HINDUNILVR', 'TATAMOTORS', 'BAJFINANCE', 'MARUTI',
    'SUNPHARMA', 'ASIANPAINT', 'TITAN', 'AXISBANK', 'NTPC', 'POWERGRID', 'TATASTEEL'
  ];

  function scanPageSymbols() {
    const text = document.title + ' ' + (document.body ? document.body.innerText.slice(0, 3000) : '');
    for (const sym of KNOWN_SYMBOLS) {
      if (text.includes(sym)) {
        chrome.runtime.sendMessage({
          type: 'AURXON_DETECTED_TICKER',
          ticker: sym,
          sourceUrl: window.location.href,
        }).catch(() => {});
        break;
      }
    }
  }

  window.addEventListener('load', scanPageSymbols);
})();
