function makeFeedback_ru(data) {
    
    const lemmaLink = data.lemma.replace(/ /g, "%20")

    const html = `
    ID <b>${data.id}</b>
    <p>
        Это образовательный проект и находится на стадии тестирования и редактирования.
        <br>
        Словарь является частичным переводом <a class="link_ru" href="https://digitalpalidictionary.github.io/">DPD</a> - <b>Электронный Словарь Пали (от Дост. Бодхираса).</b>
        <br>
        <b>Помощь.</b> Чтобы увидеть подробное описание пожалуйста кликните на любое заглавие или сокращение.
        
        Список литературы можно увидеть в статье <b>литература</b>.
    </p>
    <p>
        <a class="link" 
        href="https://docs.google.com/forms/d/e/1FAIpQLSfResxEUiRCyFITWPkzoQ2HhHEvUS5fyg68Rl28hFH6vhHlaA/viewform?usp=pp_url&amp;entry.1433863141=${progName}+${data.date}"
        target="_blank">Добавить отсутствующее слово</a>
        <span>
            . Пожалуйста, используйте эту 
        </span>
        <a class="link_ru" 
        href="https://docs.google.com/forms/d/e/1FAIpQLSfResxEUiRCyFITWPkzoQ2HhHEvUS5fyg68Rl28hFH6vhHlaA/viewform?usp=pp_url&entry.1433863141=${progName}+${data.date}"
        target="_blank">онлайн-форму</a> для добавления отсутствующих слов, особенно из Винаи, комментариев и других поздних текстов. Если вы предпочитаете работать в автономном режиме, вот 
        <a class="link" download="true" 
        href="https://github.com/digitalpalidictionary/dpd-db/raw/main/misc/DPD%20Add%20Words.xlsx" 
        target="_blank">таблица для загрузки</a>
        <span>
            , заполните и отправьте. 
        </span>
    </p>
    <p>
        Заметили ошибку? <a class="link_ru" href="https://docs.google.com/forms/d/1iMD9sCSWFfJAFCFYuG9HRIyrr9KFRy0nAOVApM998wM/viewform?usp=pp_url&entry.438735500=${lemmaLink}&entry.326955045=Грамматика&entry.1433863141=${progName}+${data.date}" target="_blank">Исправьте здесь</a>.
        <span>
            Ваши предложения и комментарии будут неоценимой помощью в улучшении качества данной работы и будут полезны всем пользователям словаря. 
        </span>
    </p>
    <p>
        <span>Ваша версия словаря от <b>${data.date}</b>. Пожалуйста, регулярно проверяйте наличие обновлений.</span>
    </p>
    <p>
        <a class="link_ru" href="https://digitalpalidictionary.github.io/rus/">Веб страница</a>.
        <span>
            Можно найти свежую версию словаря; узнать больше о функциях, как установить и настроить.
        </span>
    </p>
    <p>
        <a class="link_ru" href="mailto:devamitta@sasanarakkha.org">Помощь проекту</a><span>. Если вы программист или хорошо знаете Пали или как-то хотите поддержать проект, помощь приветствуется!</span>
    </p>
    <p>
        При поддержке <a class="link_ru" href="https://sasanarakkha.org/">Sāsanārakkha Buddhist Sanctuary</a>.
    </p>
    `
    return html
}

    
