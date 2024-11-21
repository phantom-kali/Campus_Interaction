// CSRF Token Setup
$(document).ready(function () {
    // Function to get cookie by name
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === name + "=") {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Set up CSRF token for all AJAX requests
    const csrftoken = getCookie("csrftoken");
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        },
    });
});

// Dropdown Toggle
document.addEventListener('DOMContentLoaded', function() {
    // Handle dropdown toggles for both desktop and mobile
    document.querySelectorAll(".dropdown-toggle").forEach((toggle) => {
        toggle.addEventListener("click", function(e) {
            e.preventDefault(); // Prevent default link behavior
            e.stopPropagation(); // Prevent event bubbling
            
            // Toggle active class on the clicked element
            this.classList.toggle("active");
            
            // Find the next sibling dropdown/dropdown-menu-list
            const dropdownMenu = this.nextElementSibling;
            if (dropdownMenu) {
                dropdownMenu.classList.toggle("show");
            }
        });
    });

    // Close dropdowns when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.dropdown-toggle')) {
            document.querySelectorAll('.dropdown, .dropdown-menu-list').forEach(dropdown => {
                dropdown.classList.remove('show');
            });
            document.querySelectorAll('.dropdown-toggle').forEach(toggle => {
                toggle.classList.remove('active');
            });
        }
    });
});

// Search Functionality
$(".search-switch").on("click", function () {
    $(".search-model").fadeIn(400, function () {
        $("#search-input").focus();
    });
});

$(".search-close-switch").on("click", function () {
    $(".search-model").fadeOut(400, function () {
        $("#search-input").val("");
    });
});

$(document).on("keydown", function (e) {
    if (e.key === "Escape") {
        $(".search-model").fadeOut(400, function () {
            $("#search-input").val("");
        });
    }
});

// Search Input Handler
document.getElementById("search-input").addEventListener("keyup", function () {
    const query = this.value.trim();
    const suggestionsContainer = document.getElementById("suggestions");

    if (query.length > 2) {
        fetchSuggestions(query, suggestionsContainer);
    } else {
        suggestionsContainer.classList.remove("show");
        suggestionsContainer.innerHTML = "";
    }
});

// Fetch Search Suggestions
function fetchSuggestions(query, container) {
    fetch(`/search/?q=${query}`, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
    })
        .then((response) => response.json())
        .then((data) => {
            let suggestionsHTML = "";

            if (data.no_results) {
                suggestionsHTML = `<div class="no-results">${data.no_results}</div>`;
            } else {
                for (const [category, items] of Object.entries(data)) {
                    suggestionsHTML += `<div class="suggestion-category"><strong>Section: ${category}</strong><ul>`;
                    items.forEach((item) => {
                        const name = highlightQuery(item.title || item.name, query);
                        const description = highlightQuery(item.description || "", query);
                        let url = "";

                        if (category === "polls") {
                            url = `/polls/polls/${item.id}/vote/`;
                        } else if (category === "posts") {
                            url = `/feeds/post/${item.id}/`;
                        } else if (category === "items") {
                            url = `/marketplace/item/${item.id}/`;
                        } else {
                            url = `/${category}/${item.id}/`;
                        }

                        suggestionsHTML += `
                        <li>
                            <a href="${url}" class="suggestion-links">
                                <strong>${name}</strong>
                                <p class="suggestion-description">${description}</p>
                            </a>
                        </li>`;
                    });
                    suggestionsHTML += "</ul></div>";
                }
            }

            container.innerHTML = suggestionsHTML;
            container.classList.add("show");
        })
        .catch((error) => console.error("Error fetching search suggestions:", error));
}

function highlightQuery(text, query) {
    if (!query) return text;
    const regex = new RegExp(`(${query})`, "gi");
    return text.replace(regex, `<mark>$1</mark>`);
}

// Click Outside Search Handler
document.addEventListener("click", function (e) {
    const searchInput = document.getElementById("search-input");
    const suggestionsContainer = document.getElementById("suggestions");

    if (!e.target.closest("#search-input")) {
        suggestionsContainer.classList.remove("show");
    } else {
        const query = searchInput.value.trim();
        if (query.length > 2 && suggestionsContainer.innerHTML) {
            suggestionsContainer.classList.add("show");
        }
    }
});

// Canvas Menu
$(".canvas__open").on("click", function () {
    $(".offcanvas-menu-wrapper").addClass("active");
    $(".offcanvas-menu-overlay").addClass("active");
});

$(".offcanvas-menu-overlay, .offcanvas__close").on("click", function (e) {
    e.stopPropagation();
    $(".offcanvas-menu-wrapper").removeClass("active");
    $(".offcanvas-menu-overlay").removeClass("active");
});

$(".offcanvas-menu-wrapper").on("click", function (e) {
    e.stopPropagation();
});

// Preloader
$(window).on("load", function () {
    $(".loader").fadeOut();
    $("#preloder").delay(200).fadeOut("slow");
});

// Background Set
$(".set-bg").each(function () {
    var bg = $(this).data("setbg");
    $(this).css("background-image", "url(" + bg + ")");
});


// Nice Scroll
$(".nice-scroll").niceScroll({
    cursorborder: "",
    cursorcolor: "#dddddd",
    boxzoom: false,
    cursorwidth: 5,
    background: "rgba(0, 0, 0, 0.2)",
    cursorborderradius: 50,
    horizrailenabled: false,
});
