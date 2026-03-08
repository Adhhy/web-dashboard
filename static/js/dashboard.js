document.addEventListener('DOMContentLoaded', function () {
    const logoutBtn = document.getElementById('logout-btn');

    if (logoutBtn) {
        logoutBtn.addEventListener('click', async function () {
            try {
                const response = await fetch('/auth/logout', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                if (response.ok) {
                    // Redirect to login page on success
                    window.location.href = '/';
                } else {
                    console.error('Logout failed');
                    alert('Logout failed. Please try again.');
                }
            } catch (error) {
                console.error('Logout error:', error);
                alert('An error occurred during logout.');
            }
        });
    }
});
