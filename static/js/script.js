
// Function to confirm anbd then delete a tenant
document.addEventListener('DOMContentLoaded', function() {
    // Function to confirm and submit request deletion
    function confirmDelete(tenantId) {
        if (confirm("Are you sure you want to delete this tenant?")) {
            // If confirmed, submit the form to delete the tenant
            document.getElementById(`delete_tenant_form_${tenantId}`).submit();
        }
    }
    const deleteButtons = document.querySelectorAll('.delete-tenant-button');
    deleteButtons.forEach(button => {
        const tenantId = button.getAttribute('data-tenant-id');
        button.addEventListener('click', () => {
            confirmDelete(tenantId);
        });
    });
});


// Function to prompt for new apartment number and submit request to move tenant
function moveTenant(tenant_id) {
    var newApartmentNumber = prompt("Enter the new apartment number:");
    if (newApartmentNumber !== null) {
        fetch(`/move-tenant/${tenant_id}`, {
            method: 'POST',
            body: new URLSearchParams({ new_apartment_number: newApartmentNumber }),
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (!data.isError) {
                document.getElementById(`apartment_number_${tenant_id}`).textContent = newApartmentNumber;
            } else {
                alert(data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
}



document.addEventListener('DOMContentLoaded', function() {
    var searchInput = document.getElementById('searchInput');

    searchInput.addEventListener('keyup', function() {
        var searchValue = searchInput.value.toLowerCase();

        // Select all rows from the table
        var rows = document.querySelectorAll('.request-list table tbody tr');

        rows.forEach(function(row) {
            // Convert row's cells to an array to use some Array methods
            var cells = Array.from(row.getElementsByTagName('td'));
            var found = cells.some(function(cell) {
                return cell.textContent.toLowerCase().includes(searchValue);
            });
            // If the search term is found in any cell, show the row; otherwise, hide it
            row.style.display = found ? '' : 'none';
        });
    });
});

