"""just draft notes"""


from mako.template import Template

from db.models import PaliWord

from tools.meaning_construction import make_meaning_html
from tools.meaning_construction import summarize_construction
from tools.meaning_construction import degree_of_completion

from tools.paths import ProjectPaths


def render_dpd_definition_templ(
        __pth__: ProjectPaths,
        i: PaliWord,
        make_link: bool,
        dpd_definition_templ: Template
) -> str:
    """render the definition of a word's most relevant information:
    1. pos
    2. case
    3 meaning
    4. summary
    5. degree of completition"""

    # pos
    pos: str = i.pos

    # plus_case
    plus_case: str = ""
    if i.plus_case is not None and i.plus_case:
        plus_case: str = i.plus_case

    # id
    id: int = i.id

    # sbs_category
    sbs_category: bool = False
    if i.sbs:
        if i.sbs.sbs_category:
            sbs_category = True

    meaning = make_meaning_html(i)
    summary = summarize_construction(i)
    complete = degree_of_completion(i)

    return str(
        dpd_definition_templ.render(
            i=i,
            make_link=make_link,
            pos=pos,
            plus_case=plus_case,
            meaning=meaning,
            summary=summary,
            complete=complete,
            id=id,
            sbs_category=sbs_category))








# dpd_definition.html

<div class='content'>
    <p>
        % if sbs_category:
            <i>(s)</i>
        % endif
        ${pos}. 
        % if plus_case:
            (${plus_case}) 
        % endif
        ${meaning} 
        % if summary:
            [${summary}] 
        % endif
        % if make_link and i.source_link_sutta:
        <a href="${i.source_link_sutta}">link</a>
        % endif
        ${complete} 
        ${id}
    </p>
</div>