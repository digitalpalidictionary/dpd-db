
function makeFamilyWordHtml_ru(data) {

    fw = ru_family_word_json[data.family_word]
    const lemmaLink = data.lemma.replace(/ /g, "%20")

    //// header

    var html = `
        <p class="heading underlined_ru">
            <b>${fw.count}</b> 
            слов(а), которые принадлежат к семье 
            <b>${superScripter(data.family_word)}</b> 
        </p>
    `;

    //// table

    html += `<table class="family_ru"><tbody>`;

    fw.data.forEach(item => {
        html += `
            <tr>
            <th>${item[0]}</th>
            <td><b>${item[1]}</b></td>
            <td>${item[2]}</td>
            <td><span class="gray">${item[3]}</span</td>
            </tr>
        `;
    });

    html += `</tbody></table>`;

    //// footer

    html += `
        <p class="footer_ru">
        Что-то не на месте?
        <a class="link_ru" 
        href="https://docs.google.com/forms/d/1iMD9sCSWFfJAFCFYuG9HRIyrr9KFRy0nAOVApM998wM/viewform?usp=pp_url&amp;entry.438735500=${lemmaLink}&amp;entry.326955045=Семья+слова&amp;entry.1433863141=GoldenDict+${data.date}" 
        target="_blank">
        Пожалуйста сообщите
        </a>.
        </p>
    `;

    return html
}
