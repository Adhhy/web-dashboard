document.addEventListener('DOMContentLoaded', function () {
    const loginForm = document.getElementById('login-form');
    const passwordInput = document.getElementById('password');
    const togglePassword = document.getElementById('toggle-password');
    const errorMessage = document.getElementById('error-message');

    // Password visibility toggle
    if (togglePassword) {
        togglePassword.addEventListener('click', function () {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);

            // Toggle eye icon (simple text swap for now, could use SVG switch)
            const icon = this.querySelector('svg');
            if (type === 'text') {
                icon.style.opacity = '0.5';
            } else {
                icon.style.opacity = '1';
            }
        });
    }

    // Role selection handling
    const roleButtons = document.querySelectorAll('.role-btn');
    let selectedRole = null;

    roleButtons.forEach(button => {
        button.addEventListener('click', function () {
            // Remove selection from all buttons
            roleButtons.forEach(btn => btn.classList.remove('selected'));

            // Add selection to clicked button
            this.classList.add('selected');
            selectedRole = this.getAttribute('data-role');

            console.log("Selected role:", selectedRole);
        });
    });

    // Form submission handling
    if (loginForm) {
        loginForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            // Enforce role selection
            if (!selectedRole) {
                errorMessage.textContent = 'Please select a role (Student, Advisor, Faculty, or Admin) before signing in.';
                return;
            }

            const username = document.getElementById('username').value;
            const password = passwordInput.value;

            // Clear previous error
            errorMessage.textContent = '';
            errorMessage.style.color = '#e53e3e'; // Error red

            try {
                const response = await fetch('/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ username, password, role: selectedRole })
                });

                const result = await response.json();

                if (response.ok && result.success) {
                    // Success: Display message and redirect to the URL provided by server
                    errorMessage.textContent = 'Login successful! Redirecting...';
                    errorMessage.style.color = '#38a169'; // Success green

                    setTimeout(() => {
                        window.location.href = result.redirect_url || '/dashboard';
                    }, 1000);
                } else {
                    // Failure: Display error message from server
                    errorMessage.textContent = result.message || 'Invalid username, password, or role.';
                }
            } catch (error) {
                console.error('Login error:', error);
                errorMessage.textContent = 'A connection error occurred. Please try again.';
            }
        });
    }
});
