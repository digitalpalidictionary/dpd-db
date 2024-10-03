function makeFamilyCompoundHtml_ru(data) {
    const familyCompoundList = data.family_compounds
    const lemmaTag = data.lemma.replace(/ /g, "_")
    const lemmaLink = data.lemma.replace(/ /g, "%20")
    var html = "";

    //// header

    if (familyCompoundList.length > 1) {
        html += `<p class="heading" id="${lemmaTag}_cf_top">перейти к: `; 
        familyCompoundList.forEach(item => {
            itemTag = item.replace(/ /g, "_")
            html += `<a class="jump_ru" href="#${lemmaTag}_cf_${itemTag}">${item}</a> `;
        });
        html += `</p>`;
    };

    familyCompoundList.forEach(item => {
        fc = ru_family_compound_json[item]
        itemTag = item.replace(/ /g, "_")

        if (familyCompoundList.length > 1) {
            html += `<p class="heading underlined_ru overlined_ru" `
            html += `id=${lemmaTag}_cf_${itemTag}>`;
            html += `<b>${fc.count}</b> составных слов(а) содержат `;
            html += `<b>${superScripter(item)}</b>`;
            html += `<a class="jump_ru" href="#${lemmaTag}_cf_top"> ⤴</a></p>`;
        } else if (familyCompoundList.length == 1) {
            html += `<p class="heading underlined_ru" `
            html += `id=${lemmaTag}_cf_top>`;
            html += `<b>${fc.count}</b> составное слово содержащее `;
            html += `<b>${superScripter(item)}</b>`;
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
        <a class="link_ru" 
        href="https://docs.google.com/forms/d/1iMD9sCSWFfJAFCFYuG9HRIyrr9KFRy0nAOVApM998wM/viewform?usp=pp_url&amp;entry.438735500=${lemmaLink}&amp;entry.326955045Семья+составных&amp;entry.1433863141=GoldenDict+${data.date}" 
        target="_blank">
        Пожалуйста, сообщите об ошибке</a>.`; 
    
    html += `<a class="jump_ru" href="#${lemmaTag}_cf_top"> ⤴</a></p>`

    return html
}
