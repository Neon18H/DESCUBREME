(() => {
  const root = document.documentElement;
  const toggle = document.getElementById('darkModeToggle');
  const theme = localStorage.getItem('theme') || 'light';
  root.setAttribute('data-theme', theme);

  toggle?.addEventListener('click', () => {
    const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
  });

  const form = document.getElementById('planForm');
  const summary = document.getElementById('selectionSummary');
  const overlay = document.getElementById('loadingOverlay');

  const updateSummary = () => {
    if (!form || !summary) return;
    const data = new FormData(form);
    const interests = data.getAll('interests').join(', ') || 'ninguno';
    summary.textContent = `Ciudad: ${data.get('city') || '-'} | Mood: ${data.get('mood') || '-'} | Horario: ${data.get('start_time') || '-'}-${data.get('end_time') || '-'} | Presupuesto: $${data.get('budget') || 0} | Intereses: ${interests}`;
  };

  form?.addEventListener('change', updateSummary);
  form?.addEventListener('input', updateSummary);
  form?.addEventListener('submit', () => overlay?.classList.remove('d-none'));
  updateSummary();
})();
