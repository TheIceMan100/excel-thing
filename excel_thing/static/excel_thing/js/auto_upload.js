document.querySelectorAll("[data-submit-on-change]").forEach((input) => {
  input.addEventListener("change", () => {
    if (input.files.length > 0) {
      input.form.requestSubmit();
    }
  });
});
