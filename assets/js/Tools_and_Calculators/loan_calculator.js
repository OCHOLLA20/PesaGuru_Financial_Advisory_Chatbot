function calculateLoan() {
    let loanAmount = parseFloat(document.getElementById("loan-amount").value) || 0;
    let interestRate = parseFloat(document.getElementById("interest-rate").value) || 0;
    let loanTerm = parseFloat(document.getElementById("loan-term").value) || 0;

    if (loanAmount <= 0 || interestRate < 0 || loanTerm <= 0) {
        alert("Please enter valid values.");
        return;
    }

    let monthlyRate = (interestRate / 100) / 12;
    let totalMonths = loanTerm * 12;
    let monthlyPayment = loanAmount * (monthlyRate / (1 - Math.pow(1 + monthlyRate, -totalMonths)));
    let totalPayment = monthlyPayment * totalMonths;
    let totalInterest = totalPayment - loanAmount;

    document.getElementById("monthly-payment").innerHTML = `📆 Monthly Payment: <strong>$${monthlyPayment.toFixed(2)}</strong>`;
    document.getElementById("total-payment").innerHTML = `💰 Total Payment: <strong>$${totalPayment.toFixed(2)}</strong>`;
    document.getElementById("total-interest").innerHTML = `📉 Total Interest: <strong>$${totalInterest.toFixed(2)}</strong>`;

    document.getElementById("result-container").style.display = "block";
}

function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
