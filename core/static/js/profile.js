(function () {
  function mountChips(box) {
    const targetId = box.dataset.target;
    const hidden = document.getElementById(targetId);
    if (!hidden) return;

    hidden.classList.add('d-none');
    const input = box.querySelector('input');
    const chips = new Set((hidden.value || '').split(',').map(v => v.trim()).filter(Boolean));

    function render() {
      box.querySelectorAll('.chip').forEach(c => c.remove());
      chips.forEach(tag => {
        const chip = document.createElement('span');
        chip.className = 'chip me-1 mb-1';
        chip.textContent = tag;
        const close = document.createElement('button');
        close.type = 'button';
        close.className = 'chip-remove';
        close.textContent = '×';
        close.addEventListener('click', () => {
          chips.delete(tag);
          render();
        });
        chip.appendChild(close);
        box.insertBefore(chip, input);
      });
      hidden.value = Array.from(chips).join(', ');
    }

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        const value = input.value.trim();
        if (!value) return;
        chips.add(value);
        input.value = '';
        render();
      }
    });

    render();
  }

  function bindPreview(inputId, imgId) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(imgId);
    if (!input || !preview) return;
    input.addEventListener('change', () => {
      const [file] = input.files;
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (e) => {
        preview.src = e.target.result;
      };
      reader.readAsDataURL(file);
    });
  }

  document.querySelectorAll('.chips-box').forEach(mountChips);
  bindPreview('id_avatar', 'avatarPreview');
  bindPreview('id_cover', 'coverPreview');
})();
