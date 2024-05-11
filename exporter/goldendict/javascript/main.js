

function button_click(el) {
    const target_id=el.getAttribute('data-target');

    // generate root & compound families + feedback tab
    generateTemplateFromJson(target_id);
    
    target = document.getElementById(target_id);
    target.classList.toggle('hidden');

    if (el.classList.contains('close')) {
        // close button should toggle active highlight on the button which controls the same target
        target_control = document.querySelector('a.button[data-target="'+target_id+'"]');
        target_control.classList.toggle('active');
    } else {
        // close button doesn't need active highlight
        el.classList.toggle('active');
    }
    // prevent default
    return false;
}





function init() {
    
    //test if json was already initilized before
    if (typeof json_init_done === 'undefined' || json_init_done !== 1)  {
        
        // **remember that the json init was done**
        var json_init_done = 1;
        
        // get path prefix for resource folder, that js files can be loaded
        // needs href and org to be set to the same value in <link id="js_main" href="main.js" org="main.js">
        findResourcePath()
        
        // js files to be loaded on page load (written in the global header of the dict entry)
        const files = [
            "template.js",
            "json_templates.js",
            "family_compound_json.js",
            "family_idiom_json.js",
            "family_root_json.js",
            "family_set_json.js",
            "family_word_json.js",
        ];
        
        for (var i = 0; i < files.length; i++) {
            const js_file = document.createElement('script');
            js_file.src = data['resource_prefix_path'] + files[i];
            document.getElementsByTagName("head")[0].appendChild(js_file);
        
        }
        
    }
    
}





// find resource path that files can be loaded easier / images can be used in templats
// needs href and org to be set to the same value in <link id="js_main" href="main.js" org="main.js">
function findResourcePath(){
    
    // check if it was already calculated
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


init();

