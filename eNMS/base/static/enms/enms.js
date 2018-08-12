/*
global
NProgress: false
*/

const currentUrl = window.location.href.split('#')[0].split('?')[0];

/**
 * Sidebar initialization.
 */
function initSidebar() {
  let setContentHeight = function() {
    $('.right_col').css('min-height', $(window).height());
    let bodyHeight = $('body').outerHeight();
    let footerHeight = $('body').hasClass('footer_fixed')
      ? -10
      : $('footer').height();
    let leftColHeight = $('.left_col').eq(1).height()
      + $('.sidebar-footer').height();
    let contentHeight = bodyHeight < leftColHeight ? leftColHeight : bodyHeight;
    contentHeight -= $('.nav_menu').height() + footerHeight;
    $('.right_col').css('min-height', contentHeight);
  };

  $('#sidebar-menu').find('a').on('click', function(ev) {
    let $li = $(this).parent();
    if ($li.is('.active')) {
      $li.removeClass('active active-sm');
      $('ul:first', $li).slideUp(function() {
        setContentHeight();
      });
    } else {
      // prevent closing menu if we are on child menu
      if (!$li.parent().is('.child_menu')) {
          $('#sidebar-menu').find('li').removeClass('active active-sm');
          $('#sidebar-menu').find('li ul').slideUp();
      } else {
        if ($('body').is('.nav-sm')) {
          $('#sidebar-menu').find('li').removeClass('active active-sm');
          $('#sidebar-menu').find('li ul').slideUp();
        }
      }
      $li.addClass('active');
      $('ul:first', $li).slideDown(function() {
          setContentHeight();
      });
    }
  });

  $('#menu_toggle').on('click', function() {
    if ($('body').hasClass('nav-md')) {
      $('#sidebar-menu').find('li.active ul').hide();
      $('#sidebar-menu').find('li.active').addClass('active-sm');
      $('#sidebar-menu').find('li.active').removeClass('active');
    } else {
      $('#sidebar-menu').find('li.active-sm ul').show();
      $('#sidebar-menu').find('li.active-sm').addClass('active');
      $('#sidebar-menu').find('li.active-sm').removeClass('active-sm');
    }
    $('body').toggleClass('nav-md nav-sm');
    setContentHeight();
    $('.dataTable').each(function() {
      $(this).dataTable().fnDraw();
    });
  });

  // check active menu
  const url = 'a[href="' + currentUrl + '"]';
  $('#sidebar-menu').find(url).parent('li').addClass('current-page');
  $('#sidebar-menu').find('a').filter(function() {
    return this.href == currentUrl;
  }).parent('li').addClass('current-page').parents('ul').slideDown(function() {
    setContentHeight();
  }).parent().addClass('active');

  setContentHeight();
  if ($.fn.mCustomScrollbar) {
    $('.menu_fixed').mCustomScrollbar({
      autoHideScrollbar: true,
      theme: 'minimal',
      mouseWheel: {preventDefault: true},
    });
  }
}

if (typeof NProgress != 'undefined') {
  $(document).ready(function() {
    NProgress.start();
  });
  $(window).load(function() {
    NProgress.done();
  });
}

$(document).ready(function() {
  initSidebar();
});
