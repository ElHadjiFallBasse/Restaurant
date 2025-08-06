// Restaurant Management System - JavaScript

$(document).ready(function() {
    
    // CSRF Token setup for AJAX requests
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    const csrftoken = getCookie('csrftoken');
    
    // Setup AJAX with CSRF token
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!this.crossDomain && !/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
    
    // Update Order Status
    $('.update-order-status').on('change', function() {
        const orderId = $(this).data('order-id');
        const newStatus = $(this).val();
        const statusElement = $(this).closest('tr').find('.order-status');
        
        $.ajax({
            url: `/orders/${orderId}/update-status/`,
            type: 'POST',
            data: {
                'status': newStatus
            },
            success: function(response) {
                if (response.success) {
                    statusElement.text(response.status);
                    statusElement.removeClass().addClass('badge order-status');
                    
                    // Add appropriate badge color
                    if (newStatus === 'paid') {
                        statusElement.addClass('bg-success');
                    } else if (newStatus === 'pending') {
                        statusElement.addClass('bg-warning');
                    } else if (newStatus === 'cancelled') {
                        statusElement.addClass('bg-danger');
                    } else {
                        statusElement.addClass('bg-info');
                    }
                    
                    showNotification('Statut mis à jour avec succès', 'success');
                } else {
                    showNotification('Erreur lors de la mise à jour', 'error');
                }
            },
            error: function() {
                showNotification('Erreur de communication', 'error');
            }
        });
    });
    
    // Toggle Table Availability
    $('.toggle-table').on('click', function(e) {
        e.preventDefault();
        const tableId = $(this).data('table-id');
        const tableCard = $(this).closest('.table-card');
        const statusElement = tableCard.find('.table-status');
        
        $.ajax({
            url: `/tables/${tableId}/toggle/`,
            type: 'POST',
            success: function(response) {
                if (response.success) {
                    if (response.is_available) {
                        tableCard.removeClass('occupied').addClass('available');
                        statusElement.text('Disponible').removeClass('text-danger').addClass('text-success');
                    } else {
                        tableCard.removeClass('available').addClass('occupied');
                        statusElement.text('Occupée').removeClass('text-success').addClass('text-danger');
                    }
                    showNotification(`Table ${response.status_text.toLowerCase()}`, 'success');
                } else {
                    showNotification('Erreur lors de la mise à jour', 'error');
                }
            },
            error: function() {
                showNotification('Erreur de communication', 'error');
            }
        });
    });
    
    // Search functionality with debounce
    let searchTimeout;
    $('.search-input').on('input', function() {
        clearTimeout(searchTimeout);
        const searchTerm = $(this).val();
        const form = $(this).closest('form');
        
        searchTimeout = setTimeout(function() {
            if (searchTerm.length >= 2 || searchTerm.length === 0) {
                form.submit();
            }
        }, 500);
    });
    
    // Auto-refresh dashboard every 30 seconds
    if (window.location.pathname === '/') {
        setInterval(function() {
            location.reload();
        }, 30000);
    }
    
    // Notification system
    function showNotification(message, type) {
        const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
        const notification = $(`
            <div class="alert ${alertClass} alert-dismissible fade show notification" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `);
        
        $('main').prepend(notification);
        
        // Auto-dismiss after 3 seconds
        setTimeout(function() {
            notification.alert('close');
        }, 3000);
    }
    
    // Confirm delete actions
    $('.confirm-delete').on('click', function(e) {
        if (!confirm('Êtes-vous sûr de vouloir supprimer cet élément ?')) {
            e.preventDefault();
        }
    });
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Form validation enhancement
    $('.needs-validation').on('submit', function(e) {
        if (this.checkValidity() === false) {
            e.preventDefault();
            e.stopPropagation();
        }
        $(this).addClass('was-validated');
    });
    
    // Dynamic form fields
    $('.add-form-row').on('click', function(e) {
        e.preventDefault();
        const formsetContainer = $(this).data('target');
        const totalForms = $(`#id_${formsetContainer}-TOTAL_FORMS`);
        const currentForms = parseInt(totalForms.val());
        
        // Clone the empty form
        const emptyForm = $(`.${formsetContainer}-form:last`).clone();
        
        // Update form indices
        emptyForm.html(emptyForm.html().replace(/__prefix__/g, currentForms));
        emptyForm.find('input, select, textarea').val('');
        
        // Insert new form
        $(`.${formsetContainer}-forms`).append(emptyForm);
        totalForms.val(currentForms + 1);
    });
    
    // Remove form row
    $(document).on('click', '.remove-form-row', function(e) {
        e.preventDefault();
        $(this).closest('.form-row').remove();
    });
    
    // Real-time clock
    function updateClock() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('fr-FR');
        $('.current-time').text(timeString);
    }
    
    if ($('.current-time').length) {
        updateClock();
        setInterval(updateClock, 1000);
    }
    
    // Smooth scrolling for anchor links
    $('a[href*="#"]').not('[href="#"]').not('[href="#0"]').click(function(event) {
        if (location.pathname.replace(/^\//, '') == this.pathname.replace(/^\//, '') && 
            location.hostname == this.hostname) {
            var target = $(this.hash);
            target = target.length ? target : $('[name=' + this.hash.slice(1) + ']');
            if (target.length) {
                event.preventDefault();
                $('html, body').animate({
                    scrollTop: target.offset().top - 70
                }, 1000);
            }
        }
    });
    
    // Print functionality
    $('.print-btn').on('click', function() {
        window.print();
    });
    
    // Export functionality (placeholder)
    $('.export-btn').on('click', function() {
        const format = $(this).data('format');
        showNotification(`Export ${format} en cours...`, 'success');
        // TODO: Implement actual export functionality
    });
    
    // Loading states for buttons
    $('.btn-loading').on('click', function() {
        const btn = $(this);
        const originalText = btn.text();
        btn.prop('disabled', true);
        btn.html('<span class="spinner-border spinner-border-sm me-2"></span>Chargement...');
        
        // Re-enable after 3 seconds (adjust based on actual operation)
        setTimeout(function() {
            btn.prop('disabled', false);
            btn.text(originalText);
        }, 3000);
    });
    
    // Keyboard shortcuts
    $(document).keydown(function(e) {
        // Ctrl+N for new order
        if (e.ctrlKey && e.keyCode === 78) {
            e.preventDefault();
            window.location.href = '/orders/create/';
        }
        
        // Ctrl+D for dashboard
        if (e.ctrlKey && e.keyCode === 68) {
            e.preventDefault();
            window.location.href = '/';
        }
    });
    
    // Add animation classes to elements as they come into view
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, observerOptions);
    
    // Observe all cards and tables
    document.querySelectorAll('.card, .table-card').forEach(el => {
        observer.observe(el);
    });
    
});

// Global functions
window.RestaurantManager = {
    showNotification: function(message, type) {
        const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
        const notification = $(`
            <div class="alert ${alertClass} alert-dismissible fade show notification" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `);
        
        $('main').prepend(notification);
        
        setTimeout(function() {
            notification.alert('close');
        }, 3000);
    },
    
    confirmAction: function(message) {
        return confirm(message || 'Êtes-vous sûr de vouloir effectuer cette action ?');
    }
};