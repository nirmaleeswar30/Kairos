// charts.js - Handles chart functionality for reports

document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts if on the reports page
    if (document.getElementById('attendanceChartContainer')) {
        initAttendanceChart();
    }
    
    if (document.getElementById('plateChartContainer')) {
        initPlateChart();
    }
    
    if (document.getElementById('parkingChartContainer')) {
        initParkingChart();
    }
});

/**
 * Initialize the attendance chart
 */
function initAttendanceChart() {
    // Fetch attendance data from the server
    fetch('/api/attendance-data')
        .then(response => response.json())
        .then(data => {
            // Create the chart
            const ctx = document.getElementById('attendanceChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Daily Attendance',
                        data: data.data,
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Number of Check-ins'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Date'
                            }
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: 'Attendance Over Time'
                        },
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error loading attendance data:', error);
            showChartError('attendanceChartContainer', 'Failed to load attendance data');
        });
}

/**
 * Initialize the license plate detection chart
 */
function initPlateChart() {
    // Fetch plate detection data from the server
    fetch('/api/plate-data')
        .then(response => response.json())
        .then(data => {
            // Create the chart
            const ctx = document.getElementById('plateChart').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'License Plate Detections',
                        data: data.data,
                        fill: false,
                        backgroundColor: 'rgba(153, 102, 255, 0.2)',
                        borderColor: 'rgba(153, 102, 255, 1)',
                        borderWidth: 1,
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Number of Detections'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Date'
                            }
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: 'License Plate Detections Over Time'
                        },
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error loading plate data:', error);
            showChartError('plateChartContainer', 'Failed to load plate detection data');
        });
}

/**
 * Initialize the parking space status chart
 */
function initParkingChart() {
    // Fetch parking data from the server
    fetch('/api/parking-data')
        .then(response => response.json())
        .then(data => {
            // Create the chart
            const ctx = document.getElementById('parkingChart').getContext('2d');
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Occupied Spaces', 'Free Spaces'],
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
                        title: {
                            display: true,
                            text: 'Current Parking Space Status'
                        },
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    }
                }
            });
            
            // Update the summary text
            const summaryElement = document.getElementById('parkingSummary');
            if (summaryElement) {
                summaryElement.innerHTML = `
                    <p><strong>Total Spaces:</strong> ${data.total}</p>
                    <p><strong>Occupied Spaces:</strong> ${data.occupied}</p>
                    <p><strong>Free Spaces:</strong> ${data.free}</p>
                    <p><strong>Occupancy Rate:</strong> ${Math.round((data.occupied / data.total) * 100)}%</p>
                `;
            }
        })
        .catch(error => {
            console.error('Error loading parking data:', error);
            showChartError('parkingChartContainer', 'Failed to load parking space data');
        });
}

/**
 * Show an error message when chart data fails to load
 */
function showChartError(containerId, message) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle"></i> ${message}
            </div>
        `;
    }
}
