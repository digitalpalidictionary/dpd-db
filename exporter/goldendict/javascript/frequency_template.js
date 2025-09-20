function makeFrequency(data) {
  const lemmaLink = data.lemma.replace(/ /g, "%20");
  var html = `
<p class="heading underlined">
        ${data.FreqHeading}
    </p>
`;

  if (data.CstFreq[0] != undefined) {
    html += `
<table class="freq">
    <thead>
        <tr>
            <th></th>
            <th></th>
            <th colspan="3" title="Chaṭṭha Saṅgāyana Tipiṭaka (Myanmar)">
                <b>
                    CST
                </b>
            </th>
            <th></th>
            <th colspan="2" title="Buddha Jayanti Tipiṭaka (Sri Lanka)">
                <b>
                    BJT
                </b>
            </th>
            <th></th>
            <th colspan="2" title="Syāmaraṭṭha 1927 Royal Edition (Thailand)">
                <b>
                    SYA
                </b>
            </th>
            <th></th>
            <th colspan="1" title="Mahāsaṅgīti Tipiṭaka (Sutta Central)">
                <b>
                    MST
                </b>
            </th>
        </tr>
        <tr style="text-align: right;">
            <th></th>
            <th></th>
            <!-- CST -->
            <th title="mūla">M</th>
            <th title="aṭṭhakathā">A</th>
            <th title="ṭīkā">Ṭ</th>
            <th></th>
            <!-- BJT -->
            <th title="mūla">M</th>
            <th title="aṭṭhakathā">A</th>
            <th></th>
            <!-- SYA -->
            <th title="mūla">M</th>
            <th title="aṭṭhakathā">A</th>
            <th></th>
            <!-- SC -->
            <th title="mūla">M</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <th class="vertical-text" rowspan="6">Vinaya</th>
        </tr>
        <tr>
            <th>Pārājika</th>
            <!-- CST -->
            <td class="gr${data.CstGrad[0]}">${data.CstFreq[0]}</td>
            <td class="gr${data.CstGrad[19]}">${data.CstFreq[19]}</td>
            <td class="gr${data.CstGrad[33]}" rowspan="5">${data.CstFreq[33]}</td>
            <td class="gap"></td>
            <!-- BJT -->
            <td class="gr${data.BjtGrad[0]}">${data.BjtFreq[0]}</td>
            <td class="gr${data.BjtGrad[19]}">${data.BjtFreq[19]}</td>
            <td class="gap"></td>
            <!-- SYA -->
            <td class="gr${data.SyaGrad[0]}" rowspan="2">${data.SyaFreq[0]}</td>
            <td class="gr${data.SyaGrad[17]}" rowspan="5">${data.SyaFreq[17]}</td>
            <td class="gap"></td>
            <!-- SC -->
            <td class="gr${data.ScGrad[0]}">${data.ScFreq[0]}</td>
        </tr>
        <tr>
            <th>Pācittiya</th>
            <!-- CST -->
            <td class="gr${data.CstGrad[1]}">${data.CstFreq[1]}</td>
            <td class="gr${data.CstGrad[20]}">${data.CstFreq[20]}</td>
            <td class="gap"></td>
            <!-- BJT -->
            <td class="gr${data.BjtGrad[1]}">${data.BjtFreq[1]}</td>
            <td class="gr${data.BjtGrad[20]}">${data.BjtFreq[20]}</td>
            <td class="gap"></td>
            <!-- SYA -->
            <td class="gap"></td>
            <!-- SC -->
            <td class="gr${data.ScGrad[1]}">${data.ScFreq[1]}</td>
        </tr>
        <tr>
            <th>Mahāvagga</th>
            <!-- CST -->
            <td class="gr${data.CstGrad[2]}">${data.CstFreq[2]}</td>
            <td class="gr${data.CstGrad[21]}">${data.CstFreq[21]}</td>
            <td class="gap"></td>
            <!-- BJT -->
            <td class="gr${data.BjtGrad[2]}">${data.BjtFreq[2]}</td>
            <td class="gr${data.BjtGrad[21]}">${data.BjtFreq[21]}</td>
            <td class="gap"></td>
            <!-- SYA -->
            <td class="gr${data.SyaGrad[1]}">${data.SyaFreq[1]}</td>
            <td class="gap"></td>
            <!-- SC -->
            <td class="gr${data.ScGrad[2]}">${data.ScFreq[2]}</td>
        </tr>
        <tr>
            <th>Cūḷavagga</th>
            <!-- CST -->
            <td class="gr${data.CstGrad[3]}">${data.CstFreq[3]}</td>
            <td class="gr${data.CstGrad[22]}">${data.CstFreq[22]}</td>
            <td class="gap"></td>
            <!-- BJT -->
            <td class="gr${data.BjtGrad[3]}">${data.BjtFreq[3]}</td>
            <td class="gr${data.BjtGrad[22]}">${data.BjtFreq[22]}</td>
            <td class="gap"></td>
            <!-- SYA -->
            <td class="gr${data.SyaGrad[2]}">${data.SyaFreq[2]}</td>
            <td class="gap"></td>
            <!-- SC -->
            <td class="gr${data.ScGrad[3]}">${data.ScFreq[3]}</td>
        </tr>
        <tr>
            <th>Parivāra</th>
            <!-- CST -->
            <td class="gr${data.CstGrad[4]}">${data.CstFreq[4]}</td>
            <td class="gr${data.CstGrad[23]}">${data.CstFreq[23]}</td>
            <td class="gap"></td>
            <!-- BJT -->
            <td class="gr${data.BjtGrad[4]}">${data.BjtFreq[4]}</td>
            <td class="gr${data.BjtGrad[23]}">${data.BjtFreq[23]}</td>
            <td class="gap"></td>
            <!-- SYA -->
            <td class="gr${data.SyaGrad[3]}">${data.SyaFreq[3]}</td>
            <td class="gap"></td>
            <!-- SC -->
            <td class="gr${data.ScGrad[4]}">${data.ScFreq[4]}</td>
        </tr>
        <tr>
            <th class="vertical-text" rowspan="8">Sutta</th>
        </tr>
        <tr>
            <th>Dīgha</th>
            <!-- CST -->
            <td class="gr${data.CstGrad[5]}">${data.CstFreq[5]}</td>
            <td class="gr${data.CstGrad[24]}">${data.CstFreq[24]}</td>
            <td class="gr${data.CstGrad[34]}">${data.CstFreq[34]}</td>
            <td class="gap"></td>
            <!-- BJT -->
            <td class="gr${data.BjtGrad[5]}">${data.BjtFreq[5]}</td>
            <td class="gr${data.BjtGrad[24]}">${data.BjtFreq[24]}</td>
            <td class="gap"></td>
            <!-- SYA -->
            <td class="gr${data.SyaGrad[4]}">${data.SyaFreq[4]}</td>
            <td class="gr${data.SyaGrad[18]}">${data.SyaFreq[18]}</td>
            <td class="gap"></td>
            <!-- SC -->
            <td class="gr${data.ScGrad[5]}">${data.ScFreq[5]}</td>
        </tr>
        <tr>
            <th>Majjhima</th>
            <!-- CST -->
            <td class="gr${data.CstGrad[6]}">${data.CstFreq[6]}</td>
            <td class="gr${data.CstGrad[25]}">${data.CstFreq[25]}</td>
            <td class="gr${data.CstGrad[35]}">${data.CstFreq[35]}</td>
            <td class="gap"></td>
            <!-- BJT -->
            <td class="gr${data.BjtGrad[6]}">${data.BjtFreq[6]}</td>
            <td class="gr${data.BjtGrad[25]}">${data.BjtFreq[25]}</td>
            <td class="gap"></td>
            <!-- SYA -->
            <td class="gr${data.SyaGrad[5]}">${data.SyaFreq[5]}</td>
            <td class="gr${data.SyaGrad[19]}">${data.SyaFreq[19]}</td>
            <td class="gap"></td>
            <!-- SC -->
            <td class="gr${data.ScGrad[6]}">${data.ScFreq[6]}</td>
        </tr>
        <tr>
            <th>Saṃyutta</th>
            <!-- CST -->
            <td class="gr${data.CstGrad[7]}">${data.CstFreq[7]}</td>
            <td class="gr${data.CstGrad[26]}">${data.CstFreq[26]}</td>
            <td class="gr${data.CstGrad[36]}">${data.CstFreq[36]}</td>
            <td class="gap"></td>
            <!-- BJT -->
            <td class="gr${data.BjtGrad[7]}">${data.BjtFreq[7]}</td>
            <td class="gr${data.BjtGrad[26]}">${data.BjtFreq[26]}</td>
            <td class="gap"></td>
            <!-- SYA -->
            <td class="gr${data.SyaGrad[6]}">${data.SyaFreq[6]}</td>
            <td class="gr${data.SyaGrad[20]}">${data.SyaFreq[20]}</td>
            <td class="gap"></td>
            <!-- SC -->
            <td class="gr${data.ScGrad[7]}">${data.ScFreq[7]}</td>
        </tr>
        <tr>
            <th>Aṅguttara</th>
            <!-- CST -->
            <td class="gr${data.CstGrad[8]}">${data.CstFreq[8]}</td>
            <td class="gr${data.CstGrad[27]}">${data.CstFreq[27]}</td>
            <td class="gr${data.CstGrad[37]}">${data.CstFreq[37]}</td>
            <td class="gap"></td>
            <!-- BJT -->
            <td class="gr${data.BjtGrad[8]}">${data.BjtFreq[8]}</td>
            <td class="gr${data.BjtGrad[27]}">${data.BjtFreq[27]}</td>
            <td class="gap"></td>
            <!-- SYA -->
            <td class="gr${data.SyaGrad[7]}">${data.SyaFreq[7]}</td>
            <td class="gr${data.SyaGrad[21]}">${data.SyaFreq[21]}</td>
            <td class="gap"></td>
            <!-- SC -->
            <td class="gr${data.ScGrad[8]}">${data.ScFreq[8]}</td>
        </tr>
        <tr>
            <th>Khuddaka 1</th>
            <!-- CST -->
            <td class="gr${data.CstGrad[9]}">${data.CstFreq[9]}</td>
            <td class="gr${data.CstGrad[28]}">${data.CstFreq[28]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <!-- BJT -->
            <td class="gr${data.BjtGrad[9]}">${data.BjtFreq[9]}</td>
            <td class="gr${data.BjtGrad[28]}">${data.BjtFreq[28]}</td>
            <td class="gap"></td>
            <!-- SYA -->
            <td class="gr${data.SyaGrad[8]}">${data.SyaFreq[8]}</td>
            <td class="gr${data.SyaGrad[22]}">${data.SyaFreq[22]}</td>
            <td class="gap"></td>
            <!-- SC -->
            <td class="gr${data.ScGrad[9]}">${data.ScFreq[9]}</td>
        </tr>
        <tr>
            <th>Khuddaka 2</th>
            <!-- CST -->
            <td class="gr${data.CstGrad[10]}">${data.CstFreq[10]}</td>
            <td class="gr${data.CstGrad[29]}">${data.CstFreq[29]}</td>
            <td class="void"></td>
            <td class="gap"></td>
            <!-- BJT -->
            <td class="gr${data.BjtGrad[10]}">${data.BjtFreq[10]}</td>
            <td class="gr${data.BjtGrad[29]}">${data.BjtFreq[29]}</td>
            <td class="gap"></td>
            <!-- SYA -->
            <td class="gr${data.SyaGrad[9]}">${data.SyaFreq[9]}</td>
            <td class="gr${data.SyaGrad[23]}">${data.SyaFreq[23]}</td>
            <td class="gap"></td>
            <!-- SC -->
            <td class="gr${data.ScGrad[10]}">${data.ScFreq[10]}</td>
        </tr>
        <tr>
            <th>Khuddaka 3</th>
            <!-- CST -->
            <td class="gr${data.CstGrad[11]}">${data.CstFreq[11]}</td>
            <td class="gr${data.CstGrad[30]}">${data.CstFreq[30]}</td>
            <td class="gr${data.CstGrad[38]}">${data.CstFreq[38]}</td>
            <td class="gap"></td>
            <!-- BJT -->
            <td class="gr${data.BjtGrad[11]}">${data.BjtFreq[11]}</td>
            <td class="gr${data.BjtGrad[30]}">${data.BjtFreq[30]}</td>
            <td class="gap"></td>
            <!-- SYA -->
            <td class="gr${data.SyaGrad[10]}">${data.SyaFreq[10]}</td>
            <td class="gr${data.SyaGrad[24]}">${data.SyaFreq[24]}</td>
            <td class="gap"></td>
            <!-- SC -->
            <td class="gr${data.ScGrad[11]}">${data.ScFreq[11]}</td>
        </tr>
        <tr>
            <th class="vertical-text" rowspan="8">Abhidhamma</th>
        </tr>
        <tr>
            <th>Dhammasaṅgaṇī</th>
            <!-- CST -->
            <td class="gr${data.CstGrad[12]}">${data.CstFreq[12]}</td>
            <td class="gr${data.CstGrad[31]}" rowspan="7">${data.CstFreq[31]}</td>
            <td class="gr${data.CstGrad[39]}" rowspan="7">${data.CstFreq[39]}</td>
            <td class="gap"></td>
            <!-- BJT -->
            <td class="gr${data.BjtGrad[12]}">${data.BjtFreq[12]}</td>
            <td class="gr${data.BjtGrad[31]}">${data.BjtFreq[31]}</td>
            <td class="gap"></td>
            <!-- SYA -->
            <td class="gr${data.SyaGrad[11]}">${data.SyaFreq[11]}</td>
            <td class="gr${data.SyaGrad[25]}" rowspan="7">${data.SyaFreq[25]}</td>
            <td class="gap"></td>
            <!-- SC -->
            <td class="gr${data.ScGrad[12]}">${data.ScFreq[12]}</td>
        </tr>
        <tr>
            <th>Vibhaṅga</th>
            <!-- CST -->
            <td class="gr${data.CstGrad[13]}">${data.CstFreq[13]}</td>
            <td class="gap"></td>
            <!-- BJT -->
            <td class="gr${data.BjtGrad[13]}">${data.BjtFreq[13]}</td>
            <td class="gr${data.BjtGrad[32]}">${data.BjtFreq[32]}</td>
            <td class="gap"></td>
            <!-- SYA -->
            <td class="gr${data.SyaGrad[12]}">${data.SyaFreq[12]}</td>
            <td class="gap"></td>
            <!-- SC -->
            <td class="gr${data.ScGrad[13]}">${data.ScFreq[13]}</td>
        </tr>
        <tr>
            <th>Dhātukathā</th>
            <!-- CST -->
            <td class="gr${data.CstGrad[14]}">${data.CstFreq[14]}</td>
            <td class="gap"></td>
            <!-- BJT -->
            <td class="gr${data.BjtGrad[14]}">${data.BjtFreq[14]}</td>
            <td class="gr${data.BjtGrad[33]}">${data.BjtFreq[33]}</td>
            <td class="gap"></td>
            <!-- SYA -->
            <td class="gr${data.SyaGrad[13]}" rowspan="2">${data.SyaFreq[13]}</td>
            <td class="gap"></td>
            <!-- SC -->
            <td class="gr${data.ScGrad[14]}">${data.ScFreq[14]}</td>
        </tr>
        <tr>
            <th>Puggalapaññatti</th>
            <!-- CST -->
            <td class="gr${data.CstGrad[15]}">${data.CstFreq[15]}</td>
            <td class="gap"></td>
            <!-- BJT -->
            <td class="gr${data.BjtGrad[15]}">${data.BjtFreq[15]}</td>
            <td class="gr${data.BjtGrad[34]}">${data.BjtFreq[34]}</td>
            <td class="gap"></td>
            <!-- SYA -->
            <!-- included in Dhātukathā -->
            <td class="gap"></td>
            <!-- SC -->
            <td class="gr${data.ScGrad[15]}">${data.ScFreq[15]}</td>
        </tr>
        <tr>
            <th>Kathāvatthu</th>
            <!-- CST -->
            <td class="gr${data.CstGrad[16]}">${data.CstFreq[16]}</td>
            <td class="gap"></td>
            <!-- BJT -->
            <td class="gr${data.BjtGrad[16]}">${data.BjtFreq[16]}</td>
            <td class="gr${data.BjtGrad[35]}">${data.BjtFreq[35]}</td>
            <td class="gap"></td>
            <!-- SYA -->
            <td class="gr${data.SyaGrad[14]}">${data.SyaFreq[14]}</td>
            <td class="gap"></td>
            <!-- SC -->
            <td class="gr${data.ScGrad[16]}">${data.ScFreq[16]}</td>
        </tr>
        <tr>
            <th>Yamaka</th>
            <!-- CST -->
            <td class="gr${data.CstGrad[17]}">${data.CstFreq[17]}</td>
            <td class="gap"></td>
            <!-- BJT -->
            <td class="gr${data.BjtGrad[17]}">${data.BjtFreq[17]}</td>
            <td class="gr${data.BjtGrad[36]}">${data.BjtFreq[36]}</td>
            <td class="gap"></td>
            <!-- SYA -->
            <td class="gr${data.SyaGrad[15]}">${data.SyaFreq[15]}</td>
            <td class="gap"></td>
            <!-- SC -->
            <td class="gr${data.ScGrad[17]}">${data.ScFreq[17]}</td>
        </tr>
        <tr>
            <th>Paṭṭhāna</th>
            <!-- CST -->
            <td class="gr${data.CstGrad[18]}">${data.CstFreq[18]}</td>
            <td class="gap"></td>
            <!-- BJT -->
            <td class="gr${data.BjtGrad[18]}">${data.BjtFreq[18]}</td>
            <td class="gr${data.BjtGrad[37]}">${data.BjtFreq[37]}</td>
            <td class="gap"></td>
            <!-- SYA -->
            <td class="gr${data.SyaGrad[16]}">${data.SyaFreq[16]}</td>
            <td class="gap"></td>
            <!-- SC -->
            <td class="gr${data.ScGrad[18]}">${data.ScFreq[18]}</td>
        </tr>
        <tr>
            <th class="vertical-text" rowspan="10">Aññā</th>
        </tr>
        <tr>
            <th>Visuddhimagga</th>
            <!-- CST -->
            <td class="void"></td>
            <td class="gr${data.CstGrad[32]}">${data.CstFreq[32]}</td>
            <td class="gr${data.CstGrad[40]}">${data.CstFreq[40]}</td>
            <td class="gap"></td>
            <!-- BJT -->
            <td class="void"></td>
            <td class="gr${data.BjtGrad[38]}">${data.BjtFreq[38]}</td>
            <td class="gap"></td>
            <!-- SYA -->
            <td class="void"></td>
            <td class="gr${data.SyaGrad[26]}">${data.SyaFreq[26]}</td>
            <td class="gap"></td>
            <!-- SC -->
            <td class="void"></td>
        </tr>
        <tr>
            <th>Leḍī Sayāḍo</th>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gr${data.CstGrad[41]}">${data.CstFreq[41]}</td>
        </tr>
        <tr>
            <th>Buddhavandanā</th>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gr${data.CstGrad[42]}">${data.CstFreq[42]}</td>
        </tr>
        <tr>
            <th>Vaṃsa</th>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gr${data.CstGrad[43]}">${data.CstFreq[43]}</td>
        </tr>
        <tr>
            <th>Byākaraṇa</th>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gr${data.CstGrad[44]}">${data.CstFreq[44]}</td>
        </tr>
        <tr>
            <th>Pucchavissajjanā</th>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gr${data.CstGrad[45]}">${data.CstFreq[45]}</td>
        </tr>
        <tr>
            <th>Nīti</th>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gr${data.CstGrad[46]}">${data.CstFreq[46]}</td>
        </tr>
        <tr>
            <th>Pakiṇṇaka</th>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gr${data.CstGrad[47]}">${data.CstFreq[47]}</td>
        </tr>
        <tr>
            <th>Sihaḷa</th>
            <td class="void"></td>
            <td class="void"></td>
            <td class="gr${data.CstGrad[48]}">${data.CstFreq[48]}</td>
        </tr>
    </tbody>
</table>
<p>
    <b>CST</b>: Chaṭṭha Saṅgāyana Tipiṭaka (Myanmar)
</p>
<p>
    <b>BJT</b>: Buddha Jayanti Tipiṭaka (Sri Lanka)
</p>
<p>
    <b>SYA</b>: Syāmaraṭṭha 1927 Royal Edition (Thailand)
</p>
<p>
    <b>MST</b>: Mahāsaṅgīti Tipiṭaka (Sutta Central)
</p>
`;
  } else {
    html += `
<p>
    It probably only occurs in compounds. Or perhaps there is an error.
</p>
`;
  }
  html += `
<p>
    For a detailed explanation of how this word frequency chart is calculated, it's accuracies and inaccuracies,
    please refer to <a class="link" href="https://digitalpalidictionary.github.io/features/frequency/">this webpage</a>.
</p>
<p class='footer'>
    If something looks out of place, <a class="link"
        href="https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&entry.438735500=${
          data.id
        }%20${data.lemma.replace(
    / /g,
    "%20"
  )}&entry.326955045=Frequency&entry.1433863141=GoldenDict+${data.date}"
        target="_blank">log it here.</a>
</p>
`;
  return html;
}
