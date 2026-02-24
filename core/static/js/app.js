(function () {
  const getCookie = (name) => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
  };

  const promptInput = document.getElementById('chatPrompt');
  const generateBtn = document.getElementById('generatePlanBtn');
  const resultsRoot = document.getElementById('resultsRoot');
  const loadingState = document.getElementById('loadingState');
  const errorNode = document.getElementById('planError');

  const bindSocialActions = () => {
    document.querySelectorAll('.js-like-plan').forEach((button) => {
      button.addEventListener('click', async () => {
        const response = await fetch(`/plan/${button.dataset.planId}/like`, {
          method: 'POST',
          credentials: 'same-origin',
          headers: { 'X-CSRFToken': getCookie('csrftoken') },
        });
        if (!response.ok) return;
        const data = await response.json();
        button.querySelector('.js-like-count').textContent = data.likes_count;
        button.querySelector('i').className = `bi bi-heart${data.liked ? '-fill' : ''}`;
      });
    });

    document.querySelectorAll('.js-copy-link').forEach((button) => {
      button.addEventListener('click', async () => {
        await navigator.clipboard.writeText(button.dataset.link);
        button.textContent = 'Enlace copiado ✓';
      });
    });

    document.querySelectorAll('.js-toggle-public').forEach((button) => {
      button.addEventListener('click', async () => {
        const response = await fetch(`/plan/${button.dataset.planId}/toggle-public`, {
          method: 'POST',
          credentials: 'same-origin',
          headers: { 'X-CSRFToken': getCookie('csrftoken') },
        });
        const data = await response.json();
        if (data.is_public) {
          button.textContent = 'Público';
          alert(`Link para compartir: ${window.location.origin}${data.share_url}`);
        } else {
          button.textContent = 'Compartir';
        }
      });
    });
  };

  bindSocialActions();

  if (!promptInput || !generateBtn || !resultsRoot || !loadingState) return;

  const render = (payload) => {
    const parsed = payload.parsed_request;
    resultsRoot.innerHTML = `
      <div class="glass-card p-3 p-md-4 fade-up mb-3">
        <h2 class="h4 mb-1">Plan en ${parsed.city}</h2>
        <p class="text-soft mb-2">${parsed.mood} · ${parsed.group} · Presupuesto COP ${Number(parsed.budget_cop).toLocaleString('es-CO')}</p>
        <button class="btn app-btn app-btn-primary btn-sm js-save-plan">Guardar plan</button>
      </div>
      ${payload.time_windows.map((window) => `
        <section class="result-block fade-up">
          <h3 class="h5 mb-2">${window.label}</h3>
          <div class="row g-3">
            ${(window.places || []).map((place) => `
              <div class="col-12 col-md-6 col-xl-4">
                <article class="place-card h-100">
                  <div class="place-image" style="background-image:url('${place.photo_url || ''}')"></div>
                  <div class="p-3"><h4 class="h6">${place.name}</h4><p class="small text-soft mb-0">⭐ ${place.rating || 'N/A'}</p></div>
                </article>
              </div>`).join('')}
          </div>
        </section>`).join('')}
    `;

    document.querySelector('.js-save-plan').addEventListener('click', async (event) => {
      const response = await fetch('/api/save-plan/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({
          ...payload,
          title: `Plan ${parsed.mood || ''} en ${parsed.city}`,
        }),
      });
      if (response.status === 302 || response.status === 403) {
        window.location.href = '/auth/login/?next=/';
        return;
      }
      const data = await response.json();
      event.target.textContent = 'Guardado ✓';
      event.target.disabled = true;
      if (data.detail_url) {
        const link = document.createElement('a');
        link.className = 'btn btn-sm app-btn app-btn-secondary ms-2';
        link.href = data.detail_url;
        link.textContent = 'Ver plan';
        event.target.after(link);
      }
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
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({ prompt }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error);
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
