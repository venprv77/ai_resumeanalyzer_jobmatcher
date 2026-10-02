document.addEventListener("DOMContentLoaded", function () {

    // -----------------------------
    // Password validation
    // -----------------------------

    const registerForm = document.querySelector(
        "form[action*='register']"
    );

    if (registerForm) {

        registerForm.addEventListener("submit", function (event) {

            const password = document.querySelector(
                "input[name='password']"
            );

            if (password && password.value.length < 6) {

                alert(
                    "Password must contain at least 6 characters."
                );

                event.preventDefault();
            }

        });
    }


    // -----------------------------
    // Resume file validation
    // -----------------------------

    const resumeInput = document.querySelector(
        "input[name='resume']"
    );

    if (resumeInput) {

        resumeInput.addEventListener("change", function () {

            const file = this.files[0];

            if (!file) {
                return;
            }

            // Check PDF
            if (file.type !== "application/pdf") {

                alert("Please select a PDF file.");

                this.value = "";

                return;
            }


            // Check file size
            const maxSize = 5 * 1024 * 1024;

            if (file.size > maxSize) {

                alert(
                    "Resume size must be less than 5 MB."
                );

                this.value = "";

                return;
            }

        });
    }


    // -----------------------------
    // Upload loading message
    // -----------------------------

    const uploadForm = document.querySelector(
        "form[action*='upload_resume']"
    );

    if (uploadForm) {

        uploadForm.addEventListener("submit", function () {

            const button = this.querySelector(
                "button[type='submit']"
            );

            if (button) {

                button.disabled = true;

                button.innerText =
                    "Uploading...";

            }

        });
    }


    // -----------------------------
    // Flash message auto-hide
    // -----------------------------

    const messages = document.querySelectorAll(
        ".message"
    );

    messages.forEach(function (message) {

        setTimeout(function () {

            message.style.opacity = "0";

            setTimeout(function () {

                message.remove();

            }, 500);

        }, 4000);

    });


    // -----------------------------
    // Confirm logout
    // -----------------------------

    const logoutLinks = document.querySelectorAll(
        "a[href*='logout']"
    );

    logoutLinks.forEach(function (link) {

        link.addEventListener("click", function (event) {

            const confirmLogout = confirm(
                "Are you sure you want to logout?"
            );

            if (!confirmLogout) {

                event.preventDefault();

            }

        });

    });

});