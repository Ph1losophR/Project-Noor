/* Design system §12.1's whole admitted scope: the section autosave, and nothing else.
 *
 * It decides *when* to post, never *what is true*. The server validates an autosaved post
 * exactly as it validates a button press, which means an incomplete form is refused with a
 * 400 and nothing is stored — so the response is not read. Delete this file and every
 * section still saves on the submit that navigates away from it; §12.1's third rule and
 * §14 both say that in as many words.
 *
 * On `change` rather than on `input`: `change` fires when a box is left, so a section posts
 * once per field filled instead of once per keystroke. No timer, no debounce, no state.
 */
for (const form of document.querySelectorAll("form[data-autosave]")) {
  form.addEventListener("change", () => {
    fetch(form.action, { method: "POST", body: new FormData(form) });
  });
}
