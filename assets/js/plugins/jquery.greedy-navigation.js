/* Priority navigation: move links into a disclosure when they no longer fit. */
(function($) {
  var $nav = $('#site-nav');
  var $btn = $nav.find('button');
  var $vlinks = $nav.find('.visible-links');
  var $hlinks = $nav.find('.hidden-links');
  var previousWidth;

  function setExpanded(expanded) {
    $btn.attr('aria-expanded', String(expanded)).toggleClass('close', expanded);
    $hlinks.toggleClass('hidden', !expanded);
  }

  function updateNav() {
    var navWidth = $nav.width();
    if (navWidth === previousWidth) return;
    previousWidth = navWidth;

    var expanded = $btn.attr('aria-expanded') === 'true';
    var focused = document.activeElement;

    // Restore the original order before measuring at the new width.
    $hlinks.children().appendTo($vlinks);
    $btn.addClass('hidden');

    if ($vlinks.outerWidth() > navWidth) {
      $btn.removeClass('hidden');
      var availableSpace = Math.max(0, navWidth - $btn.outerWidth() - 16);
      var $movable = $vlinks.children(':not(.masthead__menu-item--lg)');

      // The title cannot move. Stop when no removable links remain, even if a
      // long title still exceeds the available space at a narrow viewport.
      while ($vlinks.outerWidth() > availableSpace && $movable.length) {
        $movable.last().prependTo($hlinks);
        $movable = $vlinks.children(':not(.masthead__menu-item--lg)');
      }
    }

    var hasHiddenLinks = $hlinks.children().length > 0;
    $btn.toggleClass('hidden', !hasHiddenLinks);
    setExpanded(hasHiddenLinks && expanded);

    // Moving a focused link must not strand focus inside a closed disclosure.
    if ($.contains($hlinks[0], focused) && !expanded) {
      $btn.trigger('focus');
    } else if (focused === $btn[0] && !hasHiddenLinks) {
      $vlinks.find('a').first().trigger('focus');
    } else if ($.contains($nav[0], focused) && focused !== document.activeElement) {
      $(focused).trigger('focus');
    }
  }

  $btn.on('click', function() {
    setExpanded($(this).attr('aria-expanded') !== 'true');
  });

  $nav.on('keydown', function(event) {
    if (event.key === 'Escape' && $btn.attr('aria-expanded') === 'true') {
      setExpanded(false);
      $btn.trigger('focus');
      event.preventDefault();
    }
  });

  $(document).on('click', function(event) {
    if (!$nav.is(event.target) && !$nav.has(event.target).length) setExpanded(false);
  });

  $(window).on('resize', updateNav);
  updateNav();
})(jQuery);
