(function () {
  const root = document.documentElement;
  const toggle = document.getElementById('darkModeToggle');
  const currentTheme = localStorage.getItem('theme') || 'light';
  root.setAttribute('data-theme', currentTheme);

  if (toggle) {
    toggle.addEventListener('click', function () {
      const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
    });
  }

  const form = document.getElementById('planForm');
  const overlay = document.getElementById('loadingOverlay');
  const summary = document.getElementById('selectionSummary');

  function updateSummary() {
    if (!form || !summary) return;
    const data = new FormData(form);
    const interests = data.getAll('interests').join(', ') || 'ninguno';
    summary.textContent = `Ciudad: ${data.get('city') || '-'} | Mood: ${data.get('mood') || '-'} | Horario: ${data.get('start_time') || '-'}-${data.get('end_time') || '-'} | Presupuesto: $${data.get('budget') || 0} | Intereses: ${interests}`;
  }

  if (form) {
    form.addEventListener('input', updateSummary);
    form.addEventListener('submit', function () {
      if (overlay) overlay.classList.remove('d-none');
    });
    updateSummary();
  }
})();
