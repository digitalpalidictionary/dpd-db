
# Руководство по корректировке русских переводов

Большое количество слов в словаре переведено с использованием нейронных сетей и нуждается в корректировке. Это руководство поможет вам внести изменения, соблюдая единый формат.

---

## 1. Как оставить отзыв

### Индивидуальные отзывы
Вы можете оставить отзыв через [Google-форму](https://docs.google.com/forms/d/1iMD9sCSWFfJAFCFYuG9HRIyrr9KFRy0nAOVApM998wM/viewform?) или воспользоваться кнопками [пер. ИИ] и [перевести], чтобы открыть соответствующую форму.

---

## 2. Работа со списком слов

### Скачивание и использование файлов
Для удобства работы регулярно обновляются два файла:

- **[ru_total_roots.tsv](https://github.com/digitalpalidictionary/dpd-db/blob/main/dps/rus/ru_total_roots.tsv)**  
  Все слова отсортированы по корню и семье корня, начиная с наиболее частых.  

- **[ru_total_comps.tsv](https://github.com/digitalpalidictionary/dpd-db/blob/main/dps/rus/ru_total_comps.tsv)**  
  Все составные слова отсортированы по элементам, начиная с наиболее частых.  

### Редактирование
1. Выберите слово или корень, скопируйте слова в отдельный файл. (например все слова имеющие корень √kar)
2. Отметьте слово или корень что вы выбрали [в таблице](https://docs.google.com/spreadsheets/d/1-BiIZ1XdbtjKw4QbfMWCo23mSzuCdBroY5F4HMrTPRk/edit?gid=0#gid=0) для того чтобы не делать уже выбранную кем то работу. После завершения и отправки на проверку залейте пожалуйста поле зеленым.
3. Текущая информация в базе данных:
   - `ru_meaning` — смысловой перевод (человеческая редакция).
   - `ru_meaning_lit` — дословный перевод (человеческая редакция).
   - `ru_meaning_raw` — машинный перевод.
4. Вносите изменения в следующие колонки:
   - **`corrections_ru_meaning`** — если исправляете или вносите заново `ru_meaning`.
   - **`corrections_ru_meaning_lit`** — если исправляете или вносите заново `ru_meaning_lit`.
5. Используйте колонку `notes` для заметок к редактору либо если предлагаете заметки для публикации в словаре в графе `Заметки`.

---

## 3. Основные принципы перевода

### Общие рекомендации
1. **Лаконичность.** Держите переводы краткими, чтобы словарь оставался легким для восприятия.
2. **Максимум три синонима.** Старайтесь ограничиваться тремя синонимами (четыре допустимы только для уточнения смыслов).
3. **Разнообразие.** Не повторяйте одинаковые слова в синонимах. Например:  
   - Вместо *«хорошо сделанный; хорошо изготовленный»* — *«хорошо сделанный; искусно изготовленный»*.
   - Вместо *«имеющий хорошие причины; имеющий доказательства; имеющий свидетельства»* — *«имеющий хорошие причины; подкреплённый доказательствами; со свидетельствами»*
   - Вместо *«следует обмануть; следует ввести в заблуждение; может обмануть; может ввести в заблуждение; может надуть»* — *«следует обмануть; может ввести в заблуждение; может надуть»*

### Особенности перевода
- **Дословный и смысловой перевод.**  
  Не дублируйте дословный перевод в колонке смыслового, старайтесь подобрать синоним. 

- **Части речи.**  
  Ознакомьтесь с форматами существующих слов для конкретной части речи, читая сокращение в русской части словаря (пройдя к соответсвующей статье):  
  - **ger** — действие в процессе (например: *делая, удаляя*), либо завершенное действие (в зависимости от контекста)  
  - **abs** — завершенное действие (например: *сделав, покинув*).  
  - **caus** — побудительное значение (*побуждая, побуждённый*).  
  и т.д.

- **Род.**  
  По умолчанию прилагательные и причастия переводятся в мужском роде, если не указано иное.  

- **Пассивный смысл.**  
  Обратите внимание на пассивные значения слов, особенно имеющих часть речи `pp`.
  - Вместо: *«исправленный; признавшийся в ошибках; признавшийся в проступках»*. в контексте чаще это слово имеет именно пассивное значение и относится к объекту *«(проступок) исправленный; в котором признался»*.  

---

## 4. Примеры переводов

### Существительные
- **masc:** *костер, помощник, проступок, владыка*.  
- **fem:** *неприязнь, жалость, работа, женщина*.  
- **nt:** *делание, состояние, слово, наставление*.  

### Глаголы
- **pr:** *живет, смотрит, выходит, является*.  
- **aor** *делал, сказал, шел, бродил, вырезал*
- **opt** *следует сделать; должен совершить; может выполнить; мог бы исполнить*
- **fut** *будет, объясит, сделает, разрушит, поймет*
- **inf** *добиваться, продолжать, защищать, объяснять*

### Причастия
- **pp:** *созданный, достигнутый, запятнанный*.  
- **ptp:** *должен быть сделанным; подлежит совершению; выполнимый; досл. к исполнению*.  
- **prp**	*обучаемый, волнующийся, подвергаемый, (либо) принимая, зная, вращая, давая* (в зависимости от контекста)

### Деепричастия
- **ger:** *понимая, избегая, приближаясь*.  
- **abs:** *спросив, сделав, поднявшись, преодолев*.  

### Другие категории
- **ind:** *скоро, сейчас, внутри, дольше*.  
- **ordin:** *восьмой (8ой), тринадцатый (13ый)*. 
- **card** *тридцать (30), девять (9), четыре (4), сорок (40)*.
- **adj**	*свободный, плохой, мягкий*



---

## 5. Особые случаи перевода

### Абстрактные существительные
- Для слов `abstr`, избегайте использования слова *состояние* в смысловом переводе.  
  Например: *состояние тревоги* → *тревожность*. Слово *состояние* лучше упомянать лишь в дословном переводе.

### Сложные фразы
- Упрощайте вспомогательные конструкции:  
    - Вместо: *«не заставленный делать кем-либо; не побуждённый делать кем-либо»*. — *«не заставленный делать; не побуждённый делать (кем-либо)»*.  

    - Вместе: *«делается кем-то или чем-то; практикуется кем-то»*. — *«делается; практикуется (кем-то)»*.

- Если перевод невозможен одним словом:  
  - Для существительных рекомендуется использование вспомогательных слов чтобы подчеркнуть что это именно существительное а не прилагательное или причастие: *«что-то, что следует сделать»*.  
  - Для прилагательных и причастий: *«следует сделать»*.  

---

Этот формат поможет вам эффективно редактировать переводы, соблюдая единообразие и качество словаря. 