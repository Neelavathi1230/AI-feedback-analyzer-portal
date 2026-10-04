// Small helper script used on every page.

document.addEventListener('DOMContentLoaded', function () {
  // 1. Bootstrap client-side validation for every form with class "needs-validation"
  document.querySelectorAll('form.needs-validation').forEach(function (form) {
    form.addEventListener('submit', function (event) {
      // "confirm password" fields: must equal the field named in data-match
      form.querySelectorAll('[data-match]').forEach(function (field) {
        var other = form.querySelector('#' + field.dataset.match);
        field.setCustomValidity(other && field.value !== other.value ? 'Passwords do not match' : '');
      });
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add('was-validated');
    });
  });

  // 2. Live character counter for textareas that have data-counter="<span id>"
  document.querySelectorAll('textarea[data-counter]').forEach(function (area) {
    var counter = document.getElementById(area.dataset.counter);
    var update = function () { counter.textContent = area.value.length; };
    area.addEventListener('input', update);
    update();
  });

  // 3. Ask before dangerous actions: <form data-confirm="Are you sure?">
  document.querySelectorAll('form[data-confirm]').forEach(function (form) {
    form.addEventListener('submit', function (event) {
      if (!window.confirm(form.dataset.confirm)) {
        event.preventDefault();
      }
    });
  });
});
