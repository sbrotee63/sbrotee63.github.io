/* ==========================================================================
   jQuery plugin settings and other scripts
   ========================================================================== */

$(document).ready(function(){
  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var updateMotion = function() {
    $.fx.off = reducedMotion.matches;
    if (reducedMotion.matches) $(':animated').stop(true, true);
  };
  updateMotion();
  if (reducedMotion.addEventListener) {
    reducedMotion.addEventListener('change', updateMotion);
  } else {
    reducedMotion.addListener(updateMotion);
  }

  $("#main").fitVids();

  $('.skip-link').on('click', function() {
    $('#main').trigger('focus');
  });

  var $themeButton = $('.theme-toggle');
  var updateThemeButton = function() {
    var light = document.documentElement.dataset.theme === 'light';
    $themeButton.attr('aria-label', light ? 'Switch to dark theme' : 'Switch to light theme')
      .attr('aria-pressed', String(light));
    $('meta[name="theme-color"]').attr('content', light ? '#f5f4fa' : '#0d1320');
  };
  updateThemeButton();
  $themeButton.prop('hidden', false).on('click', function() {
    var next = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem('brotee-theme', next); } catch (error) { /* Optional preference. */ }
    updateThemeButton();
  });

  // add lightbox class to all image links
  $("a[href$='.jpg'],a[href$='.jpeg'],a[href$='.JPG'],a[href$='.png'],a[href$='.gif']").addClass("image-popup");

  // Magnific-Popup options
  $(".image-popup").magnificPopup({
    type: 'image',
    tLoading: 'Loading image #%curr%...',
    gallery: {
      enabled: true,
      navigateByImgClick: true,
      preload: [0,1] // Will preload 0 - before current, and 1 after the current image
    },
    image: {
      tError: '<a href="%url%">Image #%curr%</a> could not be loaded.',
    },
    removalDelay: 500, // Delay in milliseconds before popup is removed
    // Class that is added to body when popup is open.
    // make it unique to apply your CSS animations just to this exact popup
    mainClass: 'mfp-zoom-in',
    callbacks: {
      beforeOpen: function() {
        this.st.removalDelay = reducedMotion.matches ? 0 : 500;
        // just a hack that adds mfp-anim class to markup
        this.st.image.markup = this.st.image.markup.replace('mfp-figure', 'mfp-figure mfp-with-anim');
      }
    },
    closeOnContentClick: true,
    midClick: true // allow opening popup on middle mouse click. Always set it to true if you don't provide alternative source.
  });

});
