'use strict';

/**
 * Browsertime preScript: removes full-screen overlays (age gates, cookie
 * banners, GDPR modals, etc.) so that they don't interfere with measurements.
 *
 * Used as --preScript /scripts/dismiss-age-gate.js
 */
module.exports = async function (context, commands) {
  // Wait for any overlay to fully render
  await commands.wait.byTime(3000);

  // Remove overlays from the DOM
  await commands.js.run(`
    (function() {
      var vw = window.innerWidth, vh = window.innerHeight, removed = 0;

      // Remove fixed/absolute elements with high z-index covering >80% of viewport
      var allEls = document.querySelectorAll(
        'div, section, dialog, aside, [role="dialog"], [role="alertdialog"]'
      );
      for (var i = 0; i < allEls.length; i++) {
        var el = allEls[i], style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden') continue;
        if (style.position !== 'fixed' && style.position !== 'absolute') continue;
        var z = parseInt(style.zIndex) || 0;
        if (z < 10) continue;
        var rect = el.getBoundingClientRect();
        if (rect.width >= vw * 0.8 && rect.height >= vh * 0.8) {
          el.remove();
          removed++;
        }
      }

      // Remove backdrop / overlay elements
      var backdrops = document.querySelectorAll(
        '.modal-backdrop, .overlay-backdrop, .popup-overlay, .popup-voile, ' +
        '[class*="backdrop"], [class*="overlay"]:not(nav):not(header)'
      );
      for (var b = 0; b < backdrops.length; b++) {
        var bs = window.getComputedStyle(backdrops[b]);
        if (
          (bs.position === 'fixed' || bs.position === 'absolute') &&
          (parseInt(bs.zIndex) || 0) >= 10
        ) {
          backdrops[b].remove();
          removed++;
        }
      }

      // Restore scrolling
      document.documentElement.style.overflow = '';
      document.body.style.overflow = '';
      document.documentElement.style.position = '';
      document.body.style.position = '';
      document.body.classList.remove(
        'modal-open', 'no-scroll', 'noscroll', 'overflow-hidden', 'popup-open'
      );

      return removed;
    })();
  `);

  // Brief wait for DOM to settle after removal
  await commands.wait.byTime(1000);
};
