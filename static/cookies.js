
function getCookieStatus() {
  return localStorage.getItem('cookieStatus');
}

function setCookieAccepted() {
  localStorage.setItem('cookieStatus', 'accepted');
}

function setCookieDeclined() {
  localStorage.setItem('cookieStatus', 'declined');
}

function isGermanUser() {
  const userLanguage = navigator.language || navigator.userLanguage;
  if (userLanguage.startsWith('de')) {
      return true;
  }
  return false;
}

function loadContent() {
  const cookieStatus = getCookieStatus();
  if (cookieStatus === 'accepted') {
    const gtagScript = document.createElement('script');
    gtagScript.async = true;
    gtagScript.src = 'https://www.googletagmanager.com/gtag/js?id=G-CGWQKX3VYK';
    document.head.appendChild(gtagScript);
    const gtagConfig = document.createElement('script');
    gtagConfig.innerHTML = `
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-CGWQKX3VYK');
    `;
    document.head.appendChild(gtagConfig);
  }
}

function showCookieBanner() {
  const banner = document.getElementById('cookie-banner');
  if (isGermanUser()) {
    banner.innerHTML = `
    <div style="position: absolute; z-index: 300; top: 50%; left: 50%; transform: translate(-50%, -50%); background-color: var(--background-tile-color); color: var(--text-color); border-radius: 30px; padding: 20px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3); flex-direction: column; justify-content: space-between; width: 600px; max-width: 80vw; max-height: 60svh; text-align: center;">
      <h2 style="color: var(--primary-color);">Deine Daten. Deine Wahl.</h2>
      <p style="margin-top: 20px; text-wrap: balance;">Um Dein Erlebnis auf unserer Website zu verbessern und den Traffic zu analysieren, verwenden wir funktionale und analytische Cookies. Du hast die Möglichkeit, nicht-essentielle Cookies abzulehnen. Weitere Details und die Möglichkeit, Deine Präferenzen anzupassen, findest Du in unserer <a href="privacy" style="color: var(--text-color);">Datenschutzerklärung</a>.</p>
      <div style="margin-top: 20px; display: flex; justify-content: center; gap: 20px;">
        <button onclick="setCookieStatus('decline')" style="border-radius: 25px; width: 50%; padding: 10px 0; border: none; background-color: var(--secondary-color); color: var(--text-color); cursor: pointer;">Optionale Ablehnen</button>
        <button onclick="setCookieStatus('accept')" style="border-radius: 25px; width: 50%; padding: 10px 0; border: none; background-color: var(--primary-color); color: var(--white-color); cursor: pointer;">Alle Akzeptieren</button>
      </div>
    </div>
      `;
  } else {
    banner.innerHTML = `
    <div style="position: absolute; z-index: 300; top: 50%; left: 50%; transform: translate(-50%, -50%); background-color: var(--background-tile-color); color: var(--text-color); border-radius: 30px; padding: 20px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3); flex-direction: column; justify-content: space-between; width: 600px; max-width: 80vw; max-height: 60svh; text-align: center;">
      <h2 style="color: var(--primary-color);">Your Data. Your Choice.</h2>
      <p style="margin-top: 20px; text-wrap: balance;">To enhance Your experience on our website and analyze traffic, we use functional and analytical cookies. You have the option to decline non-essential cookies. For more details and to adjust your preferences, please visit our <a href="privacy" style="color: var(--text-color);">Privacy Policy</a>.</p>
      <div style="margin-top: 20px; display: flex; justify-content: center; gap: 20px;">
        <button onclick="setCookieStatus('decline')" style="border-radius: 25px; width: 50%; padding: 10px 0; border: none; background-color: var(--secondary-color); color: var(--text-color); cursor: pointer;">Decline Optional</button>
        <button onclick="setCookieStatus('accept')" style="border-radius: 25px; width: 50%; padding: 10px 0; border: none; background-color: var(--primary-color); color: var(--white-color); cursor: pointer;">Accept All</button>
      </div>
    </div>
    `;
  } 
  banner.style.display = 'block';
}

function setCookieStatus(status) {
  const banner = document.getElementById('cookie-banner');
  if (status === 'accept') {
    setCookieAccepted();
    loadContent();
  } else {
    setCookieDeclined();
  }
  unblurPage();
  banner.style.display = 'none';
}

function handleLoading() {
  const cookieStatus = getCookieStatus();
  
  if (cookieStatus !== 'accepted' && cookieStatus !== 'declined') {
      showCookieBanner();
      blurPageExcept();
  } 
  loadContent();
}

function blurPageExcept() {
  const elements = document.querySelectorAll('body > *:not(#cookie-banner)');
  elements.forEach(element => {
    element.classList.add('blurred');
  });
}

function unblurPage() {
  const elements = document.querySelectorAll('.blurred');
  elements.forEach(element => {
    element.classList.remove('blurred');
  });
}

handleLoading();