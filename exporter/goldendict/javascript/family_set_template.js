function makeFamilySets(data) {
    const familySetList = data.family_sets
    const familySetLen = familySetList.length
    const lemma = data.lemma
    const lemmaTag = data.lemma.replace(/ /g, "_")
    const lemmaLink = data.lemma.replace(/ /g, "%20")
    var html = "";

    //// header

    if (familySetLen > 1) {
        html += `<p class="heading" id="${lemmaTag}_set_top">jump to: `; 
        familySetList.forEach(item => {
            itemLink = item.replace(/ /g, "_")
            html += `<a class="jump" href="#${lemmaTag}_set_${itemLink}">${item}</a>. `;
        });
        html += `</p>`;
    };

    familySetList.forEach(setName => {
        fc = family_set_json[setName]
        const setTag = setName.replace(/ /g, "_")

        if (familySetList.length > 1) {
            html += `<p class="heading underlined overlined" `
            html += `id=${lemmaTag}_set_${setTag}>`;
            html += `<b>${lemma}</b> belongs to the set of <b>${setName}</b>`;
            html += `<a class="jump" href="#${lemmaTag}_set_top"> ⤴</a></p>`;
        } else if (familySetList.length == 1) {
            html += `<p class="heading underlined" `
            html += `id=${lemmaTag}_set_top>`;
            html += `<b>${lemma}</b> belongs to the set of <b>${setName}</b>`;
        };
        
        //// table

        html += `<table class="family"><tbody>`;
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
        <p class="footer">
        Spot a mistake? 
        <a class="link" 
        href="https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&amp;entry.438735500=${lemmaLink}&amp;entry.326955045=set+Family&amp;entry.1433863141=GoldenDict+${data.date}" 
        target="_blank">
        Fix it here</a>.`; 
    
    html += `<a class="jump" href="#${lemmaTag}_set_top"> ⤴</a></p>`

    return html
}
