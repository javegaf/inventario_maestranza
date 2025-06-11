document.addEventListener('DOMContentLoaded', function() {
        const blockModal = document.getElementById('blockModal');
        const blockForm = document.getElementById('blockForm');
        const motivoGroup = document.getElementById('motivoGroup');
        const unblockWarning = document.getElementById('unblockWarning');
        const modalTitle = document.querySelector('#blockModalLabel');
        const motivoTextarea = document.getElementById('motivo');
        
        // Setup modal when button is clicked
        document.querySelectorAll('.btn-toggle-block').forEach(button => {
            button.addEventListener('click', function() {
                const productoId = this.getAttribute('data-producto-id');
                const action = this.getAttribute('data-action');
                
                // Set form action URL
                blockForm.action = `/productos/${productoId}/toggle-block/`;
                
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
    });
