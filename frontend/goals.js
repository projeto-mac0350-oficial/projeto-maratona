/* --- Metas ("Suas metas") ------------------------------------------------- */
const metasList = document.getElementById("metas-list");
const metaForm = document.getElementById("meta-form");
const metaDescricao = document.getElementById("meta-descricao");
const metaDia = document.getElementById("meta-dia");
const metaMes = document.getElementById("meta-mes");
const metaFormError = document.getElementById("meta-form-error");
const btnDefinirMeta = document.getElementById("btn-definir-meta");
const btnCancelarMeta = document.getElementById("meta-cancelar");

function showMetaFormError(message) {
    metaFormError.textContent = message;
    metaFormError.classList.remove("hidden");
}

function resetMetaForm() {
    metaDescricao.value = "";
    metaDia.value = "";
    metaMes.value = "";
    metaFormError.classList.add("hidden");
    metaFormError.textContent = "";
}

btnDefinirMeta.addEventListener("click", () => {
    metaForm.classList.remove("hidden");
    btnDefinirMeta.classList.add("hidden");
    metaDescricao.focus();
});

btnCancelarMeta.addEventListener("click", () => {
    resetMetaForm();
    metaForm.classList.add("hidden");
    btnDefinirMeta.classList.remove("hidden");
});

function renderGoals(goals) {
    metasList.innerHTML = "";
    if (!goals.length) {
        const li = document.createElement("li");
        li.className = "metas-empty";
        li.textContent = "Nenhuma meta definida ainda.";
        metasList.appendChild(li);
        return;
    }
    goals.forEach((goal) => {
        const li = document.createElement("li");
        li.className = "meta-item";

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.addEventListener("change", () => completeGoal(goal.id, li));

        const text = document.createElement("span");
        text.className = "meta-item-text";
        text.textContent = goal.description;

        li.appendChild(checkbox);
        li.appendChild(text);

        if (goal.due_day && goal.due_month) {
            const due = document.createElement("span");
            due.className = "meta-item-due";
            const dia = String(goal.due_day).padStart(2, "0");
            const mes = String(goal.due_month).padStart(2, "0");
            due.textContent = `até ${dia}/${mes}`;
            li.appendChild(due);
        }

        metasList.appendChild(li);
    });
}

async function loadGoals() {
    try {
        const res = await fetch("/goals", { credentials: "same-origin" });
        if (!res.ok) throw new Error("request failed");
        renderGoals(await res.json());
    } catch (err) {
        metasList.innerHTML = '<li class="metas-empty">Não foi possível carregar as metas.</li>';
    }
}

async function completeGoal(id, li) {
    // A meta "concluída" simplesmente some — não existe estado "feito" salvo.
    li.remove();
    try {
        const res = await fetch(`/goals/${id}`, {
            method: "DELETE",
            credentials: "same-origin",
        });
        if (!res.ok) throw new Error("request failed");
        if (!metasList.children.length) renderGoals([]);
    } catch (err) {
        // Falhou: recarrega a lista de verdade pra não ficar dessincronizado.
        loadGoals();
    }
}

metaForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    metaFormError.classList.add("hidden");

    const description = metaDescricao.value.trim();
    if (!description) {
        showMetaFormError("Descreva a meta.");
        return;
    }
    if (description.length > 100) {
        showMetaFormError("A descrição pode ter no máximo 100 caracteres.");
        return;
    }

    const diaRaw = metaDia.value.trim();
    const mesRaw = metaMes.value.trim();
    if (Boolean(diaRaw) !== Boolean(mesRaw)) {
        showMetaFormError("Preencha dia e mês, ou deixe os dois em branco.");
        return;
    }

    const body = { description };
    if (diaRaw && mesRaw) {
        const dia = Number(diaRaw);
        const mes = Number(mesRaw);
        if (!Number.isInteger(dia) || dia < 1 || dia > 31 || !Number.isInteger(mes) || mes < 1 || mes > 12) {
            showMetaFormError("Prazo inválido — confira o dia e o mês.");
            return;
        }
        body.due_day = dia;
        body.due_month = mes;
    }

    try {
        const res = await fetch("/goals", {
            method: "POST",
            credentials: "same-origin",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            showMetaFormError(data.error || "Não foi possível salvar a meta.");
            return;
        }
        resetMetaForm();
        metaForm.classList.add("hidden");
        btnDefinirMeta.classList.remove("hidden");
        loadGoals();
    } catch (err) {
        showMetaFormError("Não foi possível salvar a meta.");
    }
});