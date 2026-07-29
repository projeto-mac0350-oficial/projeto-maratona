const params = new URLSearchParams(window.location.search);

if (params.get("logout") === "1") {

    const logoutDialog = document.createElement("dialog");
    logoutDialog.className = "auth-dialog";

    logoutDialog.innerHTML = `
        <div class="logout-dialog">
            <h2>Você saiu da sua conta</h2>
            <p>Faça login novamente em <strong>Entrar</strong> quando desejar.</p>

            <div class="logout-progress">
                <div class="logout-progress-bar"></div>
            </div>
        </div>
    `;

    document.body.appendChild(logoutDialog);
    logoutDialog.showModal();
    history.replaceState({}, "", "/");

    const closeDialog = () => {
        if (logoutDialog.open) {
            logoutDialog.close();
            logoutDialog.remove();
        }
    };
    const timer = setTimeout(closeDialog, 3000);
    logoutDialog.addEventListener(
        "click",
        (e) => {
            if (e.target === logoutDialog) {
                clearTimeout(timer);
                closeDialog();
            }
        },
        { once: true }
    );
}