/*
 * Shared auth widget — the top-corner Entrar/Sair control used on every page.
 *
 * A page opts in by including this script plus auth-widget.css and placing an
 * empty mount in its header:
 *     <span id="auth-controls"></span>
 *
 * The widget fills that mount (Entrar when logged out; "Olá, <user>" + Sair when
 * logged in), injects the login/register modal into the page, checks the current
 * session via GET /me, and dispatches a window "auth:change" event
 * ({ detail: { user } }, user is null when logged out) whenever the state
 * changes — so a page can react (e.g. show a dashboard) without its own /me call.
 */
(function () {
    "use strict";

    const MOUNT_ID = "auth-controls";

    async function postJSON(path, body) {
        const res = await fetch(path, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
            credentials: "same-origin",
        });
        let data = {};
        try {
            data = await res.json();
        } catch (e) {
            /* empty / non-JSON body */
        }
        return { ok: res.ok, status: res.status, data };
    }

    function showMessage(el, text, type) {
        el.textContent = text;
        el.className = "form-msg" + (type ? " " + type : "");
    }

    const MODAL_HTML = `
        <form method="dialog" class="auth-dialog-head">
            <h2>Acesse sua conta</h2>
            <button class="dialog-close" type="submit" aria-label="Fechar">✕</button>
        </form>
        <div class="auth-tabs">
            <button class="auth-tab active" type="button" data-target="login">Entrar</button>
            <button class="auth-tab" type="button" data-target="register">Criar conta</button>
        </div>
        <form class="auth-form" id="login-form" novalidate>
            <div class="field">
                <label for="login-username">Usuário</label>
                <input id="login-username" name="username" type="text" autocomplete="username" required>
            </div>
            <div class="field">
                <label for="login-password">Senha</label>
                <input id="login-password" name="password" type="password" autocomplete="current-password" required>
            </div>
            <button class="btn-primary" type="submit">Entrar</button>
            <p class="form-msg" id="login-msg" role="status" aria-live="polite"></p>
        </form>
        <form class="auth-form auth-hidden" id="register-form" novalidate>
            <div class="field">
                <label for="register-username">Usuário</label>
                <input id="register-username" name="username" type="text" autocomplete="username" required>
            </div>
            <div class="field">
                <label for="register-password">Senha</label>
                <input id="register-password" name="password" type="password" autocomplete="new-password" required>
            </div>
            <button class="btn-primary" type="submit">Criar conta</button>
            <p class="form-msg" id="register-msg" role="status" aria-live="polite"></p>
        </form>
    `;

    const CONTROLS_HTML = `
        <button id="signin-btn" type="button">Entrar</button>
        <span id="user-greeting" class="user-greeting auth-hidden">Olá, <strong id="header-username"></strong></span>
        <button id="logout-btn" class="auth-hidden" type="button">Sair</button>
    `;

    function init() {
        const mount = document.getElementById(MOUNT_ID);
        if (!mount) return; // page didn't opt in

        // --- Build the modal -------------------------------------------------
        const dialog = document.createElement("dialog");
        dialog.className = "auth-dialog";
        dialog.id = "auth-dialog";
        dialog.innerHTML = MODAL_HTML;
        document.body.appendChild(dialog);

        // --- Build the header controls --------------------------------------
        mount.innerHTML = CONTROLS_HTML;
        const signinBtn = mount.querySelector("#signin-btn");
        const greeting = mount.querySelector("#user-greeting");
        const headerUsername = mount.querySelector("#header-username");
        const logoutBtn = mount.querySelector("#logout-btn");

        const forms = {
            login: dialog.querySelector("#login-form"),
            register: dialog.querySelector("#register-form"),
        };
        const loginMsg = dialog.querySelector("#login-msg");
        const registerMsg = dialog.querySelector("#register-msg");

        function emit(user) {
            window.dispatchEvent(new CustomEvent("auth:change", { detail: { user: user || null } }));
        }

        function setLoggedIn(username) {
            headerUsername.textContent = username;
            signinBtn.classList.add("auth-hidden");
            greeting.classList.remove("auth-hidden");
            logoutBtn.classList.remove("auth-hidden");
            if (dialog.open) dialog.close();
            emit({ username });
        }

        function setLoggedOut() {
            signinBtn.classList.remove("auth-hidden");
            greeting.classList.add("auth-hidden");
            logoutBtn.classList.add("auth-hidden");
            emit(null);
        }

        // --- Modal open / close ---------------------------------------------
        signinBtn.addEventListener("click", () => {
            if (typeof dialog.showModal === "function") dialog.showModal();
            else dialog.setAttribute("open", "");
        });
        dialog.addEventListener("click", (e) => {
            if (e.target === dialog) dialog.close();
        });

        // --- Tab switching ---------------------------------------------------
        dialog.querySelectorAll(".auth-tab").forEach((tab) => {
            tab.addEventListener("click", () => {
                dialog.querySelectorAll(".auth-tab").forEach((t) => t.classList.remove("active"));
                tab.classList.add("active");
                Object.entries(forms).forEach(([name, form]) => {
                    form.classList.toggle("auth-hidden", name !== tab.dataset.target);
                });
            });
        });

        // --- Login -----------------------------------------------------------
        forms.login.addEventListener("submit", async (e) => {
            e.preventDefault();
            const username = forms.login.username.value.trim();
            const password = forms.login.password.value;
            if (!username || !password) {
                showMessage(loginMsg, "Preencha usuário e senha.", "error");
                return;
            }
            const button = forms.login.querySelector("button[type=submit]");
            button.disabled = true;
            showMessage(loginMsg, "Entrando...", null);
            try {
                const { ok, status, data } = await postJSON("/login", { username, password });
                if (ok) {
                    forms.login.reset();
                    showMessage(loginMsg, "", null);
                    setLoggedIn(data.username);
                } else if (status === 401) {
                    showMessage(loginMsg, "Usuário ou senha inválidos.", "error");
                } else {
                    showMessage(loginMsg, data.error || "Falha ao entrar.", "error");
                }
            } catch (err) {
                showMessage(loginMsg, "Não foi possível conectar ao servidor.", "error");
            } finally {
                button.disabled = false;
            }
        });

        // --- Register (creates the account and logs in) ----------------------
        forms.register.addEventListener("submit", async (e) => {
            e.preventDefault();
            const username = forms.register.username.value.trim();
            const password = forms.register.password.value;
            if (!username || !password) {
                showMessage(registerMsg, "Preencha usuário e senha.", "error");
                return;
            }
            const button = forms.register.querySelector("button[type=submit]");
            button.disabled = true;
            showMessage(registerMsg, "Criando conta...", null);
            try {
                const reg = await postJSON("/register", { username, password });
                if (!reg.ok) {
                    const msg = reg.status === 409
                        ? "Esse usuário já existe. Escolha outro."
                        : reg.data.error || "Falha ao criar conta.";
                    showMessage(registerMsg, msg, "error");
                    return;
                }
                const login = await postJSON("/login", { username, password });
                if (login.ok) {
                    forms.register.reset();
                    showMessage(registerMsg, "", null);
                    setLoggedIn(login.data.username);
                } else {
                    showMessage(registerMsg, "Conta criada. Faça login para entrar.", "success");
                }
            } catch (err) {
                showMessage(registerMsg, "Não foi possível conectar ao servidor.", "error");
            } finally {
                button.disabled = false;
            }
        });

        // --- Logout ----------------------------------------------------------
        logoutBtn.addEventListener("click", async () => {
            try {
                await fetch("/logout", { method: "POST", credentials: "same-origin" });
            } catch (err) {
                /* ignore: clear the UI regardless */
            }
            setLoggedOut();
        });

        // --- Reflect the existing session on load ----------------------------
        (async () => {
            try {
                const res = await fetch("/me", { credentials: "same-origin" });
                if (res.ok) {
                    const data = await res.json();
                    setLoggedIn(data.username);
                    return;
                }
            } catch (err) {
                /* no backend / no session: fall through to logged-out */
            }
            setLoggedOut();
        })();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
