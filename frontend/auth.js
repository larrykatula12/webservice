const API_URL = "http://127.0.0.1:8000";

// =================== LOGIN =====================
const loginForm = document.getElementById("loginForm");

if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;

        const formData = new URLSearchParams();
        formData.append("username", username);
        formData.append("password", password);

        const response = await fetch(`${API_URL}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: formData
        });

        const data = await response.json();

        if (response.status !== 200) {
            document.getElementById("error").textContent = data.detail || "Error de inicio de sesión";
            return;
        }

        localStorage.setItem("token", data.access_token);

        window.location.href = "dashboard.html";
    });
}

// =================== CARGAR DATOS DEL USUARIO =====================
async function loadUserData() {
    const token = localStorage.getItem("token");

    if (!token) {
        window.location.href = "login.html";
        return;
    }

    const response = await fetch(`${API_URL}/usuario/me`, {
        method: "GET",
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    if (response.status !== 200) {
        logout();
        return;
    }

    const data = await response.json();

    document.getElementById("userData").innerHTML = `
        <p><strong>ID:</strong> ${data.id}</p>
        <p><strong>Usuario:</strong> ${data.usuario}</p>
        <p><strong>Correo:</strong> ${data.correo}</p>
        <p><strong>Rol:</strong> ${data.rol}</p>
        ${data.nombre ? `<p><strong>Nombre Alumno:</strong> ${data.nombre} ${data.apellido_paterno}</p>` : ""}
    `;
}

// =================== LOGOUT =====================
function logout() {
    localStorage.removeItem("token");
    window.location.href = "login.html";
}
