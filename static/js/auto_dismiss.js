setTimeout(function () {
    let alerts = document.querySelectorAll('.auto-dismiss');
    alerts.forEach(function (alert) {
      alert.classList.remove('show'); // Activa el fade
    });
  }, 4000);
  