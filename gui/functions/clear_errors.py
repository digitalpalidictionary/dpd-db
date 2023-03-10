

def clear_errors(window):
    error_elements = [
        e for e in window.element_list() if e.key is not None and 'error' in e.key]
    for e in error_elements:
        window[e.key].update("")