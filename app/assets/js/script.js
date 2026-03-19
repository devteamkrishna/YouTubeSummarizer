$('.rating-slider').owlCarousel({
        loop: true,
        margin: 0,
        nav: true,
        dots: false,
        items: 2,
        lazyLoad : true,
        autoplayTimeout: 6000,
        autoplay: false,
        navText: [
            "<i class=\"fa-solid fa-arrow-left\"></i>",
            "<i class=\"fa-solid fa-arrow-right\"></i>"],
       responsive: {
        992: {
            items: 2,
            nav: true,
        },
           768: {
               items: 1,
               nav: true,
           },
           0: {
            items: 1,
            nav: true,
        }
       },
    });
      
  document.getElementById('banner-search').addEventListener('click', function () {
    // Show the full-screen loader
    // document.getElementById('fullscreen-loader').style.display = 'flex';
// 
    // Simulate form processing (you can replace this with your actual logic)
    // setTimeout(() => {
    //   document.getElementById('fullscreen-loader').style.display = 'none';
    // }, 2000);
  });

  // Menu  
 $('#ToggleMenu').click(function() {
    $(this).toggleClass('active');
    $('body').toggleClass('overflow-hidden');
    $('#OverlayMenu').toggleClass('open');
   });
