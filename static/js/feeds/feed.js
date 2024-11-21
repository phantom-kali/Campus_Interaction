document.addEventListener('DOMContentLoaded', function() {
    const createBtn = document.querySelector('.floating-create-btn');
    let lastScrollTop = 0;
    let scrollTimeout;

    function handleScroll() {
        clearTimeout(scrollTimeout);

        scrollTimeout = setTimeout(() => {
            const st = window.pageYOffset || document.documentElement.scrollTop;
            
            // Show button when scrolling up or near top
            if (st < lastScrollTop || st < 100) {
                createBtn.classList.remove('hidden');
            } 
            // Hide button when scrolling down
            else if (st > lastScrollTop) {
                createBtn.classList.add('hidden');
            }
            
            lastScrollTop = st <= 0 ? 0 : st;
        }, 10);
    }

    // Throttled scroll event listener
    let ticking = false;
    window.addEventListener('scroll', () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                handleScroll();
                ticking = false;
            });
            ticking = true;
        }
    });

    // Show button initially
    createBtn.classList.remove('hidden');
}); 