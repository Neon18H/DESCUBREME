(function () {
  const promptInput = document.getElementById('chatPrompt');
  const generateBtn = document.getElementById('generatePlanBtn');
  const resultsRoot = document.getElementById('resultsRoot');
  const loadingState = document.getElementById('loadingState');
  const errorNode = document.getElementById('planError');

  const getCookie = (name) => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
  };

  document.querySelectorAll('.password-toggle').forEach((button) => {
    button.addEventListener('click', () => {
      const input = document.getElementById(button.dataset.target);
      if (!input) return;
      const isPassword = input.getAttribute('type') === 'password';
      input.setAttribute('type', isPassword ? 'text' : 'password');
      button.innerHTML = `<i class="bi bi-eye${isPassword ? '-slash' : ''}"></i>`;
    });
  });

  if (!promptInput || !generateBtn || !resultsRoot || !loadingState) return;

  const loadingTemplate = () => `
    <div class="glass-card p-3 p-md-4 mb-3">
      <div class="d-flex align-items-center gap-2 mb-3 loading-copy">
        <span class="spinner-grow spinner-grow-sm" aria-hidden="true"></span>
        <span>Generando plan…</span>
      </div>
      <div class="row g-3">
        ${[1, 2, 3].map(() => `
          <div class="col-12 col-md-4">
            <div class="glass-card p-3 skeleton-card">
              <div class="skeleton skeleton-line mb-2"></div>
              <div class="skeleton skeleton-line short mb-2"></div>
              <div class="skeleton skeleton-line"></div>
            </div>
          </div>`).join('')}
      </div>
    </div>`;

  const render = (payload) => {
    const parsed = payload.parsed_request;
    resultsRoot.innerHTML = `
      <div class="glass-card p-3 p-md-4 fade-up mb-3">
        <h2 class="h4 mb-1">Plan en ${parsed.city}</h2>
        <p class="text-soft mb-0">${parsed.mood} · ${parsed.group} · Presupuesto COP ${Number(parsed.budget_cop).toLocaleString('es-CO')}</p>
      </div>
      ${payload.time_windows.map((window) => `
        <section class="result-block fade-up">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <h3 class="h5 mb-0">${window.label}</h3>
            <span class="chip">${window.start} - ${window.end}</span>
          </div>
          <div class="row g-3">
            ${(window.places || []).map((place) => `
              <div class="col-12 col-md-6 col-xl-4">
                <article class="place-card h-100">
                  <div class="place-image" style="background-image:url('${place.photo_url || ''}')"></div>
                  <div class="p-3">
                    <h4 class="h6">${place.name}</h4>
                    <p class="small text-soft mb-2">⭐ ${place.rating || 'N/A'} · ${(place.user_ratings_total || 0)} reseñas</p>
                    <p class="small text-soft mb-3">Costo: ${place.estimated_cost_cop ? `COP ${Number(place.estimated_cost_cop).toLocaleString('es-CO')}` : 'No disponible'}</p>
                    <div class="d-flex gap-2">
                      <a class="btn btn-sm app-btn app-btn-secondary" target="_blank" href="${place.maps_url}">Maps</a>
                      <button class="btn btn-sm app-btn app-btn-primary js-save" data-window='${JSON.stringify(window)}' data-place='${JSON.stringify(place)}' data-parsed='${JSON.stringify(parsed)}' data-prompt="${payload.prompt.replace(/"/g, '&quot;')}">Guardar</button>
                    </div>
                  </div>
                </article>
              </div>`).join('')}
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
        } catch (_error) {
          button.textContent = 'Error';
        }
      });
    });
  };

  const submitPrompt = async () => {
    const prompt = promptInput.value.trim();
    errorNode.classList.add('d-none');
    if (prompt.length < 8) {
      errorNode.textContent = 'Escribe una descripción más completa.';
      errorNode.classList.remove('d-none');
      return;
    }

    resultsRoot.innerHTML = '';
    loadingState.classList.remove('d-none');
    loadingState.innerHTML = loadingTemplate();
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
      loadingState.classList.add('d-none');
      loadingState.innerHTML = '';
      generateBtn.disabled = false;
    }
  };

  generateBtn.addEventListener('click', submitPrompt);
  promptInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      submitPrompt();
    }
  });
})();
