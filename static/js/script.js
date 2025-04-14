document.addEventListener('DOMContentLoaded', () => {
    const searchButton = document.getElementById('search-flights-btn');
    const setAlertButton = document.getElementById('set-alert-btn');
    const showHistoryButton = document.getElementById('show-history-btn');

    if (searchButton) {
        searchButton.addEventListener('click', searchFlights);
    } else {
        console.error("Search button not found in DOM");
    }

    if (setAlertButton) {
        setAlertButton.addEventListener('click', setAlert);
    } else {
        console.error("Set Alert button not found in DOM");
    }

    if (showHistoryButton) {
        showHistoryButton.addEventListener('click', showHistory);
    } else {
        console.error("Show History button not found in DOM");
    }
});

async function searchFlights() {
    console.log("searchFlights() called");

    const origin = document.getElementById('origin').value;
    const destination = document.getElementById('destination').value;
    const depart_date = document.getElementById('depart_date').value;
    const adults = document.getElementById('adults').value;
    const cabin_class = document.getElementById('cabin_class').value;

    console.log("Inputs:", { origin, destination, depart_date, adults, cabin_class });

    try {
        const response = await fetch('/api/flights', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ origin, destination, depart_date, adults, cabin_class })
        });
        console.log("Fetch response:", response);

        const data = await response.json();
        console.log("Response data:", data);

        if (response.ok) {
            displayFlights(data);
        } else {
            alert(data.error || 'Failed to fetch flights');
        }
    } catch (error) {
        console.error("Fetch error:", error);
        alert('Error: ' + error.message);
    }
}

function displayFlights(flights) {
    console.log("displayFlights() called with data:", flights);

    const tbody = document.getElementById('flights-body');
    tbody.innerHTML = '';

    if (!flights || flights.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7">No flights found</td></tr>';
        return;
    }

    flights.forEach(flight => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${flight.airline}</td>
            <td>Rs. ${84*flight.price.toFixed(2)}</td>
            <td>${flight.departure_time}</td>
            <td>${flight.date_checked}</td>
            <td>${flight.origin}</td>
            <td>${flight.destination}</td>
            <td>${flight.depart_date}</td>
        `;
        tbody.appendChild(row);
    });
}

async function setAlert() {
    console.log("setAlert() called");

    const origin = document.getElementById('origin').value;
    const destination = document.getElementById('destination').value;
    const depart_date = document.getElementById('depart_date').value;
    const email = document.getElementById('email').value;

    try {
        const response = await fetch('/api/set_alert', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ origin, destination, depart_date, email })
        });
        const data = await response.json();

        if (response.ok) {
            alert(data.message);
        } else {
            alert(data.error || 'Failed to set alert');
        }
    } catch (error) {
        console.error("Set alert error:", error);
        alert('Error: ' + error.message);
    }
}

async function showHistory() {
    console.log("showHistory() called");

    const origin = document.getElementById('origin').value;
    const destination = document.getElementById('destination').value;
    const depart_date = document.getElementById('depart_date').value;

    try {
        const response = await fetch('/api/history', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ origin, destination, depart_date })
        });
        const data = await response.json();

        if (response.ok) {
            document.getElementById('history-section').style.display = 'block';
            displayChart(data);
        } else {
            alert(data.error || 'Failed to fetch history');
        }
    } catch (error) {
        console.error("Show history error:", error);
        alert('Error: ' + error.message);
    }
}

function displayChart(history) {
    console.log("displayChart() called with data:", history);

    const ctx = document.getElementById('price-chart').getContext('2d');
    const labels = history.map(item => new Date(item.date_checked).toLocaleDateString());
    const prices = history.map(item => item.price);

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Price (USD)',
                data: prices,
                borderColor: '#00aaff',
                backgroundColor: 'rgba(0, 170, 255, 0.2)',
                fill: true,
                tension: 0.1
            }]
        },
        options: {
            scales: {
                x: {
                    title: { display: true, text: 'Date Checked', color: '#ffffff' },
                    ticks: { color: '#ffffff' }
                },
                y: {
                    title: { display: true, text: 'Price (USD)', color: '#ffffff' },
                    ticks: { color: '#ffffff' }
                }
            },
            plugins: {
                legend: { labels: { color: '#ffffff' } }
            },
            responsive: true,
            maintainAspectRatio: false
        }
    });
}