document.addEventListener('DOMContentLoaded', function() {
    // Card Actions - Freeze/Unfreeze Card
    const freezeButtons = document.querySelectorAll('.freeze-btn');
    freezeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const currentStatus = this.getAttribute('data-status');
            if (currentStatus === 'active') {
                this.setAttribute('data-status', 'frozen');
                this.textContent = 'Unfreeze Card';
                this.parentElement.previousElementSibling.classList.add('frozen-card');
            } else {
                this.setAttribute('data-status', 'active');
                this.textContent = 'Freeze Card';
                this.parentElement.previousElementSibling.classList.remove('frozen-card');
            }
        });
    });

    // Card Details Modal
    const detailsButtons = document.querySelectorAll('.details-btn');
    const cardDetailsModal = document.getElementById('card-details-modal');
    const closeButtons = document.querySelectorAll('.close-btn');
    
    detailsButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Get card details from the clicked card
            const card = this.parentElement.previousElementSibling;
            const cardPreview = card.cloneNode(true);
            
            // Populate the modal with card details
            document.querySelector('.card-preview').innerHTML = '';
            document.querySelector('.card-preview').appendChild(cardPreview);
            
            // Get specific card details for the info section
            const cardNumber = card.querySelector('.card-number').textContent;
            const cardHolder = card.querySelector('.holder-name').textContent;
            const expiryDate = card.querySelector('.valid-thru p:last-child').textContent;
            const cardType = card.classList.contains('mastercard') ? 'Mastercard' : 'Visa Debit';
            const cardStatus = this.nextElementSibling.getAttribute('data-status');
            
            // Update the info section
            document.getElementById('detail-card-number').textContent = cardNumber;
            document.getElementById('detail-card-holder').textContent = cardHolder;
            document.getElementById('detail-expiry').textContent = expiryDate;
            document.getElementById('detail-card-type').textContent = cardType;
            
            const statusElement = document.getElementById('detail-status');
            if (cardStatus === 'active') {
                statusElement.textContent = 'Active';
                statusElement.className = 'active-status';
            } else {
                statusElement.textContent = 'Frozen';
                statusElement.className = 'frozen-status';
            }
            
            // Load transaction data (in a real app, this would be from an API)
            loadTransactionData(cardNumber);
            
            // Display the modal
            cardDetailsModal.style.display = 'block';
        });
    });
    
    // Add New Card Modal
    const addCardButton = document.querySelector('.add-card-btn');
    const addCardModal = document.getElementById('add-card-modal');
    
    addCardButton.addEventListener('click', function() {
        addCardModal.style.display = 'block';
    });
    
    // Close Modals
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            this.closest('.modal').style.display = 'none';
        });
    });
    
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    });
    
    // Add Card Form Submission
    const addCardForm = document.getElementById('add-card-form');
    addCardForm.addEventListener('submit', function(event) {
        event.preventDefault();
        
        // Get form values
        const cardType = document.getElementById('card-type').value;
        const linkedAccount = document.getElementById('linked-account').value;
        const cardName = document.getElementById('card-name').value;
        
        // In a real app, this would send data to a server
        alert('Card request submitted successfully. Your new card will be processed shortly.');
        
        // Close the modal
        addCardModal.style.display = 'none';
    });
    
    // Function to load transaction data
    function loadTransactionData(cardNumber) {
        // In a real app, this would fetch data from an API
        // For this demo, we'll use static data
        const transactions = [
            {
                merchant: 'Naivas Supermarket',
                date: 'March 5, 2025',
                amount: 'KES 4,320.00',
                status: 'Successful'
            },
            {
                merchant: 'Java House Kenya',
                date: 'March 3, 2025',
                amount: 'KES 850.00',
                status: 'Successful'
            },
            {
                merchant: 'Shell Petrol Station',
                date: 'March 1, 2025',
                amount: 'KES 5,000.00',
                status: 'Successful'
            },
            {
                merchant: 'Netflix Subscription',
                date: 'February 28, 2025',
                amount: 'KES 1,100.00',
                status: 'Successful'
            }
        ];
        
        // Clear existing transactions
        const transactionList = document.getElementById('transaction-list');
        transactionList.innerHTML = '';
        
        // Add transactions to the table
        transactions.forEach(transaction => {
            const row = document.createElement('tr');
            
            const merchantCell = document.createElement('td');
            merchantCell.textContent = transaction.merchant;
            
            const dateCell = document.createElement('td');
            dateCell.textContent = transaction.date;
            
            const amountCell = document.createElement('td');
            amountCell.textContent = transaction.amount;
            
            const statusCell = document.createElement('td');
            const statusSpan = document.createElement('span');
            statusSpan.textContent = transaction.status;
            statusSpan.className = 'status success';
            statusCell.appendChild(statusSpan);
            
            row.appendChild(merchantCell);
            row.appendChild(dateCell);
            row.appendChild(amountCell);
            row.appendChild(statusCell);
            
            transactionList.appendChild(row);
        });
    }
    
    // Card Settings Toggles
    const toggleSwitches = document.querySelectorAll('.toggle-switch input');
    toggleSwitches.forEach(toggle => {
        toggle.addEventListener('change', function() {
            const setting = this.closest('.setting-item').querySelector('h3').textContent;
            const status = this.checked ? 'enabled' : 'disabled';
            
            // In a real app, this would update settings via an API
            console.log(`${setting} has been ${status}`);
        });
    });
    
    // Settings Manage Buttons
    const settingButtons = document.querySelectorAll('.setting-btn');
    settingButtons.forEach(button => {
        button.addEventListener('click', function() {
            const setting = this.closest('.setting-item').querySelector('h3').textContent;
            
            // In a real app, this would open specific settings pages
            alert(`${setting} management page will open here.`);
        });
    });
});