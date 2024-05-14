function makeFamilyIdioms(data) {
    const familyIdiomList = data.family_idioms
    const lemma = data.lemma
    var html = "";

    //// header

    if (familyIdiomList.length > 1) {
        html += `<p class="heading" id="${lemma}_idiom_top">jump to: `; 
        familyIdiomList.forEach(item => {
            item = item.replace(/ /g, "_")
            html += `<a class="jump" href="#${lemma}_idiom_${item}">${item}</a> `;
        });
        html += `</p>`;
    };

    familyIdiomList.forEach(item => {
        fi = family_idiom_json[item]
        item = item.replace(/ /g, "_")

        if (familyIdiomList.length > 1) {
            html += `<p class="heading underlined overlined" `
            html += `id=${lemma}_idiom_${item}>`;
            html += `<b>${fi.count}</b> idiomatic expression which contains <b>${superScripter(item)}</b>`;
            html += `<a class="jump" href="#${lemma}_idiom_top"> ⤴</a></p>`;
        } else if (familyIdiomList.length == 1) {
            html += `<p class="heading underlined" `
            html += `id=${lemma}_idiom_top>`;
            html += `<b>${fi.count}</b> idiomatic expression which contains <b>${superScripter(item)}</b>`;
        };
        
        //// table

        html += `<table class="family"><tbody>`;
        fi.data.forEach(data => {
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
        <p class="footer">
        Please add more idioms  
        <a class="link" 
        href="https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&amp;entry.438735500=${lemma}&amp;entry.326955045=Idioms&amp;entry.1433863141=GoldenDict+${data.date}" 
        target="_blank">
        here</a>.`; 
    
    html += `<a class="jump" href="#${lemma}_idiom_top"> ⤴</a></p>`

    return html
}
