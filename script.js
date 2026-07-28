const eventsList = document.getElementById('events-list');
const eventsStatus = document.getElementById('events-status');

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function formatDate(value) {
  if (!value) {
    return 'Unknown date';
  }

  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Unknown date' : date.toLocaleDateString();
}

function renderEvents(events) {
  if (!Array.isArray(events) || events.length === 0) {
    eventsList.innerHTML = '<li class="event-item">No starred repositories available yet.</li>';
    eventsStatus.textContent = 'No starred repositories available yet.';
    return;
  }

  const fragment = document.createDocumentFragment();

  events.forEach((event) => {
    const listItem = document.createElement('li');
    listItem.className = 'event-item';
    listItem.innerHTML = `
      <div class="event-title">
        <span>${escapeHtml(event.repo)}</span>
        <span class="event-date">${escapeHtml(formatDate(event.date))}</span>
      </div>
      <p>${escapeHtml(event.description || 'No description provided.')}</p>
      <div class="event-meta">
        <span>${escapeHtml(event.language || 'Mixed')}</span>
        <span>★ ${escapeHtml(event.stars ?? 0)}</span>
      </div>
    `;
    fragment.appendChild(listItem);
  });

  eventsList.replaceChildren(fragment);
  eventsStatus.textContent = `Loaded ${events.length} starred repositories.`;
}

async function loadEvents() {
  if (!eventsList || !eventsStatus) {
    return;
  }

  eventsStatus.textContent = 'Loading starred repositories…';
  eventsList.setAttribute('aria-busy', 'true');

  try {
    const response = await fetch('events.json');
    if (!response.ok) {
      throw new Error('Unable to load starred repositories');
    }

    const events = await response.json();
    renderEvents(events);
  } catch (error) {
    eventsList.innerHTML = `<li class="event-item">${escapeHtml(error.message || 'Unable to load starred repositories')}</li>`;
    eventsStatus.textContent = 'Unable to load starred repositories.';
  } finally {
    eventsList.setAttribute('aria-busy', 'false');
  }
}

loadEvents();
