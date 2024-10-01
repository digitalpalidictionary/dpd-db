function makeFamilyCompoundHtml(data) {
    const familyCompoundList = data.family_compounds
    const lemmaTag = data.lemma.replace(/ /g, "_")
    const lemmaLink = data.lemma.replace(/ /g, "%20")
    var html = "";

    //// header

    if (familyCompoundList.length > 1) {
        html += `<p class="heading" id="${lemmaTag}_cf_top">jump to: `; 
        familyCompoundList.forEach(item => {
            itemTag = item.replace(/ /g, "_")
            html += `<a class="jump" href="#${lemmaTag}_cf_${itemTag}">${item}</a> `;
        });
        html += `</p>`;
    };

    familyCompoundList.forEach(item => {
        fc = family_compound_json[item]
        itemTag = item.replace(/ /g, "_")

        if (familyCompoundList.length > 1) {
            html += `<p class="heading underlined overlined" `
            html += `id=${lemmaTag}_cf_${itemTag}>`;
            html += `<b>${fc.count}</b> compounds which contain `;
            html += `<b>${superScripter(item)}</b>`;
            html += `<a class="jump" href="#${lemmaTag}_cf_top"> ⤴</a></p>`;
        } else if (familyCompoundList.length == 1) {
            html += `<p class="heading underlined" `
            html += `id=${lemmaTag}_cf_top>`;
            html += `<b>${fc.count}</b> compound which contains `;
            html += `<b>${superScripter(item)}</b>`;
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
        href="https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&amp;entry.438735500=${lemmaLink}&amp;entry.326955045=Compound+Family&amp;entry.1433863141=GoldenDict+${data.date}" 
        target="_blank">
        Fix it here</a>.`; 
    
    html += `<a class="jump" href="#${lemmaTag}_cf_top"> ⤴</a></p>`

    return html
}
