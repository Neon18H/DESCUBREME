(function () {
  const promptInput = document.getElementById('chatPrompt');
  const generateBtn = document.getElementById('generatePlanBtn');
  const resultsRoot = document.getElementById('resultsRoot');
  const errorNode = document.getElementById('planError');

  if (!promptInput || !generateBtn || !resultsRoot) return;

  const getCookie = (name) => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
  };

  const skeleton = () => `
    <div class="row g-3">
      ${[1, 2, 3].map(() => `
      <div class="col-md-4">
        <div class="glass-card p-3">
          <div class="skeleton skeleton-image mb-3"></div>
          <div class="skeleton skeleton-line mb-2"></div>
          <div class="skeleton skeleton-line short"></div>
        </div>
      </div>`).join('')}
    </div>`;

  const render = (payload) => {
    const parsed = payload.parsed_request;
    resultsRoot.innerHTML = `
      <div class="mb-4 fade-up">
        <h2 class="text-white">Plan en ${parsed.city}</h2>
        <p class="text-soft mb-0">Mood: ${parsed.mood} · Grupo: ${parsed.group} · Presupuesto: COP ${Number(parsed.budget_cop).toLocaleString('es-CO')}</p>
      </div>
      ${payload.time_windows.map((window) => `
        <section class="mb-4 fade-up">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <h3 class="h4 text-white mb-0">${window.label}</h3>
            <span class="badge bg-dark-subtle text-white">${window.start} - ${window.end}</span>
          </div>
          <div class="row g-3">
            ${(window.places || []).map((place) => `
              <div class="col-12 col-md-6 col-xl-4">
                <article class="glass-card place-card h-100">
                  <div class="place-image" style="background-image:url('${place.photo_url || ''}')"><div class="overlay"></div></div>
                  <div class="p-3">
                    <h4 class="h5 text-white">${place.name}</h4>
                    <p class="small text-soft mb-2">⭐ ${place.rating || 'N/A'} · ${(place.user_ratings_total || 0)} reseñas</p>
                    <p class="small text-soft mb-3">Costo aprox: ${place.estimated_cost_cop ? `COP ${Number(place.estimated_cost_cop).toLocaleString('es-CO')}` : 'No disponible'}</p>
                    <div class="d-flex gap-2">
                      <a class="btn btn-sm btn-light" target="_blank" href="${place.maps_url}">Abrir Maps</a>
                      <button class="btn btn-sm btn-outline-light js-save" data-window='${JSON.stringify(window)}' data-place='${JSON.stringify(place)}' data-parsed='${JSON.stringify(parsed)}' data-prompt="${payload.prompt.replace(/"/g, '&quot;')}">Guardar</button>
                    </div>
                  </div>
                </article>
              </div>
            `).join('')}
          </div>
        </section>`).join('')}
    `;

    document.querySelectorAll('.js-save').forEach((button) => {
      button.addEventListener('click', async () => {
        try {
          const response = await fetch('/api/save-place/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({
              prompt: button.dataset.prompt,
              window: JSON.parse(button.dataset.window),
              place: JSON.parse(button.dataset.place),
              parsed_request: JSON.parse(button.dataset.parsed),
            }),
          });
          if (response.status === 403) {
            window.location.href = '/auth/login/?next=/';
            return;
          }
          const data = await response.json();
          if (!response.ok) throw new Error(data.error || 'No se pudo guardar');
          button.textContent = 'Guardado ✓';
          button.disabled = true;
        } catch (error) {
          button.textContent = 'Error';
        }
      });
    });
  };

  generateBtn.addEventListener('click', async () => {
    const prompt = promptInput.value.trim();
    errorNode.classList.add('d-none');
    if (prompt.length < 8) {
      errorNode.textContent = 'Escribe una descripción más completa.';
      errorNode.classList.remove('d-none');
      return;
    }

    resultsRoot.innerHTML = skeleton();
    generateBtn.disabled = true;

    try {
      const response = await fetch('/api/generate-plan/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ prompt }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || 'Error generando plan');
      render(payload);
    } catch (error) {
      resultsRoot.innerHTML = '';
      errorNode.textContent = error.message;
      errorNode.classList.remove('d-none');
    } finally {
      generateBtn.disabled = false;
    }
  });
})();
