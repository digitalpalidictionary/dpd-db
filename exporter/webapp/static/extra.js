function toggleSettings() {
  const settingsContent = document.getElementById('settings-content');

  // Получаем текущий стиль элемента через getComputedStyle
  const currentDisplay = window.getComputedStyle(settingsContent).display;

  // Переключаем видимость панели
  if (currentDisplay === 'none') {
    settingsContent.style.display = 'block';
  } else {
    settingsContent.style.display = 'none';
  }
}