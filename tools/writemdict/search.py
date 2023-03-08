import csv
from lxml import etree
import stardict


def parse_html(content):
	doc = etree.HTML(content)
	freqs = doc.xpath('//div[starts-with(@id,"frequency")]/table/tbody/tr/td/text()')
	#frequency xpath: '//div[starts-with(@id,"frequency")]/table/tbody/tr/td/text()'
	return sum([int(it) for it in freqs if it != '-'])

dpd = stardict.read_dict_info('/Users/sadhu/Documents/Dictionaries/dpd/dpd')
results = dpd.get_dict_by_word("ākirati")
for ret in results:
	print(parse_html(ret['h']))
