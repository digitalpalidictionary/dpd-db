function makeFamilyCompoundHtml(data) {
    const familyCompoundList = data.family_compounds
    const lemma = data.lemma
    var html = "";

    //// header

    if (familyCompoundList.length > 1) {
        html += `<p class="heading" id="${lemma}_cf_top">jump to: `; 
        familyCompoundList.forEach(item => {
            item = item.replace(/ /g, "_")
            html += `<a class="jump" href="#${lemma}_cf_${item}">${item}</a> `;
        });
        html += `</p>`;
    };

    familyCompoundList.forEach(item => {
        fc = family_compound_json[item]
        item = item.replace(/ /g, "_")

        if (familyCompoundList.length > 1) {
            html += `<p class="heading underlined overlined" `
            html += `id=${lemma}_cf_${item}>`;
            html += `<b>${fc.count}</b> compounds which contain `;
            html += `<b>${item}</b>`;
            html += `<a class="jump" href="#${lemma}_cf_top"> ⤴</a></p>`;
        } else if (familyCompoundList.length == 1) {
            html += `<p class="heading underlined" `
            html += `id=${lemma}_cf_top>`;
            html += `<b>${fc.count}</b> compound which contains `;
            html += `<b>${item}</b></p>`;
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
        href="https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&amp;entry.438735500=${lemma}&amp;entry.326955045=Compound+Family&amp;entry.1433863141=GoldenDict+${data.date}" 
        target="_blank">
        Fix it here</a>.`; 
    
    html += `<a class="jump" href="#${lemma}_cf_top"> ⤴</a></p>`

    return html
}
