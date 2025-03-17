function toggleSettings() {
  const settingsContent = document.getElementById('settings-content');
  
  // Проверяем, является ли устройство мобильным (ширина экрана меньше 769px)
  if (window.innerWidth < 769) {
    // Переключаем видимость панели
    if (settingsContent.style.display === 'none' || !settingsContent.style.display) {
      settingsContent.style.display = 'block';
    } else {
      settingsContent.style.display = 'none';
    }
  }
}

// Обработчик события для изменения размера окна
window.addEventListener('resize', function() {
  const settingsContent = document.getElementById('settings-content');
  
  // Если окно больше 769px (десктоп), автоматически раскроем панель
  if (window.innerWidth >= 769) {
    settingsContent.style.display = 'block';
  } else {
    // Если окно меньше 769px (мобильное), скрываем панель
    settingsContent.style.display = 'none';
  }
});


function toggleHistory() {
  const historyContent = document.getElementById('history-content');
  
  // Проверяем, является ли устройство мобильным (ширина экрана меньше 769px)
  if (window.innerWidth < 769) {
    // Переключаем видимость панели
    if (historyContent.style.display === 'none' || !historyContent.style.display) {
      historyContent.style.display = 'block';
    } else {
      historyContent.style.display = 'none';
    }
  }
}

// Обработчик события для изменения размера окна
window.addEventListener('resize', function() {
  const historyContent = document.getElementById('history-content');
  
  // Если окно больше 769px (десктоп), автоматически раскроем панель
  if (window.innerWidth >= 769) {
    historyContent.style.display = 'block';
  } else {
    // Если окно меньше 769px (мобильное), скрываем панель
    historyContent.style.display = 'none';
  }
});


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

document.addEventListener("DOMContentLoaded", function () {
    const tabsToggle = document.getElementById("tabs-toggle");
    const tabContainer = document.getElementById("tab-container");

    // Проверяем, существуют ли элементы перед выполнением кода
    if (!tabsToggle || !tabContainer) {
        return;
    }

    // Проверяем состояние в localStorage или скрываем по умолчанию
    if (localStorage.getItem("tabsHidden") === null || localStorage.getItem("tabsHidden") === "true") {
        tabContainer.classList.add("hidden");
        tabsToggle.checked = true;
        localStorage.setItem("tabsHidden", "true"); // Запоминаем состояние
    }

    // Обработчик переключения
    tabsToggle.addEventListener("change", function () {
        const isHidden = this.checked;
        tabContainer.classList.toggle("hidden", isHidden);
        localStorage.setItem("tabsHidden", isHidden ? "true" : "false");
    });
});