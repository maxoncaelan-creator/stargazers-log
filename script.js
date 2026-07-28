const eventsList = document.getElementById('events-list');

async function loadEvents() {
  try {
    const response = await fetch('events.json');
    if (!response.ok) {
      throw new Error('Unable to load starred repositories');
    }

    const events = await response.json();

    eventsList.innerHTML = events
      .map(
        (event) => `
          <li class="event-item">
            <div class="event-title">
              <span>${event.repo}</span>
              <span class="event-date">${new Date(event.date).toLocaleDateString()}</span>
            </div>
            <p>${event.description}</p>
            <div class="event-meta">
              <span>${event.language || 'Mixed'}</span>
              <span>★ ${event.stars}</span>
            </div>
          </li>
        `
      )
      .join('');
  } catch (error) {
    eventsList.innerHTML = `<li class="event-item">${error.message}</li>`;
  }
}

loadEvents();
