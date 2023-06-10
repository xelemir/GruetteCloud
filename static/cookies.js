
// Check if the cookie has been accepted or declined
function getCookieStatus() {
  return localStorage.getItem('cookieStatus');
}

// Set the cookie status as accepted
function setCookieAccepted() {
  localStorage.setItem('cookieStatus', 'accepted');
}

// Set the cookie status as declined
function setCookieDeclined() {
  localStorage.setItem('cookieStatus', 'declined');
}

// Load fonts based on cookie status
function loadFonts() {
  const link = document.createElement('link');
  link.rel = 'stylesheet';

  if (getCookieStatus() === 'accepted') {
    link.href = 'https://fonts.googleapis.com/css2?family=Nunito:wght@600&display=swap';
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
      <p>This website uses cookies and loads content from Google and GitHub (USA). Your IP-address will be visible to these companies. By clicking "Accept" you consent to <a href="privacy" style="color: var(--text-color);">our</a> and their privacy policies. If you decline you will have ugly icons and fonts.</p><br>
      <div style="display: inline;">
        <button id="accept-cookie" class="cookie-button">Accept</button>
        <button id="decline-cookie" class="cookie-button">Decline</button>
      </div><br>
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

  document.getElementById('decline-cookie').addEventListener('click', () => {
    setCookieDeclined();
    banner.style.display = 'none';
    loadFonts();
  });
}

// Hide the cookie banner if cookies are already accepted or declined
function hideCookieBannerIfAcceptedOrDeclined() {
  if (getCookieStatus() === 'accepted' || getCookieStatus() === 'declined') {
    const banner = document.getElementById('cookie-banner');
    banner.style.display = 'none';
    loadFonts();
  }
}

// Main function to handle the cookie banner
function handleCookieBanner() {
  if (getCookieStatus() !== 'accepted') {
    showCookieBanner();
  } else {
    loadFonts();
  }
}

// Call the main function to handle the cookie banner
handleCookieBanner();

// Check for cookie acceptance or decline on page load
hideCookieBannerIfAcceptedOrDeclined();
