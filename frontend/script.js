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

    // Function to create and return a new entry anchor
    function createEntryAnchor(entry, index) {
        const entryAnchor = document.createElement('a');
        // You can change this href to point to the actual URL or use a routing mechanism
        // If you have individual pages for each entry, the href would be the URL to that page
        entryAnchor.href = `#entry${index}`; 
        entryAnchor.classList.add('diary-entry');
        entryAnchor.innerHTML = `<h3>${entry.content}</h3><p>${entry.date}</p>`;
        entryAnchor.addEventListener('click', function(event) {
            event.preventDefault();
            // Implement the logic to handle click event here.
            // For instance, you could show the entry content in a modal or navigate to a detail page.
            console.log(`You clicked on ${entry.content}`);
        });
        return entryAnchor;
    }

    entries.forEach((entry, index) => {
        // Add entry to main entries section
        entriesSection.appendChild(createEntryAnchor(entry, index));

        // Add entry to favorites if applicable
        if (entry.favorite) {
            favoritesSection.appendChild(createEntryAnchor(entry, index));
        }
    });

    // Add the most recent entries to the 'Recents' section
    // Let's assume we want the 3 most recent entries
    const recentEntries = entries.slice(-3);
    recentEntries.forEach((entry, index) => {
        recentsSection.appendChild(createEntryAnchor(entry, index));
    });
});
