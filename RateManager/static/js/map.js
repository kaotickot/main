document.addEventListener('change', function (e) {
  if (!e.target.classList.contains('map-select')) return;
  const tr = e.target.closest('tr');
  const defInput = tr.querySelector('.def-input');
  if (e.target.value === '__DEFAULT__') {
    defInput.removeAttribute('disabled');
    defInput.focus();
  } else {
    defInput.setAttribute('disabled', 'disabled');
    defInput.value = '';
  }
});
