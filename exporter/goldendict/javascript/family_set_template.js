function makeFamilySets(data) {
    const familySetList = data.family_sets
    const lemma = data.lemma
    var html = "";

    //// header

    if (familySetList.length > 1) {
        html += `<p class="heading" id="${lemma}_set_top">jump to: `; 
        familySetList.forEach(item => {
            item = item.replace(/ /g, "_")
            html += `<a class="jump" href="#${lemma}_set_${item}">${item}</a> `;
        });
        html += `</p>`;
    };

    familySetList.forEach(item => {
        fc = family_set_json[item]
        item = item.replace(/ /g, "_")

        if (familySetList.length > 1) {
            html += `<p class="heading underlined overlined" `
            html += `id=${lemma}_set_${item}>`;
            html += `<b>${lemma}</b> belongs to the set of <b>${item}</b>`;
            html += `<a class="jump" href="#${lemma}_set_top"> ⤴</a></p>`;
        } else if (familySetList.length == 1) {
            html += `<p class="heading underlined" `
            html += `id=${lemma}_set_top>`;
            html += `<b>${lemma}</b> belongs to the set of <b>${item}</b>`;
        };
        
        //// table

        html += `<table class="family"><tbody>`;
        fc.data.forEach(data => {
            html += `
                <tr>
                <th>${data[0]}</th>
                <td><b>${data[1]}</b></td>
                <td>${data[2]}</td>
                <td><span class="gray">${data[3]}</span</td>
                </tr>`;
        });

        html += `</tbody></table>`;
    });

    //// footer

    html += `
        <p class="footer">
        Spot a mistake? 
        <a class="link" 
        href="https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&amp;entry.438735500=${lemma}&amp;entry.326955045=set+Family&amp;entry.1433863141=GoldenDict+${data.date}" 
        target="_blank">
        Fix it here</a>.`; 
    
    html += `<a class="jump" href="#${lemma}_set_top"> ⤴</a></p>`

    return html
}
