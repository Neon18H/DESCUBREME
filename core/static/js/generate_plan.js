(function () {
  const promptInput = document.getElementById('chatPrompt');
  const generateBtn = document.getElementById('generatePlanBtn');
  const resultsRoot = document.getElementById('resultsRoot');
  const loadingState = document.getElementById('loadingState');
  const errorNode = document.getElementById('planError');
  if (!promptInput || !generateBtn || !resultsRoot || !loadingState) return;

  const latInput = document.getElementById('lat');
  const lngInput = document.getElementById('lng');
  const cityInput = document.getElementById('cityName');
  const shareInput = document.getElementById('isShared');
  let latestPayload = null;

  const render = (payload) => {
    latestPayload = payload;
    const parsed = payload.parsed_request;
    const cityName = payload.resolved_location?.city_name || parsed.city;
    document.getElementById('locationStatus').textContent = `Ubicación detectada: ${cityName} (aprox.)`;
    resultsRoot.innerHTML = `
      <div class="glass-card p-3 p-md-4 fade-up mb-3">
        <h2 class="h4 mb-1">Plan en ${cityName}</h2>
        <p class="text-soft mb-2">${parsed.mood} · ${parsed.group} · Presupuesto COP ${Number(parsed.budget_cop || 0).toLocaleString('es-CO')}</p>
        <button class="btn app-btn app-btn-primary btn-sm js-save-plan">Guardar plan</button>
      </div>
      ${payload.time_windows.map((window) => `
        <section class="result-block fade-up">
          <h3 class="h5 mb-2">${window.label}</h3>
          <div class="row g-3">
            ${(window.places || []).map((place) => `
              <div class="col-12 col-md-6 col-xl-4">
                <article class="place-card h-100">
                  <div class="place-image" style="background-image:linear-gradient(180deg, transparent, rgba(0,0,0,.5)),url('${place.photo_url || ''}')"></div>
                  <div class="p-3"><h4 class="h6">${place.name}</h4><p class="small text-soft mb-0">⭐ ${place.rating || 'N/A'} · ${place.address || ''}</p></div>
                </article>
              </div>`).join('')}
          </div>
        </section>`).join('')}
    `;

    document.querySelector('.js-save-plan').addEventListener('click', async (event) => {
      const response = await fetch('/api/save-plan/', {
        method: 'POST', credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.getCSRFToken() },
        body: JSON.stringify({
          ...latestPayload,
          city_name: cityName,
          country_code: payload.resolved_location?.country_code || 'CO',
          is_shared: shareInput.checked,
          title: `Plan ${parsed.mood || ''} en ${cityName}`,
        }),
      });
      if (!response.ok) return;
      const data = await response.json();
      event.target.textContent = 'Guardado ✓';
      event.target.disabled = true;
      if (data.detail_url) window.location.href = data.detail_url;
    });
  };

  const submitPrompt = async () => {
    const prompt = promptInput.value.trim();
    errorNode.classList.add('d-none');
    if (prompt.length < 8) return;

    loadingState.classList.remove('d-none');
    loadingState.innerHTML = '<div class="glass-card p-3">Generando plan…</div>';
    generateBtn.disabled = true;

    try {
      const response = await fetch('/api/generate-plan/', {
        method: 'POST', credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.getCSRFToken() },
        body: JSON.stringify({
          prompt,
          lat: latInput.value || null,
          lng: lngInput.value || null,
          city_name: cityInput.value || null,
        }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || 'No se pudo generar el plan.');
      render(payload);
    } catch (error) {
      errorNode.textContent = error.message;
      errorNode.classList.remove('d-none');
    } finally {
      loadingState.classList.add('d-none');
      generateBtn.disabled = false;
    }
  };

  generateBtn.addEventListener('click', submitPrompt);
})();
