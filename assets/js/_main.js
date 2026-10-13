/* ==========================================================================
   jQuery plugin settings and other scripts
   ========================================================================== */

$(document).ready(function(){
  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var updateMotion = function() {
    $.fx.off = reducedMotion.matches;
    if (reducedMotion.matches) $(':animated').stop(true, true);
    $("a:not(.skip-link)").smoothScroll({offset: -80, speed: reducedMotion.matches ? 0 : 400});
  };
  updateMotion();
  if (reducedMotion.addEventListener) {
    reducedMotion.addEventListener('change', updateMotion);
  } else {
    reducedMotion.addListener(updateMotion);
  }

  // Sticky footer
  var bumpIt = function() {
      $("body").css("margin-bottom", $(".page__footer").outerHeight(true));
    },
    didResize = false;

  bumpIt();

  $(window).resize(function() {
    didResize = true;
  });
  setInterval(function() {
    if (didResize) {
      didResize = false;
      bumpIt();
    }
  }, 250);
  // FitVids init
  $("#main").fitVids();

  // init sticky sidebar
  $(".sticky").Stickyfill();

  var $authorWrapper = $(".author__urls-wrapper");
  var $followButton = $authorWrapper.find("button");
  var $authorLinks = $authorWrapper.find(".author__urls");
  var sidebarDesktop;

  $followButton.toggleClass('hidden', $authorLinks.children('li').not('.author__desktop').length === 0);

  var setAuthorExpanded = function(expanded, animate) {
    $followButton.attr('aria-expanded', String(expanded)).toggleClass('open', expanded);
    $authorLinks.stop(true, true);
    if (animate && !reducedMotion.matches) {
      $authorLinks[expanded ? 'fadeIn' : 'fadeOut']('fast');
    } else {
      $authorLinks.toggle(expanded);
    }
  };

  var stickySideBar = function(){
    if (!$authorLinks.length) return;
    // Follow the stylesheet's layout mode instead of duplicating its breakpoint.
    var desktop = $authorLinks.css('position') === 'relative';
    if (desktop === sidebarDesktop) return;
    sidebarDesktop = desktop;

    if (desktop) {
      Stickyfill.rebuild();
      Stickyfill.init();
    } else {
      Stickyfill.stop();
    }
    var focusInLinks = $.contains($authorLinks[0], document.activeElement);
    var focusOnButton = document.activeElement === $followButton[0];
    setAuthorExpanded(desktop, false);
    if (!desktop && focusInLinks) $followButton.trigger('focus');
    if (desktop && focusOnButton) $authorLinks.find('a').first().trigger('focus');
  };

  stickySideBar();

  $(window).resize(function(){
    stickySideBar();
  });

  // Follow menu drop down
  $followButton.on("click", function() {
    setAuthorExpanded($(this).attr('aria-expanded') !== 'true', true);
  });

  $authorWrapper.on('keydown', function(event) {
    if (event.key === 'Escape' && !sidebarDesktop && $followButton.attr('aria-expanded') === 'true') {
      setAuthorExpanded(false, false);
      $followButton.trigger('focus');
      event.preventDefault();
    }
  });

  $(document).on('click', function(event) {
    if (!sidebarDesktop && !$authorWrapper.is(event.target) && !$authorWrapper.has(event.target).length) {
      setAuthorExpanded(false, false);
    }
  });

  $('.skip-link').on('click', function() {
    $('#main').trigger('focus');
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
