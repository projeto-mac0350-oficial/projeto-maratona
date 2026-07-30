/*
 * Activity heatmap for the profile page ("Sua atividade").
 *
 * Classic GitHub-style grid: 7 rows (one per weekday, Sunday first), columns
 * are real calendar weeks (Sunday–Saturday) — not just contiguous 7-day
 * chunks — so each row always lines up with its actual weekday and the
 * current (partial) week only shows the cells that already happened. E.g.
 * if today is a Sunday, the last column has a single cell in the Sunday row.
 *
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

    const WEEKS = 25; // columns shown; tweak to taste
    const CELL_SIZE = 20; // px — must match .heat-day / .heat-weekday in heatmap.css
    const GRID_GAP = 3; // px — must match the gap used in heatmap.css
    const WEEKDAY_LABELS = [" ","D", "S", "T", "Q", "Q", "S", "S"]; // week starts Sunday
    const MONTH_LABELS = [
        "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
        "Jul", "Ago", "Set", "Out", "Nov", "Dez",
    ];

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

    // Sunday of the calendar week containing d (local midnight).
    function startOfWeek(d) {
        const copy = new Date(d.getFullYear(), d.getMonth(), d.getDate());
        copy.setDate(copy.getDate() - copy.getDay());
        return copy;
    }

    function addDays(d, n) {
        const copy = new Date(d);
        copy.setDate(copy.getDate() + n);
        return copy;
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

        // Columns are real Sunday–Saturday weeks: the last column is the
        // week containing today (possibly partial), the first is WEEKS-1
        // weeks before it.
        const lastColumnStart = startOfWeek(today);
        const firstColumnStart = addDays(lastColumnStart, -(WEEKS - 1) * 7);
        const colTemplate = `repeat(${WEEKS}, ${CELL_SIZE}px)`;

        const body = el("div", "heat-body");

        const weekdayLabels = el("div", "heat-weekday-labels");
        weekdayLabels.style.gridTemplateRows = `repeat(7, ${CELL_SIZE}px)`;
        weekdayLabels.style.gap = `${GRID_GAP}px`;
        WEEKDAY_LABELS.forEach((w) => weekdayLabels.appendChild(el("span", "heat-weekday", w)));
        body.appendChild(weekdayLabels);

        const gridWrap = el("div", "heat-grid-wrap");

        // One label per column, shown only where a new month starts (or in
        // the very first column) so it doesn't repeat every week.
        const monthLabels = el("div", "heat-month-labels");
        monthLabels.style.gridTemplateColumns = colTemplate;
        monthLabels.style.gap = `${GRID_GAP}px`;
        let lastMonthShown = null;
        for (let week = 0; week < WEEKS; week++) {
            const weekStart = addDays(firstColumnStart, week * 7);
            const month = weekStart.getMonth();
            const label = el("span", "heat-month-label");
            if (month !== lastMonthShown) {
                label.textContent = MONTH_LABELS[month];
                lastMonthShown = month;
            }
            label.style.gridColumn = String(week + 1);
            monthLabels.appendChild(label);
        }
        gridWrap.appendChild(monthLabels);

        const grid = el("div", "heat-grid");
        grid.style.gridTemplateColumns = colTemplate;
        grid.style.gridTemplateRows = `repeat(7, ${CELL_SIZE}px)`;
        grid.style.gap = `${GRID_GAP}px`;

        // Walk day by day from the first column's Sunday up to today only —
        // future days within today's partial week are simply never created,
        // which is what makes the last column stop exactly at today.
        let cursor = firstColumnStart;
        while (cursor <= today) {
            const iso = isoOf(cursor);
            const count = counts[iso] || 0;
            const weekIndex = Math.floor((cursor - firstColumnStart) / (7 * 86400000));

            const cell = el("span", `heat-day heat-tier-${tierFor(count)}`);
            cell.style.gridColumn = String(weekIndex + 1);
            cell.style.gridRow = String(cursor.getDay() + 1);
            cell.title = `${iso}: ${count} item(ns) concluído(s)`;
            if (iso === data.today) cell.classList.add("today");
            grid.appendChild(cell);

            cursor = addDays(cursor, 1);
        }
        gridWrap.appendChild(grid);

        body.appendChild(gridWrap);
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