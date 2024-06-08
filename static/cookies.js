
function getCookieStatus() {
  return localStorage.getItem('cookieStatus');
}

function setCookieAccepted() {
  localStorage.setItem('cookieStatus', 'accepted');
}

function setCookieDeclined() {
  localStorage.setItem('cookieStatus', 'declined');
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
  banner.innerHTML = `
  <div style="position: absolute; z-index: 300; top: 50%; left: 50%; transform: translate(-50%, -50%); background-color: var(--background-tile-color); color: var(--text-color); border-radius: 30px; padding: 20px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3); flex-direction: column; justify-content: space-between; width: 600px; max-width: 80vw; max-height: 60svh; text-align: center;">
    <b>This website uses cookies</b>
    <p style="margin-top: 20px; text-wrap: balance;">To enhance Your experience on our website and analyze traffic, we use functional and analytical cookies. You have the option to decline non-essential cookies. For more details and to adjust your preferences, please visit our <a href="privacy" style="color: var(--text-color);">Privacy Policy</a>.</p>
    <div style="margin-top: 20px; display: flex; justify-content: center; gap: 20px;">
        <button onclick="setCookieStatus('decline')" style="border-radius: 25px; width: 50%; padding: 10px 0; border: none; background-color: var(--secondary-color); cursor: pointer;">Decline Optional</button>
        <button onclick="setCookieStatus('accept')" style="border-radius: 25px; width: 50%; padding: 10px 0; border: none; background-color: var(--primary-color); color: var(--white-color); cursor: pointer;">Accept All</button>
    </div>
  </div>
  `;
  banner.style.display = 'block';
}

function setCookieStatus(status) {
  if (status === 'accept') {
    setCookieAccepted();
    loadContent();
  } else {
    setCookieDeclined();
  }
  banner.style.display = 'none';
}

function handleLoading() {
  const cookieStatus = getCookieStatus();
  
  if (cookieStatus !== 'accepted' && cookieStatus !== 'declined') {
      showCookieBanner();
  } 
  loadContent();
}

handleLoading();