
function getBetaStatus() {
    return localStorage.getItem('betaStatus');
  }
  
  function setBetaAccepted() {
    localStorage.setItem('betaStatus', 'accepted');
  }
  
  // Show the beta banner
  function showBetaBanner() {
    const banner = document.getElementById('beta-banner');
    banner.innerHTML = `
      <div class="cookie-banner">
      <div class="inner-tile">
        <b>Beta Notice</b><br>
        <p>GrütteStorage is currently in beta and may be unstable. Please excuse any weird behavior. We currently cannot guarantee the availability of your uploaded files. By using GrütteStorage you agree to this.</p><br>
        <div style="display: inline;">
          <button id="accept-beta" class="cookie-button">Accept</button>
        </div><br>
        <div style="display: inline;">
          <a href="about" style="color: var(--text-color);">Über Uns</a> | 
          <a href="help" style="color: var(--text-color);">Help</a> | 
          <a href="privacy" style="color: var(--text-color);">Privacy</a>
        </div>
      </div>
    </div>
    `;
    banner.style.display = 'block';
  
    document.getElementById('accept-beta').addEventListener('click', () => {
      setBetaAccepted();
      banner.style.display = 'none';
    });
  }
  
  // Hide the beta banner if betas are already accepted or declined
  function hideBetaBannerIfAccepted() {
    if (getBetaStatus() === 'accepted') {
      const banner = document.getElementById('beta-banner');
      banner.style.display = 'none';
    }
  }
  
  // Main function to handle the beta banner
  function handleBetaBanner() {
    if (getBetaStatus() !== 'accepted') {
      showBetaBanner();
    }
  }
  
  // Call the main function to handle the beta banner
  handleBetaBanner();
  
  // Check for beta acceptance or decline on page load
  hideBetaBannerIfAccepted();
  