document.addEventListener('DOMContentLoaded', function() {
  $.ajax({
    url: "/static/sutta_words.txt",
    dataType: "text",
    success: function(data) {

      var accentMap = {
        "ā": "a",
        "ī": "i",
        "ū": "u",
        "ḍ": "d",
        "ḷ": "l",
        "ṃ": "ṁ",
        "ṁ": "n",
        "ṁ": "m",
        "ṅ": "n",
        "ṇ": "n",
        "ṭ": "t",
        "ñ": "n",
        "ññ": "n",
        "ss": "s",
        "aa": "a",
        "ii": "i",
        "uu": "u",
        "dd": "d",
        "kk": "k",
        "ḍḍ": "d",
        "ḷḷ": "l",
        "ṇṇ": "n",
        "ṭṭ": "t",
        "cc": "c",
        "pp": "p",
        "cch": "c",
        "ch": "c",
        "kh": "k",
        "ph": "p",
        "th": "t",
        "ṭh": "t"
      };

      // Функция для нормализации слова (убираем диакритику)
      var normalize = function(term) {
        var ret = "";
        for (var i = 0; i < term.length; i++) {
          ret += accentMap[term.charAt(i)] || term.charAt(i);
        }
        return ret;
      };

      var allWords = data.split('\n');

      $("#search-box").autocomplete({
        position: {
          my: "left bottom",
          at: "left top",
          collision: "flip"
        },
        minLength: 0,
        multiple: /[\s\*]/, // изменение регулярного выражения для разделения по пробелу или звездочке
        source: function(request, response) {
          var terms = request.term.split(/[\|\s\*]/); // изменение регулярного выражения для разделения по пробелу или звездочке или |
          var lastTerm = terms.pop().trim();
          var otherMinLength = 3;

          if (lastTerm.length < otherMinLength) {
            response([]);
            return;
          }

          // Нормализуем введенный термин (убираем диакритику)
          var normalizedTerm = normalize(lastTerm);

          // Модифицируем регулярное выражение для учета двойных букв
          var re = $.ui.autocomplete.escapeRegex(normalizedTerm);
          var modifiedRe = re.replace(/([a-zA-Z])/g, "$1{1,2}");
          var matchbeginonly = new RegExp("^" + modifiedRe, "i");
          var matchall = new RegExp(modifiedRe, "i");

          var listBeginOnly = $.grep(allWords, function(value) {
            value = value.label || value.value || value;
            var normalizedValue = normalize(value); // Нормализуем слово из списка
            return matchbeginonly.test(normalizedValue); // Ищем совпадения
          });

          var listAll = $.grep(allWords, function(value) {
            value = value.label || value.value || value;
            var normalizedValue = normalize(value); // Нормализуем слово из списка
            return matchall.test(normalizedValue); // Ищем совпадения
          });

          listAll = listAll.filter(function(el) {
            return !listBeginOnly.includes(el);
          });

          // Ограничение количества подсказок до 10
          var maxRecord = 1000;
          var resultList = listBeginOnly.concat(listAll).slice(0, maxRecord);

          response(resultList);
        },
        focus: function(event, ui) {
          // Удаляем автоматическое введение при наведении мыши
          return false;
        },
        select: function(event, ui) {
          var terms = this.value.split(/([\|\s\*])/);
          terms.pop();
          terms.push(ui.item.value);

          for (var i = 1; i < terms.length; i += 2) {
            if (terms[i] === "*") {
              terms[i] = "*";
            } else if (terms[i] === "|") {
              terms[i] = "|";
            } else {
              terms[i] = " ";
            }
          }

          this.value = terms.join("");
          return false;
        }
      }).autocomplete("widget").addClass("fixed-height");
    }
  });
});
