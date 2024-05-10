// automatically generated with templates_js\generate_json_template_file.py
var template = { 
"compound":"			<!-- in the if condition the variable 'data.compounds.length' is a workaround. normaly it would be only 'compounds.length' but the if part \
				of the template function is parsed with eval, and the aditional variable that is passed to function is called data, so it has to be prefixed -->\
			{{if='data.compounds.length > 1'}}  \
			<p class=heading id='{{link}}_cf_top'>jump to: \
				{{loop='compounds'}} <a class=jump href=#{{link}}_cf_{{item}}>{{item}}</a> {{/loop}}\
			{{/if}}\
			\
			{{compound_sub}}\
\
			</table> \
			<p class=footer>Spot a mistake? <a class=link \
					href=https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&entry.438735500={{link}}&entry.326955045=Compound+Family&entry.1433863141=GoldenDict+{{date}} \
					target=_blank>Fix it here</a>.\
					<a class='jump' href='#{{link}}_cf_top'> ⤴</a>",
"compound_sub":"			<p class='heading underlined' id='{{link}}_cf_{{compound_name}}'><b>{{count}}</b> compounds which contain <b>{{compound_name}}</b> <a class=jump href=#{{link}}_cf_{{compound_name}}> ⤴</a>\
			\
			<table class=family> \
				{{loop='data'}} \
				<tr> \
					<th>{{0}} \
					<td><b>{{1}}</b> \
					<td>{{2}} \
					<span class=gray>{{3}}</span> \
				{{/loop}} \
			</table>\
			\
				\
",
"feedback":"			<p>ID <b>{{id}}</b>\
			<p>Digital Pāḷi Dictionary is a work in progress, made available for testing and feedback purposes. \
			<p><a class=link \
					href=https://docs.google.com/forms/d/e/1FAIpQLSfResxEUiRCyFITWPkzoQ2HhHEvUS5fyg68Rl28hFH6vhHlaA/viewform?usp=pp_url&entry.1433863141=GoldenDict+{{date}}\
					target=_blank>Add a missing word</a> <span> . Please use this </span> <a class=link \
					href=https://docs.google.com/forms/d/e/1FAIpQLSfResxEUiRCyFITWPkzoQ2HhHEvUS5fyg68Rl28hFH6vhHlaA/viewform?usp=pp_url&entry.1433863141=GoldenDict+{{date}}\
					target=_blank>online form</a> to add missing words, especially from Vinaya, commentaries, and other \
				later texts. If you prefer to work offline, here is a <a download=true \
					href=https://github.com/digitalpalidictionary/dpd-db/raw/main/docs/DPD%20Add%20Words.xlsx \
					target=_blank>spreadsheet to download</a> <span> , fill in and submit. </span> \
			<p><a class=link \
					href=https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&entry.438735500={{link}}&entry.1433863141=GoldenDict+{{date}}\
					target=_blank>Correct a mistake</a> <span> . Did you spot a mistake in the dictionary? Please report it. \
					It generally takes less than a minute and your corrections and suggestions help to improve the quality \
					of this dictionary for everyone who uses it. </span> \
			<p><a class=link href=https://github.com/digitalpalidictionary/digitalpalidictionary/releases>Get \
					updated</a><span>. You are using DPD GoldenDict updated on <b>{{date}}</b>. Check for an update every \
					full moon uposatha day.</span> \
			<p><a class=link href=https://digitalpalidictionary.github.io />Visit the website</a><span>. Get more detailed \
					information about installation and upgrades, advanced settings and features.</span> \
			<p><a class=link \
					href=mailto:digitalpalidictionary@gmail.com?subject=I\'d%20like%20to%20help%20with%20code!&body=Please%20let%20me%20know%20how%20I%20can%20get%20involved%20with%20the%20development%20of%20DPD.>Help \
					with coding</a><span>. If you\'re a coder and would like to support the project, please get in \
					touch.</span> \
			<p><a class=link \
					href=mailto:digitalpalidictionary@gmail.com?subject=I%20want%20to%20help%20with%20DPD!&body=Please%20let%20me%20know%20how%20I%20can%20get%20involved%20with%20the%20development%20of%20DPD.>Help \
					with Pāḷi</a><span>. If you have Pāḷi grammar skills and would like to assist, please make email \
					contact.</span> \
			<p><a class=link \
					href=mailto:digitalpalidictionary@gmail.com?subject=Keep%20me%20updated!&body=Please%20let%20me%20know%20about%20new%20features%20and%20updates%20as%20soon%20as%20they%20are%20available.>Join \
					the mailing list</a><span>. Get notified of updates and new features as soon as they become \
					available.</span> \
			<p><img src='dpd.png'> ",
"root":"			<p class='heading underlined'><b>{{count}}</b> words belong to the root family <b>{{root_family}}</b> ({{root_meaning}}) \
			<table class=family> \
				{{loop='data'}} \
				<tr> \
					<th>{{0}} \
					<td><b>{{1}}</b> \
					<td>{{2}} \
					<td><span class=gray>{{3}}</span> \
				{{/loop}} \
\
			</table> \
			<p class=footer>Something out of place? <a class=link \
					href=https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&entry.438735500={{root}}&entry.326955045=Root+Family&entry.1433863141=GoldenDict+{{date}} \
					target=_blank>Report it here</a>. " 
}