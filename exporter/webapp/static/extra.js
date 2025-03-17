function toggleSettings() {
  const settingsContent = document.getElementById('settings-content');
  
  // Переключаем видимость панели
  if (settingsContent.style.display === 'none') {
    settingsContent.style.display = 'block';
  } else {
    settingsContent.style.display = 'none';
  }
}