document.addEventListener("DOMContentLoaded", function () {
    const toggle = document.querySelector("[data-nav-toggle]");
    const navigation = document.querySelector("[data-nav-content]");

    if (toggle && navigation) {
        toggle.addEventListener("click", function () {
            const isOpen = navigation.classList.toggle("is-open");
            toggle.setAttribute("aria-expanded", String(isOpen));
        });
    }

    document.querySelectorAll("[data-password-toggle]").forEach(function (button) {
        button.addEventListener("click", function () {
            const input = document.getElementById(button.dataset.passwordToggle);
            if (!input) {
                return;
            }

            const showPassword = input.type === "password";
            input.type = showPassword ? "text" : "password";
            button.textContent = showPassword ? "Hide" : "Show";
            button.setAttribute("aria-label", showPassword ? "Hide password" : "Show password");
        });
    });

    const search = document.querySelector("[data-destination-search]");
    const category = document.querySelector("[data-category-filter]");
    const cards = Array.from(document.querySelectorAll("[data-destination-card]"));
    const count = document.querySelector("[data-filter-count]");
    const empty = document.querySelector("[data-filter-empty]");

    function filterDestinations() {
        const query = search ? search.value.trim().toLocaleLowerCase() : "";
        const selectedCategory = category ? category.value : "all";
        let visibleCount = 0;

        cards.forEach(function (card) {
            const matchesText = card.dataset.name.indexOf(query) !== -1
                || card.dataset.location.toLocaleLowerCase().indexOf(query) !== -1;
            const matchesCategory = selectedCategory === "all"
                || card.dataset.category === selectedCategory;
            const visible = matchesText && matchesCategory;
            card.hidden = !visible;
            if (visible) {
                visibleCount += 1;
            }
        });

        if (count) {
            count.textContent = visibleCount + (visibleCount === 1 ? " destination" : " destinations");
        }
        if (empty) {
            empty.hidden = visibleCount !== 0 || cards.length === 0;
        }
    }

    if (search) {
        search.addEventListener("input", filterDestinations);
    }
    if (category) {
        category.addEventListener("change", filterDestinations);
    }

    const initialCategory = document.querySelector("[data-initial-category]");
    if (category && initialCategory && initialCategory.dataset.initialCategory) {
        const categoryValue = initialCategory.dataset.initialCategory;
        if (Array.from(category.options).some(function (option) {
            return option.value === categoryValue;
        })) {
            category.value = categoryValue;
        }
    }

    if (search || category) {
        filterDestinations();
    }
});
