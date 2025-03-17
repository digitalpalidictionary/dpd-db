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


/*
// Обнуляем существующую функцию changeLanguage
if (typeof changeLanguage === 'function') {
  changeLanguage = function() {}; // Заменяем на пустую функцию
}

// Модифицированная функция changeLanguage
function changeLanguage(lang) {
  // Получаем текущий URL и разбиваем его на части
  const url = new URL(window.location.href);
  let path = url.pathname; // Путь (например, "/ru")
  const searchParams = url.search; // Параметры запроса (например, "?q=dukkha")
  const hash = url.hash; // Хэш (например, "#section")

  // Удаляем все существующие вхождения '/ru' из пути
  path = path.replace(/^\/ru/, '');

  // Если выбран язык 'ru', добавляем '/ru' в начало пути
  if (lang === 'ru') {
    path = '/ru' + path;
  }

  // Обновляем путь в URL
  url.pathname = path;

  // Принудительно обновляем страницу с новым URL
  window.location.href = url.toString();
}

*/