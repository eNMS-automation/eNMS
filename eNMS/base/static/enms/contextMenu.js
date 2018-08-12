(function($, window) {
  $.fn.contextMenu = function(settings) {
    return this.each(function() {
      // Open context menu
      $(this).on('contextmenu', function(e) {
        // return native menu if pressing control
        if (e.ctrlKey) {
          return;
        }
        const $menu = $(settings.menuSelector)
          .data('invokedOn', $(e.target))
          .show()
          .css({
            position: 'absolute',
            left: getMenuPosition(e.clientX, 'width', 'scrollLeft'),
            top: getMenuPosition(e.clientY, 'height', 'scrollTop'),
          })
          .off('click')
          .on('click', 'a', function(e) {
            $menu.hide();
            const $invokedOn = $menu.data('invokedOn');
            const $selectedMenu = $(e.target);
            settings.menuSelected.call(this, $invokedOn, $selectedMenu);
          });
        return false;
      });
      // make sure menu closes on any click
      $('body').click(function() {
        $(settings.menuSelector).hide();
      });
    });

    /**
    * Get menu position.
    * @param {mouse} mouse
    * @param {direction} direction
    * @param {scrollDir} scrollDir
    * @return {position}
    */
    function getMenuPosition(mouse, direction, scrollDir) {
      const win = $(window)[direction]();
      const scroll = $(window)[scrollDir]();
      const menu = $(settings.menuSelector)[direction]();
      let position = mouse + scroll;
      // opening menu would pass the side of the page
      if (mouse + menu > win && menu < mouse) {
        position -= menu;
      }
      return position;
    }
  };
})(jQuery, window);
