function makeFrequency(data) {
    const html = `
<div class="freq-table-container">
    <div class="freq-table-wrapper">
        <table class="freq">
            <thead>
                <tr style="text-align: right;">
                    <th colspan="2">
                        <b>
                            Chaṭṭha Saṅgāyana Tipiṭaka (Myanmar)
                        </b>
                    </th>
                    <th>M</th>
                    <th>A</th>
                    <th>Ṭ</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <th class="vertical-text" rowspan="6">Vinaya</th>
                </tr>
                <tr>
                    <th>Pārājika</th>
                    <td class="gr${data.CstGrad[0]}">${data.CstFreq[0]}</td>
                    <td class="gr${data.CstGrad[19]}">${data.CstFreq[19]}</td>
                    <td class="gr${data.CstGrad[33]}" rowspan="5">${data.CstFreq[33]}</td>
                </tr>
                <tr>
                    <th>Pācittiya</th>
                    <td class="gr${data.CstGrad[1]}">${data.CstFreq[1]}</td>
                    <td class="gr${data.CstGrad[20]}">${data.CstFreq[20]}</td>
                </tr>
                <tr>
                    <th>Mahāvagga</th>
                    <td class="gr${data.CstGrad[2]}">${data.CstFreq[2]}</td>
                    <td class="gr${data.CstGrad[21]}">${data.CstFreq[21]}</td>
                </tr>
                <tr>
                    <th>Cūḷavagga</th>
                    <td class="gr${data.CstGrad[3]}">${data.CstFreq[3]}</td>
                    <td class="gr${data.CstGrad[22]}">${data.CstFreq[22]}</td>
                </tr>
                <tr>
                    <th>Parivāra</th>
                    <td class="gr${data.CstGrad[4]}">${data.CstFreq[4]}</td>
                    <td class="gr${data.CstGrad[23]}">${data.CstFreq[23]}</td>
                </tr>
                <tr>
                    <th class="vertical-text" rowspan="8">Sutta</th>
                </tr>
                <tr>
                    <th>Dīgha Nikāya</th>
                    <td class="gr${data.CstGrad[5]}">${data.CstFreq[5]}</td>
                    <td class="gr${data.CstGrad[24]}">${data.CstFreq[24]}</td>
                    <td class="gr${data.CstGrad[34]}">${data.CstFreq[34]}</td>
                </tr>
                <tr>
                    <th>Majjhima Nikāya</th>
                    <td class="gr${data.CstGrad[6]}">${data.CstFreq[6]}</td>
                    <td class="gr${data.CstGrad[25]}">${data.CstFreq[25]}</td>
                    <td class="gr${data.CstGrad[35]}">${data.CstFreq[35]}</td>
                </tr>
                <tr>
                    <th>Saṃyutta Nikāya</th>
                    <td class="gr${data.CstGrad[7]}">${data.CstFreq[7]}</td>
                    <td class="gr${data.CstGrad[26]}">${data.CstFreq[26]}</td>
                    <td class="gr${data.CstGrad[36]}">${data.CstFreq[36]}</td>
                </tr>
                <tr>
                    <th>Aṅguttara Nikāya</th>
                    <td class="gr${data.CstGrad[8]}">${data.CstFreq[8]}</td>
                    <td class="gr${data.CstGrad[27]}">${data.CstFreq[27]}</td>
                    <td class="gr${data.CstGrad[37]}">${data.CstFreq[37]}</td>
                </tr>
                <tr>
                    <th>Khuddaka Nikāya 1</th>
                    <td class="gr${data.CstGrad[9]}">${data.CstFreq[9]}</td>
                    <td class="gr${data.CstGrad[28]}">${data.CstFreq[28]}</td>
                    <td class="void"></td>
                </tr>
                <tr>
                    <th>Khuddaka Nikāya 2</th>
                    <td class="gr${data.CstGrad[10]}">${data.CstFreq[10]}</td>
                    <td class="gr${data.CstGrad[29]}">${data.CstFreq[29]}</td>
                    <td class="void"></td>
                </tr>
                <tr>
                    <th>Khuddaka Nikāya 3</th>
                    <td class="gr${data.CstGrad[11]}">${data.CstFreq[11]}</td>
                    <td class="gr${data.CstGrad[30]}">${data.CstFreq[30]}</td>
                    <td class="gr${data.CstGrad[38]}">${data.CstFreq[38]}</td>
                    <td class="void"></td>
                </tr>
                <tr>
                    <th class="vertical-text" rowspan="8">Abhidhamma</th>
                </tr>
                <tr>
                    <th>Dhammasaṅgaṇī</th>
                    <td class="gr${data.CstGrad[12]}">${data.CstFreq[12]}</td>
                    <td class="gr${data.CstGrad[31]}" rowspan="7">${data.CstFreq[31]}</td>
                    <td class="gr${data.CstGrad[39]}" rowspan="7">${data.CstFreq[39]}</td>
                </tr>
                <tr>
                    <th>Vibhaṅga</th>
                    <td class="gr${data.CstGrad[13]}">${data.CstFreq[13]}</td>
                </tr>
                <tr>
                    <th>Dhātukathā</th>
                    <td class="gr${data.CstGrad[14]}">${data.CstFreq[14]}</td>
                </tr>
                <tr>
                    <th>Puggalapaññatti</th>
                    <td class="gr${data.CstGrad[15]}">${data.CstFreq[15]}</td>
                </tr>
                <tr>
                    <th>Kathāvatthu</th>
                    <td class="gr${data.CstGrad[16]}">${data.CstFreq[16]}</td>
                </tr>
                <tr>
                    <th>Yamaka</th>
                    <td class="gr${data.CstGrad[17]}">${data.CstFreq[17]}</td>
                </tr>
                <tr>
                    <th>Paṭṭhāna</th>
                    <td class="gr${data.CstGrad[18]}">${data.CstFreq[18]}</td>
                </tr>
                <tr>
                    <th class="vertical-text" rowspan="10">Aññā</th>
                </tr>
                <tr>
                    <th>Visuddhimagga</th>
                    <td class="void"></td>
                    <td class="gr${data.CstGrad[32]}">${data.CstFreq[32]}</td>
                    <td class="gr${data.CstGrad[40]}">${data.CstFreq[40]}</td>
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
    </div>
    <div class="freq-table-wrapper">
        <table class="freq">
            <thead>
                <tr style="text-align: right;">
                    <th colspan="2">
                        <b>
                            Buddha Jayanti Tipiṭaka (Sri Lanka)
                        </b>
                    </th>
                    <th>M</th>
                    <th>A</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <th class="vertical-text" rowspan="6">Vinaya</th>
                </tr>
                <tr>
                    <th>Pārājika</th>
                    <td class="gr${data.BjtGrad[0]}">${data.BjtFreq[0]}</td>
                    <td class="gr${data.BjtGrad[19]}">${data.BjtFreq[19]}</td>
                </tr>
                <tr>
                    <th>Pācittiya</th>
                    <td class="gr${data.BjtGrad[1]}">${data.BjtFreq[1]}</td>
                    <td class="gr${data.BjtGrad[20]}">${data.BjtFreq[20]}</td>
                </tr>
                <tr>
                    <th>Mahāvagga</th>
                    <td class="gr${data.BjtGrad[2]}">${data.BjtFreq[2]}</td>
                    <td class="gr${data.BjtGrad[21]}">${data.BjtFreq[21]}</td>
                </tr>
                <tr>
                    <th>Cūḷavagga</th>
                    <td class="gr${data.BjtGrad[3]}">${data.BjtFreq[3]}</td>
                    <td class="gr${data.BjtGrad[22]}">${data.BjtFreq[22]}</td>
                </tr>
                <tr>
                    <th>Parivāra</th>
                    <td class="gr${data.BjtGrad[4]}">${data.BjtFreq[4]}</td>
                    <td class="gr${data.BjtGrad[23]}">${data.BjtFreq[23]}</td>
                </tr>
                <tr>
                    <th class="vertical-text" rowspan="8">Sutta</th>
                </tr>
                <tr>
                    <th>Dīgha Nikāya</th>
                    <td class="gr${data.BjtGrad[5]}">${data.BjtFreq[5]}</td>
                    <td class="gr${data.BjtGrad[24]}">${data.BjtFreq[24]}</td>
                </tr>
                <tr>
                    <th>Majjhima Nikāya</th>
                    <td class="gr${data.BjtGrad[6]}">${data.BjtFreq[6]}</td>
                    <td class="gr${data.BjtGrad[25]}">${data.BjtFreq[25]}</td>
                </tr>
                <tr>
                    <th>Saṃyutta Nikāya</th>
                    <td class="gr${data.BjtGrad[7]}">${data.BjtFreq[7]}</td>
                    <td class="gr${data.BjtGrad[26]}">${data.BjtFreq[26]}</td>
                </tr>
                <tr>
                    <th>Aṅguttara Nikāya</th>
                    <td class="gr${data.BjtGrad[8]}">${data.BjtFreq[8]}</td>
                    <td class="gr${data.BjtGrad[27]}">${data.BjtFreq[27]}</td>
                </tr>
                <tr>
                    <th>Khuddaka Nikāya 1</th>
                    <td class="gr${data.BjtGrad[9]}">${data.BjtFreq[9]}</td>
                    <td class="gr${data.BjtGrad[28]}">${data.BjtFreq[28]}</td>
                </tr>
                <tr>
                    <th>Khuddaka Nikāya 2</th>
                    <td class="gr${data.BjtGrad[10]}">${data.BjtFreq[10]}</td>
                    <td class="gr${data.BjtGrad[29]}">${data.BjtFreq[29]}</td>
                </tr>
                <tr>
                    <th>Khuddaka Nikāya 3</th>
                    <td class="gr${data.BjtGrad[11]}">${data.BjtFreq[11]}</td>
                    <td class="gr${data.BjtGrad[30]}">${data.BjtFreq[30]}</td>
                </tr>
                <tr>
                    <th class="vertical-text" rowspan="8">Abhidhamma</th>
                </tr>
                <tr>
                    <th>Dhammasaṅgaṇī</th>
                    <td class="gr${data.BjtGrad[12]}">${data.BjtFreq[12]}</td>
                    <td class="gr${data.BjtGrad[31]}">${data.BjtFreq[31]}</td>
                </tr>
                <tr>
                    <th>Vibhaṅga</th>
                    <td class="gr${data.BjtGrad[13]}">${data.BjtFreq[13]}</td>
                    <td class="gr${data.BjtGrad[32]}">${data.BjtFreq[32]}</td>
                </tr>
                <tr>
                    <th>Dhātukathā</th>
                    <td class="gr${data.BjtGrad[14]}">${data.BjtFreq[14]}</td>
                    <td class="gr${data.BjtGrad[33]}">${data.BjtFreq[33]}</td>
                </tr>
                <tr>
                    <th>Puggalapaññatti</th>
                    <td class="gr${data.BjtGrad[15]}">${data.BjtFreq[15]}</td>
                    <td class="gr${data.BjtGrad[34]}">${data.BjtFreq[34]}</td>
                </tr>
                <tr>
                    <th>Kathāvatthu</th>
                    <td class="gr${data.BjtGrad[16]}">${data.BjtFreq[16]}</td>
                    <td class="gr${data.BjtGrad[35]}">${data.BjtFreq[35]}</td>
                </tr>
                <tr>
                    <th>Yamaka</th>
                    <td class="gr${data.BjtGrad[17]}">${data.BjtFreq[17]}</td>
                    <td class="gr${data.BjtGrad[36]}">${data.BjtFreq[36]}</td>
                </tr>
                <tr>
                    <th>Paṭṭhāna</th>
                    <td class="gr${data.BjtGrad[18]}">${data.BjtFreq[18]}</td>
                    <td class="gr${data.BjtGrad[37]}">${data.BjtFreq[37]}</td>
                </tr>
                <tr>
                    <th class="vertical-text" rowspan="10"></th>
                </tr>
                <tr>
                    <th>Visuddhimagga</th>
                    <td class="void"></td>
                    <td class="gr${data.BjtGrad[38]}">${data.BjtFreq[38]}</td>
                </tr>
            </tbody>
        </table>
    </div>
    <div class="freq-table-wrapper">
        <table class="freq">
            <thead>
                <tr style="text-align: right;">
                    <th colspan="2">
                        <b>
                            Mahāsaṅgīti Tipiṭaka (Sutta Central)
                        </b>
                    </th>
                    <th>M</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <th class="vertical-text" rowspan="6">Vinaya</th>
                </tr>
                <tr>
                    <th>Pārājika</th>
                    <td class="gr${data.ScGrad[0]}">${data.ScFreq[0]}</td>
                </tr>
                <tr>
                    <th>Pācittiya</th>
                    <td class="gr${data.ScGrad[1]}">${data.ScFreq[1]}</td>
                </tr>
                <tr>
                    <th>Mahāvagga</th>
                    <td class="gr${data.ScGrad[2]}">${data.ScFreq[2]}</td>
                </tr>
                <tr>
                    <th>Cūḷavagga</th>
                    <td class="gr${data.ScGrad[3]}">${data.ScFreq[3]}</td>
                </tr>
                <tr>
                    <th>Parivāra</th>
                    <td class="gr${data.ScGrad[4]}">${data.ScFreq[4]}</td>
                </tr>
                <tr>
                    <th class="vertical-text" rowspan="8">Sutta</th>
                </tr>
                <tr>
                    <th>Dīgha Nikāya</th>
                    <td class="gr${data.ScGrad[5]}">${data.ScFreq[5]}</td>
                </tr>
                <tr>
                    <th>Majjhima Nikāya</th>
                    <td class="gr${data.ScGrad[6]}">${data.ScFreq[6]}</td>
                </tr>
                <tr>
                    <th>Saṃyutta Nikāya</th>
                    <td class="gr${data.ScGrad[7]}">${data.ScFreq[7]}</td>
                </tr>
                <tr>
                    <th>Aṅguttara Nikāya</th>
                    <td class="gr${data.ScGrad[8]}">${data.ScFreq[8]}</td>
                </tr>
                <tr>
                    <th>Khuddaka Nikāya 1</th>
                    <td class="gr${data.ScGrad[9]}">${data.ScFreq[9]}</td>
                </tr>
                <tr>
                    <th>Khuddaka Nikāya 2</th>
                    <td class="gr${data.ScGrad[10]}">${data.ScFreq[10]}</td>
                </tr>
                <tr>
                    <th>Khuddaka Nikāya 3</th>
                    <td class="gr${data.ScGrad[11]}">${data.ScFreq[11]}</td>
                </tr>
                <tr>
                    <th class="vertical-text" rowspan="8">Abhidhamma</th>
                </tr>
                <tr>
                    <th>Dhammasaṅgaṇī</th>
                    <td class="gr${data.ScGrad[12]}">${data.ScFreq[12]}</td>
                </tr>
                <tr>
                    <th>Vibhaṅga</th>
                    <td class="gr${data.ScGrad[13]}">${data.ScFreq[13]}</td>
                </tr>
                <tr>
                    <th>Dhātukathā</th>
                    <td class="gr${data.ScGrad[14]}">${data.ScFreq[14]}</td>
                </tr>
                <tr>
                    <th>Puggalapaññatti</th>
                    <td class="gr${data.ScGrad[15]}">${data.ScFreq[15]}</td>
                </tr>
                <tr>
                    <th>Kathāvatthu</th>
                    <td class="gr${data.ScGrad[16]}">${data.ScFreq[16]}</td>
                </tr>
                <tr>
                    <th>Yamaka</th>
                    <td class="gr${data.ScGrad[17]}">${data.ScFreq[17]}</td>
                </tr>
                <tr>
                    <th>Paṭṭhāna</th>
                    <td class="gr${data.ScGrad[18]}">${data.ScFreq[18]}</td>
                </tr>
            </tbody>
        </table>
    </div>
</div>
`
    return html
}


