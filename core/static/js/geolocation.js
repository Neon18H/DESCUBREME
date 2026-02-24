(function () {
  const latInput = document.getElementById('lat');
  if (!latInput) return;

  const lngInput = document.getElementById('lng');
  const cityInput = document.getElementById('cityName');
  const status = document.getElementById('locationStatus');
  const modalNode = document.getElementById('manualCityModal');
  const saveManualBtn = document.getElementById('saveManualCity');
  const manualCity = document.getElementById('manualCity');
  const manualModal = modalNode ? new bootstrap.Modal(modalNode) : null;

  const setStatus = (text) => {
    status.textContent = text;
  };

  if (saveManualBtn) {
    saveManualBtn.addEventListener('click', () => {
      const label = manualCity.options[manualCity.selectedIndex].text;
      cityInput.value = label;
      setStatus(`Ubicación manual: ${label}`);
      manualModal.hide();
    });
  }

  if (!navigator.geolocation) {
    setStatus('Este dispositivo no soporta GPS.');
    manualModal?.show();
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (position) => {
      latInput.value = position.coords.latitude;
      lngInput.value = position.coords.longitude;
      setStatus('Ubicación detectada (aprox).');
    },
    () => {
      setStatus('Sin permisos GPS. Elige tu ciudad manualmente.');
      manualModal?.show();
    },
    { enableHighAccuracy: true, timeout: 10000 }
  );
})();
