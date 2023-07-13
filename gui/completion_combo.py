import logging

from typing import List, Tuple

import PySimpleGUI

LOGGER = logging.getLogger(__name__)


def count_combo_size(values: List[str]) -> Tuple[int, int]:
    width = max(map(len, values)) + 1
    return (width, 0)


class CompletionCombo(PySimpleGUI.Combo):
    """ Combo box with simplified selection
    """
    def __init__(self, values: List[str], *args, **kwargs) -> None:
        self.__values = values
        size = kwargs.get('size')
        if not size:
            self.__size = count_combo_size(values)
        kwargs['size'] = self.__size
        super().__init__(values, *args, **kwargs)

    # TODO
    def __bind(self) -> None:
        ...

    # TODO
    @classmethod
    def subscribe(cls, window, event: str) -> None:
        ...

    # TODO Bind documentation
    def reset(self) -> None:
        """ Reset variants to initial state
        """
        self.update(values=self.__values, size=self.__size)

    # TODO Save filtered list for next filtration, drop on deleting chars
    # TODO Bind documentation
    def complete(self) -> None:
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
                self.set_tooltip("\n".join(new_field_values))
                _combo_width, combo_height = self.get_size()
                tooltip = self.TooltipObject
                tooltip.y += 1.5 * combo_height
                tooltip.showtip()
            else:
                self.set_tooltip(None)
        else:
            self.reset()
            self.set_tooltip(None)

    # TODO Bind documentation
    def drop_down(self) -> None:
        """ Drop list of values down like as the arrow button has been clicked

        Only Tkinter compatible for now
        """
        # Using Tkinter event
        func = getattr(self.widget, "event_generate")
        if func:
            func("<Down>")
