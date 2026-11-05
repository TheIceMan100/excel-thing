document.querySelectorAll("[data-display-filename]").forEach((input) => {
  input.addEventListener("change", () => {
    const label = document.getElementById(input.dataset.displayFilename);
    if (label) {
      label.textContent = input.files[0]?.name ?? label.dataset.defaultText;
    }
  });
});

document.querySelectorAll("[data-submit-on-change]").forEach((input) => {
  input.addEventListener("change", () => {
    if (input.files.length > 0) {
      input.form.requestSubmit();
    }
  });
});
