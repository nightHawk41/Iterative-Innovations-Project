let showToastHandler = null;

export function registerToast(fn) {
  showToastHandler = fn;
}

export function showToast(message) {
  if (showToastHandler) {
    showToastHandler(message);
  }
}
