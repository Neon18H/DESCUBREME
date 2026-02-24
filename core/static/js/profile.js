(function () {
  const MAX_TAGS = 20;
  const MAX_TAG_LENGTH = 24;

  function parseInitial(raw) {
    if (!raw) return [];
    try {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) return parsed;
    } catch (_error) {
      return raw.split(',');
    }
    return [];
  }

  function sanitizeTag(value) {
    return (value || '').trim().slice(0, MAX_TAG_LENGTH);
  }

  function mountChips(box) {
    const targetId = box.dataset.target;
    const hidden = document.getElementById(targetId);
    const input = box.querySelector('input');
    if (!hidden || !input) return;

    hidden.classList.add('d-none');
    const chips = [];
    const seedValues = parseInitial(box.dataset.initial || hidden.value);

    function syncHidden() {
      hidden.value = JSON.stringify(chips);
    }

    function addChip(rawValue) {
      const tag = sanitizeTag(rawValue);
      if (!tag || chips.length >= MAX_TAGS) return;
      const exists = chips.some((item) => item.toLowerCase() === tag.toLowerCase());
      if (exists) return;
      chips.push(tag);
    }

    function render() {
      box.querySelectorAll('.chip').forEach((chip) => chip.remove());
      chips.forEach((tag, index) => {
        const chip = document.createElement('span');
        chip.className = 'chip';
        chip.textContent = tag;

        const close = document.createElement('button');
        close.type = 'button';
        close.className = 'chip-remove';
        close.textContent = '×';
        close.setAttribute('aria-label', `Quitar ${tag}`);
        close.addEventListener('click', () => {
          chips.splice(index, 1);
          render();
        });

        chip.appendChild(close);
        box.insertBefore(chip, input);
      });
      syncHidden();
    }

    seedValues.forEach(addChip);
    render();

    input.addEventListener('keydown', (event) => {
      if (event.key !== 'Enter') return;
      event.preventDefault();
      addChip(input.value);
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
      const [file] = input.files;
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
      const [file] = input.files;
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
