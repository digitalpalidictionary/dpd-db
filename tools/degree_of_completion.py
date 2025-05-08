from db.models import DpdHeadword


def degree_of_completion(i: DpdHeadword, html=True):
    """
    Return plain or HTML styled symbol of a word data degree of completion.
    ✔ = complete = meaning_1 and source_1
    ◑ = half-complete = meaning_1 and no source_1
    ✘ = incomplete = no meaning_1
    """

    if i.meaning_1:
        if i.source_1:
            if html:
                return """<span class="gray">✔</span>"""
            else:
                return "✔"

        else:
            if html:
                return """<span class="gray">◑</span>"""
            else:
                return "◑"
    else:
        if html:
            return """<span class="gray">✘</span>"""
        else:
            return "✘"
