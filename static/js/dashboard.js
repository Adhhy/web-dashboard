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

    const profileBtn = document.getElementById('profile-btn');
    const profileMenu = document.getElementById('profile-menu');

    if (profileBtn && profileMenu) {
        profileBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            profileMenu.classList.toggle('hidden');
        });

        document.addEventListener('click', function (e) {
            if (!profileBtn.contains(e.target) && !profileMenu.contains(e.target)) {
                profileMenu.classList.add('hidden');
            }
        });
    }

    // Change Password Modal Logic
    const changePwBtn = document.getElementById('change-password-btn');
    const changePwModal = document.getElementById('change-pw-modal');
    const cancelPwBtn = document.getElementById('cancel-pw-btn');
    const submitPwBtn = document.getElementById('submit-pw-btn');
    const changePwForm = document.getElementById('change-pw-form');
    const pwErrorAlert = document.getElementById('pw-error-alert');

    if (changePwBtn && changePwModal) {
        // Open modal
        changePwBtn.addEventListener('click', function(e) {
            e.preventDefault();
            changePwModal.classList.remove('hidden');
            if(profileMenu) profileMenu.classList.add('hidden'); // Close dropdown
        });

        // Close functions
        const closeModal = () => {
            changePwModal.classList.add('hidden');
            changePwForm.reset();
            pwErrorAlert.classList.add('hidden');
        };

        cancelPwBtn.addEventListener('click', closeModal);

        // Submit Logic
        submitPwBtn.addEventListener('click', async function() {
            const currentPw = document.getElementById('current-password').value;
            const newPw = document.getElementById('new-password').value;
            const confirmPw = document.getElementById('confirm-password').value;

            // Reset error
            pwErrorAlert.classList.add('hidden');
            pwErrorAlert.textContent = '';

            // Basic validation
            if (!currentPw || !newPw || !confirmPw) {
                pwErrorAlert.textContent = 'All fields are required.';
                pwErrorAlert.classList.remove('hidden');
                return;
            }

            if (newPw !== confirmPw) {
                pwErrorAlert.textContent = 'New password and confirm password do not match.';
                pwErrorAlert.classList.remove('hidden');
                return;
            }

            // Disable submit button while processing
            const originalBtnText = submitPwBtn.textContent;
            submitPwBtn.textContent = 'Updating...';
            submitPwBtn.disabled = true;

            try {
                const response = await fetch('/auth/change-password', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        current_password: currentPw,
                        new_password: newPw,
                        confirm_password: confirmPw
                    })
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    alert('Password changed successfully! You will now be redirected to login.');
                    window.location.href = '/';
                } else {
                    pwErrorAlert.textContent = data.message || 'Failed to change password. Please try again.';
                    pwErrorAlert.classList.remove('hidden');
                }
            } catch (error) {
                console.error('Change password error:', error);
                pwErrorAlert.textContent = 'A network error occurred. Please try again later.';
                pwErrorAlert.classList.remove('hidden');
            } finally {
                // Re-enable button
                submitPwBtn.textContent = originalBtnText;
                submitPwBtn.disabled = false;
            }
        });
    }
});
