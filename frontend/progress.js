/*
 * Persistent study progress for the static content pages.
 *
 * Any element with `data-key` is a toggle. On load we fetch the logged-in
 * user's saved progress and reflect it; on click we flip the state and persist
 * it. When logged out (or offline) the toggle still works visually but isn't
 * saved — content pages stay usable for guests.
 *
 * Each toggle declares:
 *   data-key    stable id, e.g. "busca_binaria:prob:roadworks"
 *   data-kind   "ref" (reference, read) or "problem" (solved)
 *   data-label  human label shown on the /painel dashboard
 */
(function () {
    // Maps a kind to its on/off CSS classes and button text, so this file stays
    // generic and the pages only need the three data-* attributes above.
    const STYLES = {
        ref: { on: "done", off: "pending", onText: "Lido", offText: "Pendente" },
        problem: { on: "ac", off: "na", onText: "AC", offText: "NA" },
    };

    const buttons = Array.from(document.querySelectorAll("[data-key]"));
    if (!buttons.length) return;

    function render(btn, done) {
        const s = STYLES[btn.dataset.kind];
        if (!s) return;
        btn.classList.toggle(s.on, done);
        btn.classList.toggle(s.off, !done);
        btn.textContent = done ? s.onText : s.offText;
        btn.setAttribute("aria-pressed", done ? "true" : "false");
    }

    function isDone(btn) {
        const s = STYLES[btn.dataset.kind];
        return s ? btn.classList.contains(s.on) : false;
    }

    async function save(btn, done) {
        try {
            await fetch("/progress", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "same-origin",
                body: JSON.stringify({
                    item_key: btn.dataset.key,
                    kind: btn.dataset.kind,
                    label: btn.dataset.label || "",
                    done: done,
                }),
            });
        } catch (e) {
            /* offline / logged out: keep the visual state only */
        }
    }

    buttons.forEach((btn) => {
        btn.addEventListener("click", () => {
            const done = !isDone(btn);
            render(btn, done);
            save(btn, done);
        });
    });

    // Reflect saved state on load (defaults to "not done" for guests).
    (async () => {
        let saved = {};
        try {
            const res = await fetch("/progress", { credentials: "same-origin" });
            if (res.ok) saved = await res.json();
        } catch (e) {
            /* guest / offline: leave defaults */
        }
        buttons.forEach((btn) => {
            const entry = saved[btn.dataset.key];
            render(btn, !!(entry && entry.done));
        });
    })();
})();
