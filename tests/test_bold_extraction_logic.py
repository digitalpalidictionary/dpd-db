from bs4 import BeautifulSoup
from db.bold_definitions.functions import Context, update_context

def test_update_context_basic():
    context = Context()
    file_name = "test.xml"
    
    # Test nikaya
    soup = BeautifulSoup('<p rend="nikaya">Dīghanikāye</p>', "xml")
    context = update_context(soup.p, file_name, context)
    assert context.nikaya == "Dīghanikāye"
    
    # Test book
    soup = BeautifulSoup('<head rend="book">Sīlakkhandhavaggaṭṭhakathā</head>', "xml")
    context = update_context(soup.head, file_name, context)
    assert context.book == "Sīlakkhandhavaggaṭṭhakathā"
    
    # Test title
    soup = BeautifulSoup('<head rend="title">Brahmajālasuttaṃ</head>', "xml")
    context = update_context(soup.head, file_name, context)
    assert context.title == "Brahmajālasuttaṃ"
    
    # Test subhead
    soup = BeautifulSoup('<p rend="subhead">Ganthārambhakathā</p>', "xml")
    context = update_context(soup.p, file_name, context)
    assert context.subhead == "Ganthārambhakathā"

def test_update_context_file_overrides():
    context = Context()
    file_name = "s0513a2.att.xml"
    
    soup = BeautifulSoup('<p>anything</p>', "xml")
    context = update_context(soup.p, file_name, context)
    assert context.nikaya == "khuddakanikāye"

def test_update_context_subhead_pattern():
    context = Context()
    file_name = "test.xml"
    
    soup = BeautifulSoup('<p>[1] First Section</p>', "xml")
    context = update_context(soup.p, file_name, context)
    assert context.subhead == "[1] First Section"

def test_update_context_title_cleanup():
    context = Context()
    file_name = "test.xml"
    
    soup = BeautifulSoup('<head rend="title">(1) Sutta Title</head>', "xml")
    context = update_context(soup.head, file_name, context)
    assert context.title == "Sutta Title"
