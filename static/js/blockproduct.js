document.addEventListener('DOMContentLoaded', function() {
    console.log('Block product script loaded'); // DEBUG
    
    const blockModal = document.getElementById('blockModal');
    const blockForm = document.getElementById('blockForm');
    const motivoGroup = document.getElementById('motivoGroup');
    const unblockWarning = document.getElementById('unblockWarning');
    const modalTitle = document.querySelector('#blockModalLabel');
    const motivoTextarea = document.getElementById('motivo');
    
    console.log('Form element:', blockForm); // DEBUG
    
    // Setup modal when button is clicked
    document.querySelectorAll('.btn-toggle-block').forEach(button => {
        console.log('Found toggle button:', button); // DEBUG
        
        button.addEventListener('click', function(e) {
            console.log('Button clicked'); // DEBUG
            
            const productoId = this.getAttribute('data-producto-id');
            const action = this.getAttribute('data-action');
            
            console.log('Product ID:', productoId, 'Action:', action); // DEBUG
            
            // Set the correct form action URL
            const newAction = `/inventario/productos/${productoId}/toggle-block/`;
            blockForm.action = newAction;
            
            console.log('Form action set to:', newAction); // DEBUG
            
            // Configure modal based on action
            if (action === 'block') {
                modalTitle.textContent = 'Bloquear Producto';
                motivoGroup.style.display = 'block';
                unblockWarning.style.display = 'none';
                motivoTextarea.setAttribute('required', 'required');
            } else {
                modalTitle.textContent = 'Desbloquear Producto';
                motivoGroup.style.display = 'none';
                unblockWarning.style.display = 'block';
                motivoTextarea.removeAttribute('required');
            }
        });
    });
    
    // Also add a form submit handler to double-check
    if (blockForm) {
        blockForm.addEventListener('submit', function(e) {
            console.log('Form submitting to:', this.action); // DEBUG
            
            // If action is still wrong, prevent submission
            if (!this.action.includes('/inventario/')) {
                e.preventDefault();
                console.error('Wrong action URL, preventing submission');
                alert('Error: URL incorrecta. Por favor, refresca la página e intenta de nuevo.');
                return false;
            }
        });
    }
});
