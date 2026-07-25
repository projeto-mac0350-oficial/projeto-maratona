/*
 * Activity heatmap for the profile page ("Sua atividade").
 *
 * Classic GitHub-style grid: 7 rows (one per weekday), columns are
 * consecutive weeks, today is always the last cell of the last column.
 * Fills #heatmap when the auth widget reports a user: fetches GET /heatmap
 * (a { today, counts: { "YYYY-MM-DD": N, ... } } map of problems/references
 * marked done per day) and colors each day gray (no activity) or one of
 * three green shades based on how much was done that day. Cleared on logout
 * so no data leaks across user switches. Pages without the container are
 * unaffected.
 */
(function () {
    const mount = document.getElementById("heatmap");
    if (!mount) return;

    const WEEKS = 20; // columns shown; tweak to taste
    const WEEKDAY_LABELS = ["D", "S", "T", "Q", "Q", "S", "S"]; // week starts Sunday

    // Thresholds for the 3 green tiers, by count of items done that day.
    // Tune here if the data volume changes.
    const TIERS = [2, 4]; // <=2 -> tier 1, <=4 -> tier 2, above -> tier 3

    // "YYYY-MM-DD" -> local Date. new Date("YYYY-MM-DD") parses as UTC and
    // shifts to the previous day in Brazil (UTC-3), so build from parts.
    function parseISO(s) {
        const [y, m, d] = s.split("-").map(Number);
        return new Date(y, m - 1, d);
    }

    function isoOf(dateObj) {
        const y = dateObj.getFullYear();
        const m = String(dateObj.getMonth() + 1).padStart(2, "0");
        const d = String(dateObj.getDate()).padStart(2, "0");
        return `${y}-${m}-${d}`;
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

    function tierFor(count) {
        if (!count) return 0;
        if (count <= TIERS[0]) return 1;
        if (count <= TIERS[1]) return 2;
        return 3;
    }

    // Renders from the server's `today`, not the client clock, so the grid
    // always matches the days the backend has counts for.
    function render(data) {
        clear();

        const today = parseISO(data.today);
        const counts = data.counts || {};
        const totalDays = WEEKS * 7;

        // Contiguous run of `totalDays` days ending today, chunked into
        // 7-day columns — today always lands in the last column.
        const start = new Date(today);
        start.setDate(start.getDate() - (totalDays - 1));

        mount.appendChild(
            el("p", "heat-title", `Atividade — últimas ${WEEKS} semanas`)
        );

        const body = el("div", "heat-body");

        const labels = el("div", "heat-weekday-labels");
        WEEKDAY_LABELS.forEach((w) => labels.appendChild(el("span", "heat-weekday", w)));
        body.appendChild(labels);

        const grid = el("div", "heat-grid");
        grid.style.gridTemplateColumns = `repeat(${WEEKS}, 1fr)`;
        grid.style.gridTemplateRows = "repeat(7, 1fr)";

        // Fill column-major so weekday rows line up correctly with CSS grid
        // (grid-auto-flow: column further down handles the placement).
        for (let offset = 0; offset < totalDays; offset++) {
            const day = new Date(start);
            day.setDate(day.getDate() + offset);
            const iso = isoOf(day);
            const count = counts[iso] || 0;

            const cell = el("span", `heat-day heat-tier-${tierFor(count)}`);
            cell.title = `${iso}: ${count} item(ns) concluído(s)`;
            if (iso === data.today) cell.classList.add("today");
            grid.appendChild(cell);
        }
        body.appendChild(grid);

        mount.appendChild(body);
    }

    async function load() {
        try {
            const res = await fetch("/heatmap", { credentials: "same-origin" });
            if (!res.ok) return clear();
            render(await res.json());
        } catch (e) {
            clear(); /* offline: the panel simply shows no heatmap */
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