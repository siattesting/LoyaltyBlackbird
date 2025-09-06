// PWA Install functionality
let deferredPrompt;
const installButton = document.getElementById('install-button');

window.addEventListener('beforeinstallprompt', (e) => {
  // Prevent Chrome 67 and earlier from automatically showing the prompt
  e.preventDefault();
  // Stash the event so it can be triggered later
  deferredPrompt = e;
  // Show install button
  if (installButton) {
    installButton.style.display = 'block';
  }
});

if (installButton) {
  installButton.addEventListener('click', (e) => {
    // Hide the app provided install promotion
    installButton.style.display = 'none';
    // Show the install prompt
    deferredPrompt.prompt();
    // Wait for the user to respond to the prompt
    deferredPrompt.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        console.log('User accepted the install prompt');
      } else {
        console.log('User dismissed the install prompt');
      }
      deferredPrompt = null;
    });
  });
}

// Register service worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/sw.js')
      .then((registration) => {
        console.log('SW registered: ', registration);
      })
      .catch((registrationError) => {
        console.log('SW registration failed: ', registrationError);
      });
  });
}

// Dashboard functionality
document.addEventListener('DOMContentLoaded', function() {
  // Auto-refresh dashboard stats
  function refreshStats() {
    fetch('/dashboard/stats')
      .then(response => response.json())
      .then(data => {
        // Update stats in the dashboard
        const balanceElement = document.getElementById('points-balance');
        if (balanceElement) {
          balanceElement.textContent = data.points_balance;
        }
        
        const earnedElement = document.getElementById('total-earned');
        if (earnedElement) {
          earnedElement.textContent = data.total_earned;
        }
        
        const spentElement = document.getElementById('total-spent');
        if (spentElement) {
          spentElement.textContent = data.total_spent;
        }
        
        const recentElement = document.getElementById('recent-transactions');
        if (recentElement) {
          recentElement.textContent = data.recent_transactions;
        }
      })
      .catch(error => console.error('Error refreshing stats:', error));
  }

  // Refresh stats every 30 seconds
  setInterval(refreshStats, 30000);

  // Transaction filtering
  const filterForm = document.getElementById('transaction-filters');
  if (filterForm) {
    const filterInputs = filterForm.querySelectorAll('select, input');
    filterInputs.forEach(input => {
      input.addEventListener('change', function() {
        const formData = new FormData(filterForm);
        const params = new URLSearchParams(formData);
        
        fetch(`/dashboard/transactions?${params}`, {
          headers: {
            'HX-Request': 'true'
          }
        })
        .then(response => response.text())
        .then(html => {
          const transactionList = document.getElementById('transaction-list');
          if (transactionList) {
            transactionList.innerHTML = html;
          }
        })
        .catch(error => console.error('Error filtering transactions:', error));
      });
    });
  }

  // Form validation
  const forms = document.querySelectorAll('form');
  forms.forEach(form => {
    form.addEventListener('submit', function(e) {
      const requiredFields = form.querySelectorAll('[required]');
      let isValid = true;
      
      requiredFields.forEach(field => {
        if (!field.value.trim()) {
          isValid = false;
          field.classList.add('error');
        } else {
          field.classList.remove('error');
        }
      });
      
      if (!isValid) {
        e.preventDefault();
        showAlert('Please fill in all required fields', 'error');
      }
    });
  });
});

// Utility functions
function showAlert(message, type = 'info') {
  const alertDiv = document.createElement('div');
  alertDiv.className = `alert alert-${type}`;
  alertDiv.textContent = message;
  
  const container = document.querySelector('.container') || document.body;
  container.insertBefore(alertDiv, container.firstChild);
  
  // Auto-remove after 5 seconds
  setTimeout(() => {
    alertDiv.remove();
  }, 5000);
}

// Copy to clipboard functionality
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    showAlert('Copied to clipboard!', 'success');
  }).catch(err => {
    console.error('Failed to copy: ', err);
    showAlert('Failed to copy to clipboard', 'error');
  });
}

// Background sync for offline form submissions
function syncFormData(formData, url) {
  if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
    navigator.serviceWorker.ready.then(registration => {
      // Store form data in cache
      caches.open('form-cache').then(cache => {
        cache.put(url, new Response(formData));
        // Register sync
        return registration.sync.register('background-sync');
      });
    });
  }
}
