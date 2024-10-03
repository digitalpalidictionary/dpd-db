function makeFamilySets_ru(data) {
    const familySetList = data.family_sets
    const familySetLen = familySetList.length
    const lemma = data.lemma
    const lemmaTag = data.lemma.replace(/ /g, "_")
    const lemmaLink = data.lemma.replace(/ /g, "%20")
    var html = "";

    //// header

    if (familySetLen > 1) {
        html += `<p class="heading" id="${lemmaTag}_set_top_ru">перейти к: `; 
        familySetList.forEach(item => {
            itemLink = item.replace(/ /g, "_")
            html += `<a class="jump_ru" href="#${lemmaTag}_set_ru_${itemLink}">${item}</a>. `;
        });
        html += `</p>`;
    };

    familySetList.forEach(setName => {
        fc = ru_family_set_json[setName]
        const setTag = setName.replace(/ /g, "_")

        if (familySetList.length > 1) {
            html += `<p class="heading underlined_ru overlined_ru" `
            html += `id=${lemmaTag}_set_${setTag}>`;
            html += `<b>${lemma}</b> состоит в группе <b>${setName}</b>`;
            html += `<a class="jump_ru" href="#${lemmaTag}_set_top"> ⤴</a></p>`;
        } else if (familySetList.length == 1) {
            html += `<p class="heading underlined_ru" `
            html += `id=${lemmaTag}_set_top>`;
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
        href="https://docs.google.com/forms/d/1iMD9sCSWFfJAFCFYuG9HRIyrr9KFRy0nAOVApM998wM/viewform?usp=pp_url&amp;entry.438735500=${lemmaLink}&amp;entry.326955045=Группа&amp;entry.1433863141=GoldenDict+${data.date}" 
        target="_blank">
        Опишите здесь</a>.`; 
    
    html += `<a class="jump_ru" href="#${lemmaTag}_set_top"> ⤴</a></p>`

    return html
}
