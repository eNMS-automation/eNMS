const currentUrl = window.location.href.split('#')[0].split('?')[0],
    $BODY = $('body'),
    $MENU_TOGGLE = $('#menu_toggle'),
    $SIDEBAR_MENU = $('#sidebar-menu'),
    $SIDEBAR_FOOTER = $('.sidebar-footer'),
    $LEFT_COL = $('.left_col'),
    $RIGHT_COL = $('.right_col'),
    $NAV_MENU = $('.nav_menu'),
    $FOOTER = $('footer');

// Sidebar
function init_sidebar() {
  var setContentHeight = function () {
    // reset height
    $RIGHT_COL.css('min-height', $(window).height());
  
    var bodyHeight = $('body').outerHeight(),
      footerHeight = $('body').hasClass('footer_fixed') ? -10 : $FOOTER.height(),
      leftColHeight = $LEFT_COL.eq(1).height() + $SIDEBAR_FOOTER.height(),
      contentHeight = bodyHeight < leftColHeight ? leftColHeight : bodyHeight;
  
    // normalize content
    contentHeight -= $NAV_MENU.height() + footerHeight;
  
    $RIGHT_COL.css('min-height', contentHeight);
  };

  $SIDEBAR_MENU.find('a').on('click', function(ev) {
    console.log('clicked - sidebar_menu');
        var $li = $(this).parent();
        if ($li.is('.active')) {
          $li.removeClass('active active-sm');
          $('ul:first', $li).slideUp(function() {
            setContentHeight();
          });
        } else {
          // prevent closing menu if we are on child menu
          if (!$li.parent().is('.child_menu')) {
              $SIDEBAR_MENU.find('li').removeClass('active active-sm');
              $SIDEBAR_MENU.find('li ul').slideUp();
          } else {
            if ( $('body').is( ".nav-sm" ) ) {
              $SIDEBAR_MENU.find( "li" ).removeClass( "active active-sm" );
              $SIDEBAR_MENU.find( "li ul" ).slideUp();
            }
          }
          $li.addClass('active');
          $('ul:first', $li).slideDown(function() {
              setContentHeight();
          });
        }
    });

  // toggle small or large menu 
  $MENU_TOGGLE.on('click', function() {
    if ($('body').hasClass('nav-md')) {
      $SIDEBAR_MENU.find('li.active ul').hide();
      $SIDEBAR_MENU.find('li.active').addClass('active-sm').removeClass('active');
    } else {
      $SIDEBAR_MENU.find('li.active-sm ul').show();
      $SIDEBAR_MENU.find('li.active-sm').addClass('active').removeClass('active-sm');
    }
    $('body').toggleClass('nav-md nav-sm');
    setContentHeight();
    $('.dataTable').each ( function () { $(this).dataTable().fnDraw(); });
  });

  // check active menu
  $SIDEBAR_MENU.find('a[href="' + currentUrl + '"]').parent('li').addClass('current-page');
  $SIDEBAR_MENU.find('a').filter(function () {
    return this.href == currentUrl;
  }).parent('li').addClass('current-page').parents('ul').slideDown(function() {
    setContentHeight();
  }).parent().addClass('active');

  setContentHeight();
  // fixed sidebar
  if ($.fn.mCustomScrollbar) {
    $('.menu_fixed').mCustomScrollbar({
      autoHideScrollbar: true,
      theme: 'minimal',
      mouseWheel:{ preventDefault: true }
    });
  }
};

// NProgress
if (typeof NProgress != 'undefined') {
  $(document).ready(function () {
    NProgress.start();
  });
  $(window).load(function () {
    NProgress.done();
  });
}

$(document).ready(function() {
  init_sidebar();
});
