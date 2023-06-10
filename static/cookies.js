// Check if the cookie has been accepted
function isCookieAccepted() {
  return localStorage.getItem('cookieAccepted') === 'true';
}

// Set the cookie as accepted
function setCookieAccepted() {
  localStorage.setItem('cookieAccepted', 'true');
}

// Load fonts based on cookie acceptance
function loadFonts() {
  const link = document.createElement('link');
  link.rel = 'stylesheet';

  if (isCookieAccepted()) {
    link.href = 'https://fonts.googleapis.com/css2?family=Nunito:wght@700&display=swap';
  } else {
    link.href = 'https://jan.gruettefien.com/static/Nunito/static/Nunito-SemiBold.ttf';
  }

  document.head.appendChild(link);
}

// Show the cookie banner
function showCookieBanner() {
  const banner = document.getElementById('cookie-banner');
  banner.innerHTML = `
  <div class="cookie-banner">
    <div class="inner-tile">
      <b>Cookie Policy</b><br>
      <p>This website uses cookies and loads content from Google and GitHub (USA). Your IP-address will be visible to these companies. By clicking "Accept" you consent to <a href="privacy" style="color: var(--text-color);">our</a> and their privacy policies.</p><br>
      <button id="accept-cookie" class="cookie-button">Accept</button><br>
      <div style="display: inline;">
        <a href="about" style="color: var(--text-color);">About</a> | 
        <a href="help" style="color: var(--text-color);">Help</a> | 
        <a href="privacy" style="color: var(--text-color);">Privacy</a>
      </div>
    </div>
  </div>
  `;
  banner.style.display = 'block';

  document.getElementById('accept-cookie').addEventListener('click', () => {
    setCookieAccepted();
    banner.style.display = 'none';
    loadFonts();
  });
}

// Hide the cookie banner if cookies are already accepted
function hideCookieBannerIfAccepted() {
  if (isCookieAccepted()) {
    const banner = document.getElementById('cookie-banner');
    banner.style.display = 'none';
    loadFonts();
  }
}

// Main function to handle the cookie banner
function handleCookieBanner() {
  if (!isCookieAccepted()) {
    showCookieBanner();
  } else {
    loadFonts();
  }
}

// Call the main function to handle the cookie banner
handleCookieBanner();

// Check for cookie acceptance on page load
hideCookieBannerIfAccepted();
