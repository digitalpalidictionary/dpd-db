
function makeFamilyRootHtml(data) {

    fr = family_root_json[data.family_root]

    //// header
    
    var html = `
        <p class="heading underlined">
            <b>${fr.count}</b> words belong to the root family 
            <b>${fr.root_family}</b> 
            (${fr.root_meaning})
        </p>
    `;

    //// table

    html += `
        <table class="family"><tbody>
    `;

    fr.data.forEach(item => {
        html += `
            <tr>
            <th>${item[0]}</th>
            <td><b>${item[1]}</b></td>
            <td>${item[2]}</td>
            <td><span class="gray">${item[3]}</span</td>
            </tr>
        `;
    });

    html += `
        </tbody>
        </table>
    `;

    //// footer

    html += `
        <p class="footer">
        Something out of place? 
        <a class="link" 
        href="https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&amp;entry.438735500=${data.lemma}&amp;entry.326955045=Root+Family&amp;entry.1433863141=GoldenDict+${data.date}" 
        target="_blank">
        Report it here
        </a>.
        </p>
    `;

    return html
}
