function button_click(el) {
    const target_id=el.getAttribute('data-target');

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
