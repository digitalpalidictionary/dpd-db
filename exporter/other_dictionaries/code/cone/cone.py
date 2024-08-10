import json
from pathlib import Path
import re

from tools.goldendict_exporter import export_to_goldendict_with_pyglossary
from tools.goldendict_exporter import DictEntry, DictInfo, DictVariables
from tools.mdict_exporter import export_to_mdict
from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths
from tools.printer import p_counter, p_green, p_green_title, p_red, p_title, p_yes
from tools.tic_toc import tic, toc

def main():
    tic()
    p_title("exporting cone")
    
    p_green("saving json")
    pth: ProjectPaths = ProjectPaths()

    with open(pth.cone_source_path) as f:
        cone_dict = json.load(f)
    
    with open(pth.cone_front_matter_path) as f:
        front_matter_dict = json.load(f)
    
    cone_dict.update(front_matter_dict)

    # save json
    with open(pth.cone_json_path, "w") as f:
        json.dump(cone_dict, f)
    p_yes("ok")
    
    p_green_title("making dict data")
    dict_data = []
    bulk_dump_html = "" # FIXME delete when done testing css for classes
    errors = []

    for counter, (key, html_body) in enumerate(cone_dict.items()):
        
        # clean html lines breaks at the bottom of the entry
        html_body = re.sub(
            r"\s*<p>\s*&nbsp;\s*<br>\s*<br>\s*</p>\s*", "", html_body)
        
        if "href" in html_body:
            html_body = remove_links(html_body)
        
        if html_body:
            html = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="utf-8">
                <link href="cone.css" rel="stylesheet">
            </head>
            <body> 
            """
            html += html_body
            html += "</body></html>"

            synonyms = make_synonyms_list(key)
            synonyms += add_niggahitas(synonyms, all=False)

            dict_entry = DictEntry(
                word=key,
                definition_html=html,
                definition_plain="",
                synonyms=synonyms,
            )
            
            dict_data.append(dict_entry)
            bulk_dump_html += html

        else:
            errors.append(key)
        
        if counter % 5000 == 0:
            p_counter(counter, len(cone_dict), key)
    
    if errors:
        errors_string = ', '.join(errors)
        errors_string = errors_string \
            .replace("[", "[[").replace("]", "]]") \
            .replace("(", "((").replace(")", "))")
        p_red(f"ERRORS on: {errors_string}")

    # FIXME delete when done testing css
    with open("exporter/other_dictionaries/code/cone/bulk_dump_html.html", "w") as f:
        f.write(bulk_dump_html)

    p_green("making dict_info and dict_var")

    dict_info = DictInfo(
        bookname="Dictionary of Pāli by Margaret Cone",
        author="Margaret Cone",
        description="""<div>
	<div class="title"><span class="title">A Dictionary of Pāli</span></div>
	<div class="byline">
		Texts, Works Cited, Abbreviations, and Symbols<br>
		Parts I–III combined, revised by Martin Straube
	</div>

	<h3>Foreword to the digital edition</h3>
	<p>
		The first modern Pali-English dictionary was Robert Childers’ A Dictionary of the Pali Language, published in two volumes (1872–1875). T.W. Rhys Davids and William Stede’s The Pali Text Society’s Pali-English Dictionary (1921–1925) took as its starting point Childers’ dictionary and was fifty years in the making. In his foreword Rhys Davids commented: ‘This work is essentially preliminary.’
	</p>
	<p>
		A project to provide a comprehensive Pali dictionary in the form of the Copenhagen A Critical Pāli Dictionary dates from the early decades of the twentieth century, but through lack of secure funding this came to an end in 2011 with the publication of a third volume in 2011, ending with the word karetu-kama. Hence A Critical Pāli Dictionary covers no more than a third of the Pali lexicon.
	</p>
	<p>
		Alongside the Copenhagen project, the Pali Text Society has been working on revising Rhys Davids and Stede’s dictionary for fifty years. Since 1984, using funds bequeathed to the Society by I.B. Horner (1896–1981), the Society has funded a full-time research fellow to work on this project. From 1984 to 2018 this position was occupied by Dr Margaret Cone. While the original plan was to revise the PTS’s 1925 dictionary and produce a second edition, it became apparent that so little of the original dictionary would remain unaltered that what was actually being undertaken was the production of a completely new dictionary. This has become A Dictionary of Pāli. Part one of this dictionary, covering the letters a–kh was published by the Pali Text Society in 2001, part two, covering the letters g–n, in 2010, and part three, covering the letters p–bh, in 2020. Since 2018 the Society has funded Dr Martin Straube to continue Dr Cone’s work on the Dictionary by working on volume 4, the final volume.
	</p>
	<p>
	  Writing in 1995 about the prospects for the publication of Pali dictionaries, K.R. Norman suggested that when the new dictionary was eventually published the PTS would likely keep the old single-volume 1925 dictionary in print at a subsidised price for the benefit of students who could not afford the new dictionary. The advent of online publishing in the intervening years means that the problem of access to expensive scholarly resources for students and others can be readily solved by online publication: the 1925 Pali-English Dictionary is now available online via several websites, as is also <a href="https://cpd.uni-koeln.de/">A Critical Pāli Dictionary</a>. The PTS has now facilitated the translation of the first three volumes of A Dictionary of Pāli into a digital format for publication online. In keeping with its aim to promote the study of Pali literature, the Pali Text Society is happy to make this new dictionary freely available online on the gandhari.org site for the benefit of students and scholars. Despite all efforts to ensure a correct reproduction of the printed volumes, errors may have crept into the online edition. Users are therefore requested to consult the printed volumes in cases of doubt.
	</p>
	<p>
		T.W. Rhys Davids’ words at the end of his foreword to the 1925 dictionary apply equally to the current dictionary:
	</p>
	<p>
		‘Anybody familiar with this sort of work will know what care and patience, what scholarly knowledge and judgment are involved in the collection of such material, in the sorting, the sifting and final arrangement of it, in the adding of cross references, in the consideration of etymological puzzles, in the comparison and correction of various or faulty readings, and in the verification of references given by others, or found in the indexes.’
	</p>
	<p>
		Anyone wishing to learn more about the Pali Text Society, purchase its publications (including A Dictionary of Pāli) or support its projects by becoming a member is invited to visit its website <a href="palitextsociety.org">palitextsociety.org</a>.
	</p>

	<h3>Foreword to the print edition</h3>
	<p>
		The first Pāli-English dictionary, published in two volumes in 1872 and 1875, was the work of Robert Caesar Childers. His main soure was <i>Abhidhānappadīpikā,</i> a dictionary in Pāli, probably of the late 12th century, which was itself based on the Sanskrit <i>Amarakośa</i>. He was able to consult Singhalese bhikkhus, but had access to very few Pāli texts. Even so, his dictionary is an admirable work and a considerable achievement for its time.
	</p>
	<p>
		As European knowledge of Pāli texts grew, Childers’ dictionary became unsatisfactory, and one of the aims of Thomas William Rhys Davids, the founder of the Pāli Text Society, was to produce a Pāli-English dictionary better able to serve the needs of those wishing to read or indeed edit Pāli texts. In the early years of the last century he tried to find scholars throughout Europe to co-operate in producing such a dictionary, but he met various setbacks and disappointments, and after the First World War had ended most hopes of international co-operation, he at last decided that he himself would launch what he thought of as a provisional dictionary, with Dr. William Stede as co-editor, and using some material provided by other scholars. This invaluable dictionary was published from 1921–1925.
	</p>
	<p>
		Meanwhile, in Copenhagen, Dines Andersen and Helmer Smith had begun to produce the Critical Pāli Dictionary, the first fascicle of which appeared in 1924. They had the benefit of the work of Carl Wilhelm Trenckner (1824–1891), who, while making transcripts of most of the Pāli manuscripts in the rich Copenhagen Collection, and of others from London, had made preparations for a dictionary, writing small paper-slips containing words and references, observations on grammar and syntax, and quotations illustrating secular and daily life. Andersen and Smith possessed a wide knowledge of Pāli combined with expertise in philology, in grammar, in Sanskrit and in other Indo-Aryan languages, and they laid strong and solid foundations for the Critical Pāli Dictionary. It is a giant work, an exhaustive dictionary, and for any serious Pali scholar, indispensable. Fascicles continue to be produced, but it will be many years before it is completed.
	</p>
	<p>
		In the Foreword to the first fascicle of the Pāli Text Society’s dictionary, Rhys Davids wrote:
	</p>
	<div class="introquote">
		<p>
			‘It has been decided … to reserve the proceeds of the sale [of the first edition] for the eventual issue of a second edition which shall come nearer to our ideals of what a Pāli Dictionary should be.’
		</p>
	</div>
	<p>
		This was the task I began several years ago. Within a very short time I realised that so little could be left unaltered that I had to produce a completely new dictionary, not a revision of the existing one. Rhys Davids’ dictionary is only one of my sources, although an important one. The dictionary does however remain essentially a dictionary of the texts published by the Pāli Text Society.
	</p>
	<p>
		This dictionary has two main aims: first, to help its user read and understand the Pāli Canon and its commentaries; and second, to provide a picture of the language, syntax, and even grammar of these texts.
	</p>
	<p>
		To achieve the first aim, I have tried to define all the words which appear in the texts in so far as that is possible given the fallibility of even the most recent technological aids and the limits of human capability. For the second, I have extensively used quotation to illustrate meaning, rather than providing mere references, and have given detailed information on declension and especially on parts of verbs. As a secondary aim was to produce a relatively concise dictionary, there are some things this dictionary is not. It is not an etymological dictionary, its primary reference being to Sanskrit. It is not a concordance, but quotes selectively. I have tried to show the range of texts in which a word appears, but the emphasis is on canonical texts, with less reference to commentaries. Not every compound is listed, only those where the members do not appear independently, or where the meaning might not be immediately apparent. Negative forms and many forms with <i>su-, du(r)-</i> or <i>ni(r)-</i> are given under the primary word.
	</p>
	<p>
		The writing of this dictionary presented two main difficulties. The first is that it proved impossible to be sure of the meaning of some words, where etymology and context were not sufficient to produce certainty. There are, therefore, more queries remaining than one would like. The second difficulty concerns the texts themselves. It is likely that most users of this dictionary will also be using mainly the editions of the Pāli Text Society. The majority of these editions were made many years ago, sometimes from only one or a very few manuscripts, by editors who had little help to aid their decisions. The consequence is a considerable number of doubtful readings. I have therefore very often quoted from the Burmese, Singhalese and Thai editions. Sometimes it is possible to express a preference for one or the other reading, sometimes each reading could be justified, sometimes no reading is really convincing. I give these alternative readings so that the reader may consider and choose, and to point out the fallibility of all editions.
	</p>
	<p>
		I have tried to give the quotations as they appear in the texts, but I have regularised some spellings: whatever the edition has, I always write final <i>anusvāra</i> (eg <i>~aṃ ca,</i> not <i>~añ ca; ~aṃ yeva,</i> not <i>~aññeva</i>), and <i>vy-</i> (not <i>by-</i>).
	</p>
	<p>
		It hardly needs to be said that I, as any writer of a dictionary, depend on the work of previous and present scholars, in particular of the writers of the Pāli Text Society’s first Pāli-English Dictionary and of the continuing Critical Pāli Dictionary. Generally I make no acknowledgement to these scholars in the articles of the dictionary, but I do so now, for my debt to them is great.
	</p>
	<p class="right">
		Margaret Cone<br>
	</p>
	<p class="left">
		Darwin College<br>
		Cambridge<br>
		2001<br>
	</p>
	<br>
	<br>
	<br>
	<br>
	<br>
</div>""",
        website="https://gandhari.org/dictionary?section=dop",
        source_lang="pi",
        target_lang="en",
    )

    dict_var = DictVariables(
        css_path = pth.cone_css_path,
        js_paths=None,
        gd_path=pth.cone_gd_path,
        md_path=pth.cone_mdict_path,
        dict_name="cone",
        icon_path=None,
        zip_up=True,
        delete_original=True
    )

    p_yes("")

    export_to_goldendict_with_pyglossary(
        dict_info,
        dict_var,
        dict_data,
        zip_synonyms=False
    )

    export_to_mdict(
        dict_info,
        dict_var,
        dict_data)

    toc()


def make_synonyms_list(word):
    synonyms = set()
    
    # remove digits
    if re.findall(r"\d", word):
        word = re.sub(r"\d", "", word)
    
    # ar > ā
    if re.findall(r"ar$", word):
        word_ā = re.sub(r"ar$", "ā", word)
        synonyms.add(word_ā)

    # in > ī
    if re.findall(r"in$", word):
        word_ī = re.sub(r"in$", "ī", word)
        synonyms.add(word_ī)
        word_i = re.sub(r"in$", "i", word)
        synonyms.add(word_i)
    
    # remove brackets
    if "(" in word:
        word = re.sub(r"\(|\)", "", word)
    
    synonyms.add(word)
    return list(synonyms)


def remove_links(html):
    modified_html = re.sub(r'<a href="([^"]+)">', r'<span class="blue">', html)
    modified_html = re.sub(r'</a>', r'</span>', modified_html)
    return modified_html


if __name__ == "__main__":
    main()
