document.getElementById('toggle-theme').addEventListener('click',()=>{
  if (document.documentElement.getAttribute('data-bs-theme') == 'dark') {
    document.documentElement.setAttribute('data-bs-theme','light')
  }
  else {
    document.documentElement.setAttribute('data-bs-theme','dark')
  }
})

/*function hexToRgba(hex, alpha) {
    const h = hex.replace('#', '');
    const bigint = parseInt(h, 16);
    const r = (bigint >> 16) & 255;
    const g = (bigint >> 8) & 255;
    const b = bigint & 255;
    return 'rgba(' + r + ',' + g + ',' + b + ',' + alpha + ')';
  }
*/
/*
  function colorize(opaque, hover, pieChart) {
    const v = pieChart.parsed;
    const c = v < -50 ? '#D60000'
      : v < 0 ? '#F46300'
      : v < 50 ? '#0358B6'
      : '#44DE28';

    const opacity = hover ? 1 - Math.abs(v / 150) - 0.2 : 1 - Math.abs(v / 150);

    return opaque ? c : hexToRgba(c, opacity);
  }

  function hoverColorize(pieChart) {
    return colorize(false, true, pieChart);
  }
*/