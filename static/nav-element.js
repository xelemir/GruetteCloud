function toggleDropdown() {
    var dropdownMenu = document.querySelector('.dropdown-menu');
    dropdownMenu.classList.toggle('show');
  }
  
  // Close the dropdown when clicking outside of it
  window.addEventListener('click', function(event) {
    var dropdown = document.querySelector('.dropdown');
    if (!dropdown.contains(event.target)) {
      var dropdownMenu = document.querySelector('.dropdown-menu');
      dropdownMenu.classList.remove('show');
    }
  });
  