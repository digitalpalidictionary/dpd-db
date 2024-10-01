
function makeFamilyWordHtml(data) {

    fw = family_word_json[data.family_word]
    const lemmaLink = data.lemma.replace(/ /g, "%20")

    //// header

    var html = `
        <p class="heading underlined">
            <b>${fw.count}</b> 
            words belong to the 
            <b>${superScripter(data.family_word)}</b> 
            family
        </p>
    `;

    //// table

    html += `<table class="family"><tbody>`;

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
        <p class="footer">
        Something out of place? 
        <a class="link" 
        href="https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&amp;entry.438735500=${lemmaLink}&amp;entry.326955045=Word+Family&amp;entry.1433863141=GoldenDict+${data.date}" 
        target="_blank">
        Report it here
        </a>.
        </p>
    `;

    return html
}
