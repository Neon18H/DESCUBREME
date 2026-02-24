(function () {
  const MAX_TAGS = 20;
  const MAX_TAG_LENGTH = 24;

  function parseSeed(raw) {
    if (!raw) return [];
    try {
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (_err) {
      return String(raw).split(',');
    }
  }

  function normalize(value) {
    return String(value || '').trim().slice(0, MAX_TAG_LENGTH);
  }

  function mountChips(box) {
    const hidden = document.getElementById(box.dataset.target);
    const input = box.querySelector('input');
    if (!hidden || !input) return;

    hidden.classList.add('d-none');
    const tags = [];

    function sync() {
      hidden.value = JSON.stringify(tags);
    }

    function addTag(raw) {
      const next = normalize(raw);
      if (!next || tags.length >= MAX_TAGS) return;
      if (tags.some((item) => item.toLowerCase() === next.toLowerCase())) return;
      tags.push(next);
    }

    function removeTag(index) {
      tags.splice(index, 1);
      render();
    }

    function render() {
      box.querySelectorAll('.chip').forEach((item) => item.remove());

      tags.forEach((tag, index) => {
        const chip = document.createElement('span');
        chip.className = 'chip';
        chip.textContent = tag;

        const close = document.createElement('button');
        close.type = 'button';
        close.className = 'chip-remove';
        close.innerHTML = '&times;';
        close.addEventListener('click', () => removeTag(index));

        chip.appendChild(close);
        box.insertBefore(chip, input);
      });

      sync();
    }

    parseSeed(box.dataset.initial || hidden.value).forEach(addTag);
    render();

    input.addEventListener('keydown', (event) => {
      if (event.key !== 'Enter' && event.key !== ',') return;
      event.preventDefault();
      addTag(input.value);
      input.value = '';
      render();
    });

    input.addEventListener('blur', () => {
      if (!input.value.trim()) return;
      addTag(input.value);
      input.value = '';
      render();
    });
  }

  function bindAvatarPreview() {
    const input = document.getElementById('id_avatar');
    const preview = document.getElementById('avatarPreview');
    const fallback = document.getElementById('avatarFallback');
    if (!input || !preview) return;

    input.addEventListener('change', () => {
      const file = input.files && input.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = ({ target }) => {
        preview.src = target.result;
        preview.classList.remove('d-none');
        if (fallback) fallback.classList.add('d-none');
      };
      reader.readAsDataURL(file);
    });
  }

  function bindCoverPreview() {
    const input = document.getElementById('id_cover');
    const preview = document.getElementById('coverPreview');
    if (!input || !preview) return;

    input.addEventListener('change', () => {
      const file = input.files && input.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = ({ target }) => {
        preview.style.backgroundImage = `url('${target.result}')`;
      };
      reader.readAsDataURL(file);
    });
  }

  document.querySelectorAll('.chips-box').forEach(mountChips);
  bindAvatarPreview();
  bindCoverPreview();
})();
