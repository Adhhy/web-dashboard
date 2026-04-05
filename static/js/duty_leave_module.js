/**
 * Duty Leave Module JS (Legacy Integration)
 * Handles basic UI interactivity and Guidelines modal for the legacy templates.
 */

const DutyLeaveModule = {
    // Shared UI Helpers
    getStatusPillClass: (state) => {
        const mapping = {
            'PendingAdvisor': 'status-waiting',
            'PendingFaculty': 'status-waiting',
            'Locked': 'status-locked',
            'Approved': 'status-approved',
            'Rejected': 'status-rejected',
            'Completed': 'status-approved'
        };
        return mapping[state] || '';
    }
};

// Global Guidelines Modal Trigger (Defined in base.html)
window.openRulesModal = function() {
    const modal = document.getElementById('rules-modal');
    if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
};

window.closeRulesModal = function() {
    const modal = document.getElementById('rules-modal');
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    }
};

// Global export
window.DutyLeaveModule = DutyLeaveModule;
