// elements

const bdTitleClear = document.getElementById("bd-title-clear");
const bdSearchBox1 = document.getElementById("bd-search-box-1");
const bdSearchBox2 = document.getElementById("bd-search-box-2");
// const bdSearchForm = document.getElementById('bd-search-form'); // Not needed anymore
const bdSearchButton = document.getElementById("bd-search-button");
const bdResults = document.getElementById("bd-results");
const bdFooterText = document.querySelector("#bold-def-tab .footer-pane");
const bdSearchOptions = document.getElementsByName("option");
const bdStartsWithButton = document.getElementById("option1");

// Make bdLanguage accessible in the script's scope
let bdLanguage;

const bdRegexButton = document.getElementById("option2");
const bdFuzzyButton = document.getElementById("option3");

/////////// listeners

const bdClearButton = document.querySelector(".bd-search-option-clear");

function clearBdResults() {
  bdResults.innerHTML = "";
  bdSearchBox1.value = "";
  bdSearchBox2.value = "";
}

bdClearButton.addEventListener("click", clearBdResults);

// trigger search

// Let app.js handle the search
// bdSearchBox1.addEventListener('keydown', function (event) {
//     if (event.key === 'Enter') {
//         handleBdFormSubmit(event);
//     }
// });

// bdSearchBox2.addEventListener('keydown', function (event) {
//     if (event.key === 'Enter') {
//         handleBdFormSubmit(event);
//     }
// });

// bdSearchButton.addEventListener('click', handleBdFormSubmit);

// Set up event listeners when the page loads
document.addEventListener("DOMContentLoaded", function () {
  const htmlElement = document.documentElement;
  bdLanguage = htmlElement.lang || "en"; // Assign to the outer scope variable

  // Set up event listeners for search boxes and button
  bdSearchBox1.addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
      window.performSearch();
    }
  });

  bdSearchBox2.addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
      window.performSearch();
    }
  });

  bdSearchButton.addEventListener("click", function (event) {
    event.preventDefault();
    window.performSearch();
  });
});

// text to unicode

bdSearchBox1.addEventListener("input", function () {
  let textInput = bdSearchBox1.value;
  let convertedText = uniCoder(textInput);
  bdSearchBox1.value = convertedText;
});

bdSearchBox2.addEventListener("input", function () {
  let textInput = bdSearchBox2.value;
  let convertedText = uniCoder(textInput);
  bdSearchBox2.value = convertedText;
});

function uniCoder(textInput) {
  if (!textInput || textInput == "") return textInput;
  return textInput
    .replace(/aa/g, "ā")
    .replace(/ii/g, "ī")
    .replace(/uu/g, "ū")
    .replace(/\"n/g, "ṅ")
    .replace(/\~n/g, "ñ")
    .replace(/\.t/g, "ṭ")
    .replace(/\.d/g, "ḍ")
    .replace(/\.n/g, "ṇ")
    .replace(/\.m/g, "ṃ")
    .replace(/\.l/g, "ḷ")
    .replace(/\.h/g, "ḥ");
}

// contextual help listeners

bdSearchBox1.addEventListener("mouseenter", function () {
  hoverHelp("searchBox1");
});
bdSearchBox1.addEventListener("mouseleave", function () {
  hoverHelp("default");
});
bdSearchBox2.addEventListener("mouseenter", function () {
  hoverHelp("searchBox2");
});
bdSearchBox2.addEventListener("mouseleave", function () {
  hoverHelp("default");
});

document
  .querySelector('label[for="option1"]')
  .addEventListener("mouseenter", function () {
    hoverHelp("startsWithButton");
  });
document
  .querySelector('label[for="option1"]')
  .addEventListener("mouseleave", function () {
    hoverHelp("default");
  });

document
  .querySelector('label[for="option2"]')
  .addEventListener("mouseenter", function () {
    hoverHelp("regexButton");
  });
document
  .querySelector('label[for="option2"]')
  .addEventListener("mouseleave", function () {
    hoverHelp("default");
  });

document
  .querySelector('label[for="option3"]')
  .addEventListener("mouseenter", function () {
    hoverHelp("fuzzyButton");
  });
document
  .querySelector('label[for="option3"]')
  .addEventListener("mouseleave", function () {
    hoverHelp("default");
  });

bdClearButton.addEventListener("mouseenter", function () {
  hoverHelp("clearButton");
});
bdClearButton.addEventListener("mouseleave", function () {
  hoverHelp("default");
});

// contextual help

function hoverHelp(event) {
  if (event == "searchBox1") {
    if (bdLanguage === "ru") {
      bdFooterText.innerHTML = "Какой определенный термин Пали вы ищете?";
    } else {
      bdFooterText.innerHTML =
        "What is the defined Pāḷi term you are looking for?";
    }
  } else if (event == "searchBox2") {
    if (bdLanguage === "ru") {
      bdFooterText.innerHTML =
        "Используйте это поле для поиска внутри результатов.";
    } else {
      bdFooterText.innerHTML = "Use this box to search within results.";
    }
  } else if (event == "startsWithButton") {
    if (bdLanguage === "ru") {
      bdFooterText.innerHTML =
        "Искать определения, <b>начинающиеся</b> с термина.";
    } else {
      bdFooterText.innerHTML =
        "Search for definitions <b>starting</b> with the term.";
    }
  } else if (event == "regexButton") {
    if (bdLanguage === "ru") {
      bdFooterText.innerHTML =
        "Это <b>обычный</b> режим. Вы также можете использовать <b>регулярные выражения</b> для очень точных поисков.";
    } else {
      bdFooterText.innerHTML =
        "This is the <b>normal</b> mode. You can also use <b>regular expressions</b> for very precise searches.";
    }
  } else if (event == "fuzzyButton") {
    if (bdLanguage === "ru") {
      bdFooterText.innerHTML =
        "<b>Приблизительный</b> поиск игнорирует все диакритические знаки и двойные согласные. Это полезно, если вы не знаете точного написания.";
    } else {
      bdFooterText.innerHTML =
        "<b>Fuzzy</b> search ignores all diacritics and double consonants. It's useful if you don't know the exact spelling.";
    }
  } else if (event == "clearButton") {
    if (bdLanguage === "ru") {
      bdFooterText.innerHTML =
        "Начните снова со спокойным и <b>чистым</b> интерфейсом.";
    } else {
      bdFooterText.innerHTML =
        "Start again with a calm and <b>clear</b> interface.";
    }
  } else {
    // Default case
    if (bdLanguage === "ru") {
      // Assuming the Russian docs link should also have /ru/
      bdFooterText.innerHTML =
        'Для получения подробной информации об этой функции, пожалуйста, <a href="https://digitalpalidictionary.github.io/ru/webapp/cst_bold_def/" target="_blank">прочтите документацию</a>. Используются тексты <a href="https://github.com/VipassanaTech/tipitaka-xml" target="_blank">Vipassana Research Institute</a>';
    } else {
      bdFooterText.innerHTML =
        'For detailed information on this feature, please <a href="https://digitalpalidictionary.github.io/webapp/cst_bold_def/" target="_blank">read the docs</a>. This uses <a href="https://github.com/VipassanaTech/tipitaka-xml" target="_blank">Vipassana Research Institute</a> texts';
    }
  }
}

// Let app.js handle the search
// async function handleBdFormSubmit(event) {
//     if (event) {
//         event.preventDefault();
//     }
//     // Let app.js handle the search
//     window.performSearch();
// }

// Add double-click event listener for BD tab
document.addEventListener("DOMContentLoaded", function () {
  // Add double-click listener to BD results area
  const bdResults = document.getElementById("bd-results");
  if (bdResults) {
    bdResults.addEventListener("dblclick", processBdSelection);
  }
});

function processBdSelection() {
  const selection = window.getSelection().toString();
  if (selection.trim() !== "") {
    // Switch to BD tab if not already active
    if (typeof appState !== "undefined" && appState.activeTab !== "bd") {
      window.switchTab("bd");
    }

    // Set the selected text in the first BD search box
    const bdSearchBox1 = document.getElementById("bd-search-box-1");
    if (bdSearchBox1) {
      bdSearchBox1.value = selection;
      // Update appState
      if (typeof appState !== "undefined") {
        appState.bd.searchTerm1 = selection;
      }
      // Trigger BD search
      window.performSearch();
    }
  }
}
