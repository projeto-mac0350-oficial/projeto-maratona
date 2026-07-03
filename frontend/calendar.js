/*
 * Mini calendar of logged-in days for the homepage.
 *
 * Fills #mini-calendar (inside the logged-in panel) when the auth widget
 * reports a user: fetches GET /activity — which also records today — and
 * renders the current month with the visited days marked, today highlighted
 * and the streak of consecutive days below. Cleared on logout so no data
 * leaks across user switches. Pages without the container are unaffected.
 */
(function () {
    const mount = document.getElementById("mini-calendar");
    if (!mount) return;

    const WEEKDAYS = ["D", "S", "T", "Q", "Q", "S", "S"]; // week starts Sunday

    // "YYYY-MM-DD" -> local Date. new Date("YYYY-MM-DD") would parse as UTC
    // and shift to the previous day in Brazil (UTC-3), so build from parts.
    function parseISO(s) {
        const [y, m, d] = s.split("-").map(Number);
        return new Date(y, m - 1, d);
    }

    function isoOf(year, month, day) {
        const mm = String(month + 1).padStart(2, "0");
        const dd = String(day).padStart(2, "0");
        return `${year}-${mm}-${dd}`;
    }

    function el(tag, className, text) {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    }

    function clear() {
        mount.innerHTML = "";
    }

    // Renders from the server's `today`, not the client clock, so the grid
    // always matches the days the backend recorded.
    function render(data) {
        clear();
        const today = parseISO(data.today);
        const year = today.getFullYear();
        const month = today.getMonth();
        const logged = new Set(data.days);

        const title = today.toLocaleDateString("pt-BR", {
            month: "long",
            year: "numeric",
        });
        mount.appendChild(el("p", "cal-title", title));

        const grid = el("div", "cal-grid");
        WEEKDAYS.forEach((w) => grid.appendChild(el("span", "cal-weekday", w)));

        const firstWeekday = new Date(year, month, 1).getDay();
        for (let i = 0; i < firstWeekday; i++) {
            grid.appendChild(el("span", "cal-blank"));
        }

        const daysInMonth = new Date(year, month + 1, 0).getDate();
        for (let day = 1; day <= daysInMonth; day++) {
            const iso = isoOf(year, month, day);
            let cls = "cal-day";
            if (logged.has(iso)) cls += " logged";
            if (iso === data.today) cls += " today";
            grid.appendChild(el("span", cls, String(day)));
        }
        mount.appendChild(grid);

        const label = data.streak === 1 ? "dia seguido" : "dias seguidos";
        mount.appendChild(
            el("p", "cal-streak", `🔥 Sequência: ${data.streak} ${label}`)
        );
    }

    async function load() {
        try {
            const res = await fetch("/activity", { credentials: "same-origin" });
            if (!res.ok) return clear();
            render(await res.json());
        } catch (e) {
            clear(); /* offline: the panel simply shows no calendar */
        }
    }

    window.addEventListener("auth:change", (e) => {
        if (e.detail.user) {
            load();
        } else {
            clear();
        }
    });
})();
