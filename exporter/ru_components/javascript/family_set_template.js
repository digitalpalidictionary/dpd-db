function makeFamilySets(data) {
    const familySetList = data.family_sets
    const lemma = data.lemma
    var html = "";

    //// header

    if (familySetList.length > 1) {
        html += `<p class="heading" id="${lemma}_set_top_ru">перейти к: `; 
        familySetList.forEach(item => {
            item = item.replace(/ /g, "_")
            html += `<a class="jump_ru" href="#${lemma}_set_ru_${item}">${item}</a> `;
        });
        html += `</p>`;
    };

    familySetList.forEach(setName => {
        fc = family_set_json[setName]
        const set_link = setName.replace(/ /g, "_")

        if (familySetList.length > 1) {
            html += `<p class="heading underlined_ru overlined_ru" `
            html += `id=${lemma}_set_${set_link}>`;
            html += `<b>${lemma}</b> состоит в группе <b>${setName}</b>`;
            html += `<a class="jump_ru" href="#${lemma}_set_top"> ⤴</a></p>`;
        } else if (familySetList.length == 1) {
            html += `<p class="heading underlined_ru" `
            html += `id=${lemma}_set_top>`;
            html += `<b>${lemma}</b> состоит в группе <b>${setName}</b>`;
        };
        
        //// table

        html += `<table class="family_ru"><tbody>`;
        fc.data.forEach(data => {
            const [word, pos, meaning, complete] = data
            html += `
                <tr>
                <th>${word}</th>
                <td><b>${pos}</b></td>
                <td>${meaning}</td>
                <td><span class="gray">${complete}</span</td>
                </tr>`;
        });

        html += `</tbody></table>`;
    });

    //// footer

    html += `
        <p class="footer_ru">
        Заметили ошибку? Можете предложить новую группу? 
        <a class="link_ru" 
        href="https://docs.google.com/forms/d/1iMD9sCSWFfJAFCFYuG9HRIyrr9KFRy0nAOVApM998wM/viewform?usp=pp_url&amp;entry.438735500=${lemma}&amp;entry.326955045=Группа&amp;entry.1433863141=GoldenDict+${data.date}" 
        target="_blank">
        Опишите здесь</a>.`; 
    
    html += `<a class="jump_ru" href="#${lemma}_set_top"> ⤴</a></p>`

    return html
}
