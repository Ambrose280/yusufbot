// Get the container element
var navContainer = document.querySelector('nav ul');

// Get all buttons with class="nav-link" inside the container
var links = navContainer.getElementsByClassName('nav-link');

// Loop through the buttons and add the active class to the current/clicked button
for (var i = 0; i < links.length; i++) {
    links[i].addEventListener('click', function() {
        // Get the current active element
        var current = document.getElementsByClassName('active');

        // If there's an active element, remove the active class
        if (current.length > 0) {
            current[0].className = current[0].className.replace('active', '');
        }

        // Add the active class to the clicked element
        this.className += 'active';
    });
}
