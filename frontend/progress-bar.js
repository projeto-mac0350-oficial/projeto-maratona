/*
 * Shared "problems done / total" progress bar — used by both the profile
 * page (profile.html, grouped by level) and the topics listing
 * (topics-list.html, one bar per topic card). Exposes window.ProgressBar so
 * any page can include this file and call its functions; nothing here reads
 * or writes the DOM outside of the element it returns from criarBarra.
 *
 * Import order matters: load this script before any inline script that
 * calls window.ProgressBar.*.
 */
(function () {
    // Builds the bar element: an optional label (plain text, or a link when
    // href is given) plus the "ac/total" count and the filled bar itself.
    // label is omitted entirely when falsy (e.g. a level's own row already
    // shows its title elsewhere and doesn't need it repeated here).
    function criarBarra(ac, total, label, href) {
        const pct = total ? Math.round((ac / total) * 100) : 0;

        const wrap = document.createElement("div");
        wrap.className = "barra-wrap";

        const labelRow = document.createElement("div");
        labelRow.className = "barra-label";
        labelRow.style.justifyContent = label ? "space-between" : "flex-end";

        if (label) {
            const labelEl = document.createElement(href ? "a" : "span");
            labelEl.className = href ? "barra-label-link" : "barra-label-text";
            if (href) labelEl.href = href;
            labelEl.textContent = label;
            labelRow.appendChild(labelEl);
        }

        const countEl = document.createElement("span");
        countEl.textContent = `${ac}/${total} problemas`;
        labelRow.appendChild(countEl);

        wrap.appendChild(labelRow);

        const barBg = document.createElement("div");
        barBg.className = "barra-fundo";
        const barFill = document.createElement("div");
        barFill.className = "barra-preenchida";
        barFill.style.width = `${pct}%`;
        barBg.appendChild(barFill);
        wrap.appendChild(barBg);

        return wrap;
    }

    // How many problems of one topic are marked done, given the map
    // returned by GET /progress (item_key -> {kind, done, ...}). item_key is
    // "<topic_slug>:<kind_curto>:<item_slug>" (ver _serialize_item no
    // app.py), então basta conferir o prefixo "<topic_slug>:prob:".
    function contarFeitos(progress, topicSlug) {
        let ac = 0;
        const prefix = `${topicSlug}:prob:`;
        for (const [key, item] of Object.entries(progress)) {
            if (item.kind === "problem" && item.done && key.startsWith(prefix)) {
                ac += 1;
            }
        }
        return ac;
    }

    // Real number of problems in a topic, from the topic's own content
    // (GET /topics/<slug>). This must NOT come from GET /progress: that
    // endpoint only lists items the user has already clicked at least once,
    // so using it as the denominator makes the bar always read 0% or 100%.
    async function totalProblemas(topicSlug) {
        try {
            const res = await fetch(`/topics/${encodeURIComponent(topicSlug)}`, {
                credentials: "same-origin",
            });
            if (!res.ok) return 0;
            const topic = await res.json();
            return (topic.problems || []).length;
        } catch (err) {
            return 0;
        }
    }

    window.ProgressBar = { criarBarra, contarFeitos, totalProblemas };
})();