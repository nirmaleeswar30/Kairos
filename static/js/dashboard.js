// Dashboard.js - Handles dashboard functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize any charts or data visualizations
    initCharts();
    
    // Set up event listeners
    setupEventListeners();
    
    // Update the current time
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);
});

/**
 * Initialize charts on the dashboard
 */
function initCharts() {
    // Only initialize charts if the container exists
    const attendanceChartElement = document.getElementById('attendanceChart');
    if (attendanceChartElement) {
        // Create a placeholder attendance chart
        new Chart(attendanceChartElement, {
            type: 'bar',
            data: {
                labels: ['Loading...'],
                datasets: [{
                    label: 'Attendance',
                    data: [0],
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Count'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    }
                }
            }
        });
        
        // Load actual attendance data
        fetch('/api/attendance-data')
            .then(response => response.json())
            .then(data => {
                // Update the chart with the real data
                attendanceChartElement.chart.data.labels = data.labels;
                attendanceChartElement.chart.data.datasets[0].data = data.data;
                attendanceChartElement.chart.update();
            })
            .catch(error => console.error('Error loading attendance data:', error));
    }
    
    // Only initialize parking chart if the container exists
    const parkingChartElement = document.getElementById('parkingChart');
    if (parkingChartElement) {
        // Load parking data
        fetch('/api/parking-data')
            .then(response => response.json())
            .then(data => {
                // Create a doughnut chart for parking status
                new Chart(parkingChartElement, {
                    type: 'doughnut',
                    data: {
                        labels: ['Occupied', 'Free'],
                        datasets: [{
                            data: [data.occupied, data.free],
                            backgroundColor: [
                                'rgba(255, 99, 132, 0.2)',
                                'rgba(75, 192, 192, 0.2)'
                            ],
                            borderColor: [
                                'rgba(255, 99, 132, 1)',
                                'rgba(75, 192, 192, 1)'
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'top',
                            },
                            title: {
                                display: true,
                                text: 'Parking Space Status'
                            }
                        }
                    }
                });
            })
            .catch(error => console.error('Error loading parking data:', error));
    }
    
    // Only initialize plate chart if the container exists
    const plateChartElement = document.getElementById('plateChart');
    if (plateChartElement) {
        // Load plate detection data
        fetch('/api/plate-data')
            .then(response => response.json())
            .then(data => {
                // Create a line chart for plate detections
                new Chart(plateChartElement, {
                    type: 'line',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Plate Detections',
                            data: data.data,
                            fill: false,
                            borderColor: 'rgba(153, 102, 255, 1)',
                            tension: 0.1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: 'Count'
                                }
                            },
                            x: {
                                title: {
                                    display: true,
                                    text: 'Date'
                                }
                            }
                        }
                    }
                });
            })
            .catch(error => console.error('Error loading plate data:', error));
    }
}

/**
 * Set up event listeners for dashboard elements
 */
function setupEventListeners() {
    // Feature selection buttons
    const featureButtons = document.querySelectorAll('.feature-card');
    featureButtons.forEach(button => {
        button.addEventListener('click', function() {
            window.location.href = this.dataset.url;
        });
    });
}

/**
 * Update the current time display
 */
function updateCurrentTime() {
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        const now = new Date();
        timeElement.textContent = now.toLocaleTimeString();
    }
}
