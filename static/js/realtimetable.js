    document.addEventListener('DOMContentLoaded', function() {
        // Function to refresh only the table contents
        function refreshTable() {
            // Get current URL with all filter parameters
            const currentUrl = window.location.href;
            
            // Fetch the current page with the same filters
            fetch(currentUrl)
                .then(response => response.text())
                .then(html => {
                    // Create a temporary element to parse the HTML
                    const tempElement = document.createElement('div');
                    tempElement.innerHTML = html;
                    
                    // Extract just the table content from the fetched page
                    const newTableContent = tempElement.querySelector('.table-responsive');
                    
                    // Replace only the table content in the current page
                    if (newTableContent) {
                        document.querySelector('.table-responsive').innerHTML = newTableContent.innerHTML;
                        
                        // Also update the count badge
                        const newCountBadge = tempElement.querySelector('.badge');
                        if (newCountBadge) {
                            document.querySelector('.badge').innerHTML = newCountBadge.innerHTML;
                        }
                    }
                })
                .catch(error => {
                    console.error('Error refreshing table:', error);
                });
        }
        
        // Set interval to refresh table every 5 seconds (5000 ms)
        const refreshInterval = setInterval(refreshTable, 5000);
        
        // Add event listeners to stop refreshing when user is interacting with filters
        const filterForm = document.querySelector('form');
        const formControls = filterForm.querySelectorAll('input, select');
        
        formControls.forEach(control => {
            control.addEventListener('focus', () => {
                // Pause auto-refresh when user is interacting with filters
                clearInterval(refreshInterval);
            });
            
            control.addEventListener('blur', () => {
                // Resume auto-refresh when user stops interacting with filters
                clearInterval(refreshInterval); // Clear any existing interval
                refreshInterval = setInterval(refreshTable, 5000);
            });
        });
    });
