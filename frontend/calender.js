document.addEventListener('DOMContentLoaded', () => {
    const daysGrid = document.querySelector('.days-grid');

    // Generate days for the calendar (assuming 30 days for example)
    for (let day = 1; day <= 30; day++) {
        const dayDiv = document.createElement('div');
        dayDiv.classList.add('day');
        dayDiv.textContent = day;
        // TODO: Assign mood classes based on data (for now we'll just randomize for the example)
        const mood = ['good-mood', 'mid-mood', 'bad-mood', 'not-completed'];
        dayDiv.classList.add(mood[Math.floor(Math.random() * mood.length)]);
        daysGrid.appendChild(dayDiv);
    }

    // TODO: Add event listeners to the previous and next buttons for navigation
    const prevMonthBtn = document.getElementById('prev-month');
    const nextMonthBtn = document.getElementById('next-month');

    prevMonthBtn.addEventListener('click', () => {
        // Go to the previous month
    });

    nextMonthBtn.addEventListener('click', () => {
        // Go to the next month
    });
});
