function makeFeedback(data) {
  const lemmaLink = data.lemma.replace(/ /g, "%20");

  const html = `
    ID <b>${data.id}</b>
    <p>Digital Pāḷi Dictionary is a work in progress, made available for testing and feedback purposes.</p>
    <p>
        <a class="link"
        href="https://docs.google.com/forms/d/e/1FAIpQLSfResxEUiRCyFITWPkzoQ2HhHEvUS5fyg68Rl28hFH6vhHlaA/viewform?usp=pp_url&entry.1433863141=${progName}+${
    data.date
  }"
        target="_blank">Add a missing word</a><span>. Please use this </span>
        <a class="link"
        href="https://docs.google.com/forms/d/e/1FAIpQLSfResxEUiRCyFITWPkzoQ2HhHEvUS5fyg68Rl28hFH6vhHlaA/viewform?usp=pp_url&entry.1433863141=${progName}+${
    data.date
  }"
        target="_blank">
        online form</a>
        to add missing words, especially from Vinaya, commentaries, and other later texts.
        If you prefer to work offline, here is a
        <a class="link" download="true"
        href="https://github.com/digitalpalidictionary/dpd-db/raw/main/misc/DPD%20Add%20Words.xlsx"
        target="_blank">
        spreadsheet to download</a><span>, fill in and submit. </span>
    </p>
    <p>
        <a class="link"
        href="https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&entry.438735500=${
          data.id
        }%20${data.lemma.replace(/ /g, "%20")}&entry.1433863141=${progName}+${
    data.date
  }"
        target="_blank">
        Correct a mistake</a><span>. Did you spot a mistake in the dictionary? Please report it. It generally takes less than a minute and your corrections and suggestions help to improve the quality of this dictionary for everyone who uses it.</span>
    </p>
    <p>
        <a class="link"
        href="https://github.com/digitalpalidictionary/dpd-db/releases">
        Get updated</a><span>. You are using <b>DPD ${progName}</b> updated on <b>${
    data.date
  }</b>. Check for an update every full moon uposatha day.</span>
    </p>
    <p>
        <a class="link"
        href="https://digitalpalidictionary.github.io/">
        Visit the DPD docs website</a><span>. Get more detailed information about installation and upgrades, advanced settings and features.</span>
    </p>
    <p>
        <a class="link"
        href="mailto:digitalpalidictionary@gmail.com?subject=I'd%20like%20to%20help%20with%20code!&body=Please%20let%20me%20know%20how%20I%20can%20get%20involved%20with%20the%20development%20of%20DPD.">
        Help with coding</a><span>. If you're a coder and would like to support the project, please get in touch.</span>
    </p>
    <p>
        <a class="link"
        href="mailto:digitalpalidictionary@gmail.com?subject=I%20want%20to%20help%20with%20DPD!&body=Please%20let%20me%20know%20how%20I%20can%20get%20involved%20with%20the%20development%20of%20DPD.">
        Help with Pāḷi</a><span>. If you have Pāḷi grammar skills and would like to assist, please make email contact.</span>
    </p>
    <p>
        <a class="link"
        href="mailto:digitalpalidictionary@gmail.com?subject=Keep%20me%20updated!&body=Please%20let%20me%20know%20about%20new%20features%20and%20updates%20as%20soon%20as%20they%20are%20available.">
        Join the mailing list</a><span>. Get notified of updates and new features as soon as they become available.</span>
    </p>
    `;
  return html;
}
