document.addEventListener('DOMContentLoaded', function() {
    const entries = [
        { date: 'Wednesday 1 November 2023', content: 'Diary Entry #98', favorite: false },
        { date: 'Tuesday 31 October 2023', content: 'Diary Entry #97', favorite: true },
        { date: 'Monday 30 October 2023', content: 'Diary Entry #96', favorite: false },
        { date: 'Sunday 29 October 2023', content: 'Diary Entry #95', favorite: true },
        // Add more entries as needed
    ];

    const entriesSection = document.getElementById('entries');
    const favoritesSection = document.getElementById('favorites');
    const recentsSection = document.getElementById('recents');
    const searchInput = document.getElementById('searchEntries');

    // Function to create and return a new entry element
    function createEntryElement(entry, index) {
        const entryDiv = document.createElement('div');
        entryDiv.className = 'entry';
        entryDiv.innerHTML = `<h3>${entry.content}</h3><p>${entry.date}</p>`;
        // Add event listener if needed here
        return entryDiv;
    }

    // Function to filter entries by search query
    function filterEntries(query) {
        const lowerCaseQuery = query.toLowerCase();
        const filteredEntries = entries.filter(entry => 
            entry.content.toLowerCase().includes(lowerCaseQuery) ||
            entry.date.toLowerCase().includes(lowerCaseQuery)
        );
        updateEntriesDisplay(filteredEntries);
    }

    // Function to update the display of entries
    function updateEntriesDisplay(entriesToShow) {
        entriesSection.innerHTML = ''; // Clear current entries
        entriesToShow.forEach((entry, index) => {
            entriesSection.appendChild(createEntryElement(entry, index));
        });
    }

    // Attach event listener to search bar
    searchInput.addEventListener('keyup', function() {
        filterEntries(searchInput.value);
    });

    // Add entries to the main entries section
    entries.forEach((entry, index) => {
        entriesSection.appendChild(createEntryElement(entry, index));

        // Add entry to favorites if applicable
        if (entry.favorite) {
            const favEntry = createEntryElement(entry, index);
            favEntry.classList.add('favorite'); // Add class for favorite entries if needed
            favoritesSection.appendChild(favEntry);
        }
    });

    // Add the most recent entries to the 'Recents' section
    const recentEntries = entries.slice(-3).reverse(); // Assuming you want the latest first
    recentEntries.forEach((entry, index) => {
        recentsSection.appendChild(createEntryElement(entry, index));
    });

    // Initial display of entries
    updateEntriesDisplay(entries);
});
