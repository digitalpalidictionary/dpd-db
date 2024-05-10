	
	// button_click() calls this function to check if a root, compound or feedback Tab needs to be generated
	//  + generate and place it
	function generateTemplateFromJson(target_id){
		
		// root family tab generation + insert:
		if (target_id.indexOf('root_family_') !== -1) {
			// get target element
			const el2 = document.getElementById(target_id);
			// create only once, than save in DOM
			if (el2.getAttribute('loaded') != "1") {
				// get dictionary entry name
				const w = target_id.replace('root_family_', '');
				// generate the template from the json root data & json_template.js file
				//  data is the global variable from the <script> tag in the dictionary entry
				const root_name = data[w]['root'];
				el2.innerHTML = renderTemplate(template["root"], family_root_json[root_name]);
				// mark that this tab has already been generated
				el2.setAttribute('loaded', '1');
			}
		}		
		
		// compound family tab generation + insert:
		if (target_id.indexOf('compound_family_') !== -1) {
			// get target element
			const el2 = document.getElementById(target_id);			
			// create only once, than save in DOM
			if (el2.getAttribute('loaded') != "1") {
				// get dictionary entry name
				const w = target_id.replace('compound_family_', '');				
				// small workaround to add compund_name to json, or its not visible in the template
				//  data is the global variable from the <script> tag in the dictionary entry
				const compounds = data[w]['compounds'];
				
				// generate the compound_sub template 
				var compound_sub = '';
				for (var i = 0; i < compounds.length; i++) {					
					const vPass = merge_obj(family_compound_json[compounds[i]], {'compound_name': compounds[i], 'link':data[w]['link']});  // workaround because compound entries have the compound name only in the variable key
					compound_sub = compound_sub + renderTemplate(template["compound_sub"], vPass) + '\n';
				}
				
				// add some additional variables for the template
				data[w]['compound_sub'] = compound_sub;
				data[w]['compound_len'] =  data[w]['compounds'].length
				// generate the template from the json compound data & json_template.js file
				el2.innerHTML = renderTemplate(template["compound"], data[w]);
				// mark that this tab has already been generated
				el2.setAttribute('loaded', '1');
			}
		}



		// feedback tab generation + insert:
		if (target_id.indexOf('feedback_') !== -1) {
			// get target element
			const el2 = document.getElementById(target_id);
			// create only once, than save in DOM
			if (el2.getAttribute('loaded') != "1") {
				// get dictionary entry name
				const w = target_id.replace('feedback_', '');
				// generate the template from the json_template.js file
				//  data is the global variable from the <script> tag in the dictionary entry
				el2.innerHTML = renderTemplate(template["feedback"], data[w]);
				// mark that this tab has already been generated
				el2.setAttribute('loaded', '1');
			}			
		}

		
	}
	
	
// -------------- template function - with (hopefully) friedly support from perplexity.ia ------------------------	
// ** takes a template string and populates all {{variables}} with real data **

	// data can be any array, eg. data = {'items':'fruits', 'count':5, 'fruity':['apples','oranges']}  ->  there are {{items}} in the shop. we have {{count}}
	// loop accepts {{loop='some_array'}}...{{/loop}}  
	// some_array = [{a:'hi',b:3},{a:'bar',b:2},..] or some_array = [['hi',3],['bar',2],..]
	// to use: {{loop='some_array'}}{{a}}, {{b}}{{/loop}} or {{loop='some_array'}}{{0}}, {{1}}{{/loop}} 
	// {{if='condition'}} {{else}} {{/if}}  - the condition can be any js statement
	function renderTemplate(template, data) {
		const loopRegex = /\{\{loop='(\w+)'\}\}([\s\S]*?)\{\{\/loop\}\}/g;
		const variableRegex = /\{\{([\w.]+)\}\}/g;
		const srcRegex = /src='([^']+)'/g;
		const ifRegex = /\{\{if='([^']+)'\}\}([\s\S]*?)(?:\{\{else\}\}([\s\S]*?))?\{\{\/if\}\}/g;
		const resource_prefix_path = findResourcePath();

		return template
			// the if condition is just passed to eval (so the variables from data must be prefixed with 'data.')
			.replace(ifRegex, function(match, condition, trueText, falseText) {  
				const conditionResult = eval(condition);
				return conditionResult ? trueText : (falseText || '');
			})
			.replace(loopRegex, function(match, loopVar, loopTemplate) {
				const loopData = data[loopVar];
				if (!Array.isArray(loopData)) {
					return match;
				}

				return loopData.map(function(item, index) {
					const dataItem = merge_obj(data, {'item':item, 'index': index});
					return loopTemplate.replace(variableRegex, function(match, key) {
						if (key === '.') {
							return item;
						}
						if (!isNaN(parseInt(key, 10))) {
							return item[parseInt(key)];
						}
						const value = key.split('.').reduce(function(obj, prop) {
							return obj && obj[prop];
						}, dataItem);
						return value !== undefined ? value : match;
					});
				}).join('');
			})
			.replace(variableRegex, function(match, key) {
				return data.hasOwnProperty(key) ? data[key] : match;
			})
			.replace(srcRegex, function(match, path) {
				return "src='" + resource_prefix_path + path + "'";
			});
	}

	// goldendict does not support newer syntax to merge objects, so this function can be used to merge multiple variables
	function merge_obj() {
	  var mergedObject = {};

	  // Iterate over each argument passed to the function
	  for (var i = 0; i < arguments.length; i++) {
		var currentObject = arguments[i];

		// Copy properties from the current object to mergedObject
		for (var key in currentObject) {
		  if (currentObject.hasOwnProperty(key)) {
			mergedObject[key] = currentObject[key];
		  }
		}
	  }
	  return mergedObject;
	}


// --------------end template function ------------------------
	
	// find resource path that images can be used in templats / js files can be easyer loaded
	function findResourcePath(){
		
		if (typeof data['resource_prefix_path'] === 'undefined') {
			
			// the <link id="json_file_templates" href="json_templates.js" org="json_templates.js"> tag from the dictionary entry 
			// needs both href and org attribute to see how the src path is modified by goldendict
			const validPath = document.getElementById('js_main').getAttribute('href');
			const orgPath = document.getElementById('js_main').getAttribute('org');	
			
			// extract the prefix
			const prefix = validPath.replace(orgPath, '');
			
			// check if the generated prefix + orgPath equals the resource path
			if (prefix + orgPath == validPath) {
				// save it in the global variable data for quick return next time around
				data['resource_prefix_path'] = prefix;
			} else {
				// if there where errors dont prepend anything to the src path
				data['resource_prefix_path'] = '';
			}
		}		
		return data['resource_prefix_path'];		
	}
	
	
// ---------debugging: add a small link to the bottom of the page to quickly view the page source-----------------------	
function debug_View_Source_link(){
	
// Create the "View Source Code" link
	const viewSourceLink = document.createElement('a');
	viewSourceLink.href = '#';
	viewSourceLink.textContent = '[debug: view source code]';
	document.body.appendChild(viewSourceLink);

	viewSourceLink.addEventListener('click', function(event) {
		event.preventDefault(); // Prevent the link from navigating

		// Create the textarea element
		const sourceCodeInput = document.createElement('textarea');
		sourceCodeInput.id = 'sourceCodeInput';
		sourceCodeInput.readOnly = true;
		sourceCodeInput.style.width = '100%';
		sourceCodeInput.style.height = '300px';
		sourceCodeInput.style.fontFamily = 'monospace';

		// Get the current page's HTML source
		const pageSource = document.documentElement.outerHTML;

		// Set the source code in the text input field
		sourceCodeInput.value = pageSource;

		// Append the textarea to the body
		document.body.appendChild(sourceCodeInput);

	});
		
}
// debug_save_source()