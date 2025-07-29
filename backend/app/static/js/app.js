// app.js - Minimal JS for LIM OS frontend (progressive enhancement only)

// Mobile navigation toggle
function toggleMobileMenu() {
    const menu = document.getElementById('navbar-menu');
    const toggle = document.querySelector('.navbar-toggle');
    
    if (menu && toggle) {
        menu.classList.toggle('mobile-open');
        toggle.classList.toggle('active');
    }
}

// User dropdown toggle
function toggleUserDropdown() {
    const dropdown = document.getElementById('user-dropdown');
    
    if (dropdown) {
        dropdown.classList.toggle('show');
    }
}

// Close dropdowns when clicking outside
document.addEventListener('click', function(event) {
    const dropdown = document.getElementById('user-dropdown');
    const toggle = document.querySelector('.nav-dropdown-toggle');
    
    if (dropdown && !toggle?.contains(event.target)) {
        dropdown.classList.remove('show');
    }
});

// Close mobile menu when clicking on a link
document.addEventListener('click', function(event) {
    if (event.target.matches('.navbar-menu a')) {
        const menu = document.getElementById('navbar-menu');
        const toggle = document.querySelector('.navbar-toggle');
        
        if (menu && toggle) {
            menu.classList.remove('mobile-open');
            toggle.classList.remove('active');
        }
    }
}); 