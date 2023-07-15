""" Usage example:

TODO
"""

import logging

from typing import List, Tuple

import PySimpleGUI

LOGGER = logging.getLogger(__name__)


def count_combo_size(values: List[str]) -> Tuple[int, int]:
    width = max(map(len, values)) + 1
    return (width, 0)


class CompletionCombo(PySimpleGUI.Combo):
    """ Combo box with simplified selection

    TooltipObject member should not be changed after initialization
    """
    def __init__(self, values: List[str], *args, **kwargs) -> None:
        self.__values = values
        size = kwargs.get('size')
        if not size:
            self.__size = count_combo_size(values)
        kwargs['size'] = self.__size
        initial_tooltip = kwargs.get('tooltip')
        if not initial_tooltip:
            self.__initial_tooltip = '\n'.join(values)
            kwargs['tooltip'] = self.__initial_tooltip
        super().__init__(values, *args, **kwargs)

    def hide_tooltip(self) -> None:
        self.set_tooltip(self.__initial_tooltip)
        self.TooltipObject.hidetip()

    def reset(self) -> None:
        """ Reset variants to initial state
        """
        self.update(values=self.__values, size=self.__size)

    # TODO Save filtered list for next filtration, drop on deleting chars
    def filter(self) -> None:
        """ Filter values with current value
        """
        value = self.get()
        if value:
            search = value
            new_field_values = [x for x in self.__values if search in x]
            key = self.key or self.__class__.__name__
            LOGGER.debug(
                'New values of %s: %s', key, ', '.join(new_field_values))
            self.update(
                value=search,
                values=new_field_values,
                size=self.__size)
            if new_field_values:
                self.set_tooltip('\n'.join(new_field_values))
                _combo_width, combo_height = self.get_size()
                tooltip = self.TooltipObject
                tooltip.y += 1.5 * combo_height
                tooltip.showtip()
            else:
                self.hide_tooltip()
        else:
            self.reset()
            self.hide_tooltip()

    def drop_down(self) -> None:
        """ Drop list of values down like as the arrow button has been clicked

        Only Tkinter compatible for now
        """
        # Using Tkinter event
        func = getattr(self.widget, "event_generate")
        if func:
            func("<Down>")

    def complete(self) -> None:
        """ Complete word with first entry of the list
        """
        self.update(set_to_index=0)
        self.hide_tooltip()
