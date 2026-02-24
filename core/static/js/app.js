(function () {
  const csrf = () => (window.getCSRFToken ? window.getCSRFToken() : '');

  document.querySelectorAll('.js-like-plan').forEach((button) => {
    button.addEventListener('click', async () => {
      const response = await fetch(`/plan/${button.dataset.planId}/like`, {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'X-CSRFToken': csrf() },
      });
      if (!response.ok) return;
      const data = await response.json();
      button.querySelector('.js-like-count').textContent = data.likes_count;
      button.querySelector('i').className = `bi bi-heart${data.liked ? '-fill' : ''}`;
    });
  });

  document.querySelectorAll('.js-toggle-public').forEach((button) => {
    button.addEventListener('click', async () => {
      const response = await fetch(`/plan/${button.dataset.planId}/toggle-public`, {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'X-CSRFToken': csrf() },
      });
      if (!response.ok) return;
      const data = await response.json();
      button.textContent = data.is_public ? 'Público' : 'Compartir';
    });
  });
})();
