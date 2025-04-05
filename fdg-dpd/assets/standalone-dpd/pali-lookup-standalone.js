// js file made from https://github.com/cittadhammo/dpd-db/tree/main/tbw/output are loaded in every page !
// variables dpd_ebts, ... can be called directly.
// console.log(dpd_i2h, dpd_ebts, dpd_deconstructor)

// original below //

function E(nodeName, text) {
 var e = document.createElement(nodeName);
 if (text) e.appendChild(T(text));
 return e;
}

//Pali lookup functions//
function generateLookupMarkup(){
 //We want to wrap every word in a tag.
 var classes = "td[lang=pi]"
 generateMarkupCallback.nodes = $(classes).toArray();
 generateMarkupCallback.start = Date.now();
 generateMarkupCallback();
 return;
}

function generateMarkupCallback() {
 var node = generateMarkupCallback.nodes.shift();
 if (!node) {
 console.log('Markup generation took ' + (Date.now() - generateMarkupCallback.start) + 's')
 return}
 toLookupMarkup(node);
 setTimeout(generateMarkupCallback, 5);
}

var paliRex = /([aiueokgcjtdnpbmyrlvshāīūṭḍṅṇṁñḷ’­”]+)/i;
var splitRex = /([^  ,. – —:;?!“‘-]+)/;
function toLookupMarkup(startNode)
{
 var parts, i, out = "", proxy, node;
 var it = new Iter(startNode, 'text');
 while (node = it.next()) if (node.nodeValue) {
 if (node.parentNode.nodeName == 'A')
  if (node.parentNode.parentNode.nodeName[0] != 'H')
  continue;
 out = "";
 parts = node.nodeValue.split(splitRex);
 for (i = 0; i < parts.length; i++) {
  if (i % 2 == 1) {// Word
  var word = parts[i]
  if (node.parentNode.nodeName != 'A')
   out += '<span class="lookup" onClick="return true">' + word + '</span>' 
  else
   out += word
  } else { //Non-word
  out += parts[i];
  }
 }
 proxy = E('span');
 node.parentNode.replaceChild(proxy, node);
 proxy.outerHTML = out;
 }
}

var G_uniRegExpNSG = /[ – :;?!,.“‘]+/gi;
var toggleLookupOn = false;
var paliDictRequested = false;
var pi2en_dict = null;
function enablePaliLookup(){
 $(document).on('mouseenter', 'span.lookup', lookupWordHandler);
 generateLookupMarkup();
}

function disablePaliLookup(){
 $(document).off('mouseenter', 'span.lookup');
 $('.meaning').remove();
 $('.lookup').each(function(){
 this.outerHTML = $(this).text();
 });
}

function lookupWordHandler(event){
 if (! 'paliDictionary' in window) return;

 if ($(this).children().is("span.meaning")) return;

 var word = $(this).text().toLowerCase().trim();
 word = word.replace(/­/g, '')//optional hyphen

 word = word.replace(/ṁg/g, 'ṅg').replace(/ṁk/g, 'ṅk').replace(/ṁ/g, 'ṁ').replace(/ṁ/g, 'ṁ');
 var meaning = lookupWord(word);
 if (meaning) {
 var textBox = $('<span class="meaning">'+meaning+'</span>');
 $(this).append(textBox);
 }
}

function lookupWord(word){
  // BEHAVIOUR
  // take the word variable and search for that in dpd_i2h.json
  // 	if it return a list of headwords
  // 		look up each headword in the list in dpd_ebts.json
  // 			add the result to html_string
  // lookup the word in  dpd_deconstructor.json
  // 	if it returns any results
  // 		 add the result to html_string
  // display the html string as a popup
  // TODO: the words in the popup must be able to be recursively looked up by clicking on them in the same way as above.
  let out ="";
  console.log("---")
  console.log("before: ", word)
  word = word.replace(/[’”'"]/g, "").replace(/ṁ/g, "ṃ");
  console.log("after: ", word)
  if(word in dpd_i2h){
    out+="<strong>" + word + '</strong><br><ul style="line-height: 1em; padding-left: 15px;">'
    for (const headword of dpd_i2h[word]){
      if(headword in dpd_ebts){
        out+='<li>' + headword + '. ' + dpd_ebts[headword] + '</li>'
      }
    }
    out += "</ul>"
  }

  if(word in dpd_deconstructor){
    out+="<strong>" + word+ '</strong><br><ul style="line-height: 1em; padding-left: 15px;">'
    out+="<li>" + dpd_deconstructor[word] + "</li>"
  }

  out+="</ul>"

  return out.replace(/ṃ/g, "ṁ")
}


function _IterPermissions(permissables){
 if (!permissables)
 return undefined;
 var tmp = [];
 if (permissables.indexOf('element') != -1)
 tmp.push(1);
 if (permissables.indexOf('text') != -1)
 tmp.push(3);
 if (permissables.indexOf('comment') != -1)
 tmp.push(8);
 if (permissables.indexOf('document') != -1)
 tmp.push(9);
 if (tmp.length > 0)
 return tmp;
}

function Iter(node, permissables){
 //Iterates in-order over the subtree headed by 'node'
 //permissables should be a string containing one or more of
 //"element, text, comment, document"
 //This iter is suitable for inserting/appending content to the
 //current node - the inserted content will not be iterated over.
 this.permissables = _IterPermissions(permissables);
 this.next_node = node;
}
Iter.prototype = {
 next_node: undefined,
 stack: [],
 permissables: null,
 next: function(){
 var current = this.next_node;
 if (current === undefined) return undefined;
 if (current.firstChild) {
  this.stack.push(this.next_node);
  this.next_node = this.next_node.firstChild;
 }
 else if (this.next_node.nextSibling) {
  this.next_node = this.next_node.nextSibling;
 }
 else {
  while (this.stack.length > 0)
  {
  var back = this.stack.pop();
  if (back.nextSibling)
  {
   this.next_node = back.nextSibling;
   break;
  }
  }
  if (this.stack.length == 0) this.next_node = undefined;
 }
 if (!this.permissables)
  return current;
 if (this.permissables.indexOf(current.nodeType) != -1)
  return current;
 
 return this.next()
 }
}

function FreeIter(node, permissables) {
 //FreeIter is an ultra lightweight iterator that traverses the entire
 //document, starting (not including) 'node', in forward or reverse.
 //next/previous ALWAYS use the live state of the node.
 this.permissables = _IterPermissions(permissables);
 this.current = node;
}

FreeIter.prototype = {
 current: undefined,
 next: function(node){
 var node = this.current;
 if (node.firstChild) {
  node = node.firstChild;
 }
 else if (node.nextSibling) {
  node = node.nextSibling;
 }
 else {
  while (true){
  node = node.parentNode;
  if (!node) {
   return undefined;
  }
  if (node.nextSibling) {
   node = node.nextSibling;
   break;
  }
  }
 }
 this.current = node;
 if (!this.permissables)
  return node;
 if (this.permissables.indexOf(node.nodeType) != -1)
  return node;
 return this.next();
 },
 previous: function(node){
 var node = this.current;
 if (node.previousSibling) {
  node = node.previousSibling;
  while (node.lastChild)
  node = node.lastChild;
 } else if (node.parentNode) {
  node = node.parentNode;
 } else {
  return undefined;
 }
 this.current = node;
 if (!this.permissables)
  return node;
 if (this.permissables.indexOf(current.nodeType) != -1)
  return node;
 return this.previous();
 }
}

function nextInOrder(node, permissables) {
 //Get the next node in 'natural order'
 if (node.firstChild) {
 node = node.firstChild;
 }
 else if (node.nextSibling) {
 node = node.nextSibling;
 }
 else {
 while (true){
  node = node.parentNode;
  if (!node) {
  return undefined;
  }
  if (node.nextSibling) {
  node = node.nextSibling;
  break;
  }
 }
 }
 if (typeof permissables == 'number') {
 if (node.nodeType == permissables)
  return node;
 }
 else if (permissables.indexOf(node.nodeType) != -1)
 return node;
 return nextInOrder(node, permissables);
}

function previousInOrder(node, permissables) {
 //Get previous node in 'natural order'
 if (node.previousSibling) {
 node = node.previousSibling;
 while (node.lastChild)
  node = node.lastChild;
 } else if (node.parentNode) {
 node = node.parentNode;
 } else {
 return undefined;
 }
 if (!permissables)
 return node;
 if (typeof permissables == 'number') {
 if (node.nodeType == permissables)
  return node;
 }
 else if (permissables.indexOf(node.nodeType) != -1)
 return node;
 return previousInOrder(node, permissables);
}