(() => {
    const toggle = document.getElementById("auth-password-toggle");
    const input = document.getElementById("auth-password");

    if (toggle && input) {
        toggle.addEventListener("click", () => {
            const visible = input.type === "text";
            input.type = visible ? "password" : "text";
            toggle.setAttribute("aria-label", visible ? "Show password" : "Hide password");
        });
    }
})();
