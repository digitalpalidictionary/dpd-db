
function makeFamilyRootHtml(data, fr, source, link) {
    
    if (link == undefined) {
        const link = data.lemma.replace(" ", "%20")
    }

    //// header
    
    var html = `
        <p class="heading underlined">
            <b>${fr.count}</b> words belong to the root family 
            <b>${fr.root_family}</b> 
            (${fr.root_meaning})
        </p>
    `;

    //// table

    if (source == "root") {
        html += `<table class="root_family"><tbody>`;
    } else {
        html += `<table class="family"><tbody>`;
    }

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

    if (source == "root") {
        html += `
        <p class="footer">
        Something out of place? 
        <a class="root_link" 
        href="https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&amp;entry.438735500=${link}&amp;entry.326955045=Root+Family&amp;entry.1433863141=GoldenDict+${data.date}" 
        target="_blank">
        Report it here
        </a>.
        </p>
    `;
    } else {
        html += `
        <p class="footer">
        Something out of place? 
        <a class="link" 
        href="https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&amp;entry.438735500=${link}&amp;entry.326955045=Root+Family&amp;entry.1433863141=GoldenDict+${data.date}" 
        target="_blank">
        Report it here
        </a>.
        </p>
    `;
    }

    return html
}
