document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelectorAll('nav ul li a');
    const tabContents = document.querySelectorAll('.tab-content');
    const contentArea = document.getElementById('content-area');

    // Function to hide all tabs
    function hideAllTabs() {
        tabContents.forEach(tab => {
            tab.style.display = 'none';
        });
    }

    // Function to show a specific tab
    function showTab(tabId) {
        const tabToShow = document.getElementById(tabId + '-content');
        if (tabToShow) {
            hideAllTabs();
            tabToShow.style.display = 'block';
        } else {
            // Optionally handle case where content doesn't exist
            console.warn(`Content section for ${tabId} not found.`);
            hideAllTabs(); // Hide others even if target not found
        }
    }

    // Add click event listeners to nav links
    navLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault(); // Prevent default anchor link behavior

            const tabId = this.getAttribute('data-tab');

            // Update active class on nav links
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');

            // Show the corresponding tab content
            showTab(tabId);
        });
    });

    // Show the default tab (e.g., 'accounts') on initial load
    const defaultTabLink = document.querySelector('nav ul li a[data-tab="accounts"]');
    if (defaultTabLink) {
        defaultTabLink.classList.add('active');
        showTab('accounts');
    } else {
        // Fallback if default tab doesn't exist
        hideAllTabs();
        if (tabContents.length > 0) {
            tabContents[0].style.display = 'block'; // Show the first tab available
             const firstNavLink = document.querySelector('nav ul li a');
             if(firstNavLink) firstNavLink.classList.add('active');
        }
    }

    // Basic form handling (prevent default submission for now)
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    if(loginForm) {
        loginForm.addEventListener('submit', function(event) {
            event.preventDefault();
            alert('Login functionality to be implemented.');
            // Here you would typically send data to a server
        });
    }

     if(registerForm) {
        registerForm.addEventListener('submit', function(event) {
            event.preventDefault();
            alert('Registration functionality to be implemented.');
             // Here you would typically send data to a server
        });
    }
}); 