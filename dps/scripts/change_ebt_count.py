#!/usr/bin/env python3

"""mark all which have sbs_category"""

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths


def main():
    tic()
    print("[bright_yellow] mark all which have sbs_category changing ebt_count")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    dpd_db = db_session.query(PaliWord).all()

    for word in dpd_db:
        if word.sbs:
            if word.sbs.sbs_category:
                word.dd.ebt_count = 1
            else:
                word.dd.ebt_count = ""
        else:
            word.dd.ebt_count = ""


    db_session.commit()

    db_session.close()

    toc()


if __name__ == "__main__":
    main()



# # in dpd_definition.html

# <div class='content'>
#     <p>
#         % if sbs_category:
#             <i>(s)</i>
#         % endif
#         ${pos}. 
#         % if plus_case:
#             (${plus_case}) 
#         % endif
#         ${meaning} 
#         % if summary:
#             [${summary}] 
#         % endif
#         % if make_link and i.source_link_sutta:
#         <a href="${i.source_link_sutta}">link</a>
#         % endif
#         ${complete} 
#         ${id} 
#     </p>
# </div>


# # in eport_dpd.py
#     summary = render_dpd_definition_templ(pth, i, dd, rd['make_link'], tt.dpd_definition_templ)


# def render_dpd_definition_templ(
#         __pth__: ProjectPaths,
#         i: PaliWord,
#         dd: DerivedData,
#         make_link: bool,
#         dpd_definition_templ: Template
# ) -> str:
#     """render the definition of a word's most relevant information:
#     1. pos
#     2. case
#     3 meaning
#     4. summary
#     5. degree of completition"""

#     # pos
#     pos: str = i.pos

#     # id
#     id: int = i.id

#     # plus_case
#     plus_case: str = ""
#     if i.plus_case is not None and i.plus_case:
#         plus_case: str = i.plus_case

#     meaning = make_meaning_html(i)
#     summary = summarize_construction(i)
#     complete = degree_of_completion(i)

#     # sbs_category
#     sbs_category: str = ""
#     if dd.ebt_count is None:
#         sbs_category = ""
#     elif dd.ebt_count == 1:
#         sbs_category = """<i>(s)</i>"""
#     else:
#         sbs_category = ""


#     return str(
#         dpd_definition_templ.render(
#             i=i,
#             make_link=make_link,
#             pos=pos,
#             plus_case=plus_case,
#             meaning=meaning,
#             summary=summary,
#             complete=complete,
#             id=id,
#             sbs_category=sbs_category
#             ))