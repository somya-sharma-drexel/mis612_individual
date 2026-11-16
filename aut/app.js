// Registration page: no storage, no backend. Validates input and shows HELLO WORLD on success.
const MIN_PASSWORD_LENGTH = 8;

const form = document.getElementById("register-form");
const errorEl = document.getElementById("error");
const successEl = document.getElementById("success");

function validate(username, password) {
  if (!username.trim()) return "Username is required.";
  if (!password) return "Password is required.";
  if (password.length < MIN_PASSWORD_LENGTH) {
    return "Password must be at least " + MIN_PASSWORD_LENGTH + " characters.";
  }
  return null;
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = validate(form.username.value, form.password.value);
  if (message) {
    successEl.hidden = true;
    errorEl.textContent = message;
    errorEl.hidden = false;
    return;
  }
  errorEl.hidden = true;
  successEl.hidden = false;
});
