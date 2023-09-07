import argparse


class ListArgAction(argparse.Action):
    """ Action for list of strings argument

    Accept lists in form of "--arg 1 2 3", "--arg 1,2,3" and even mixed
    "--arg 1,2 3".

    Usage:

    parser.add_argument(
        '--list',
        choices=['a', 'b', 'c']
        default=['a', 'b'],
        action=ListArgAction)

    If choices omissed any values acceptable.
    """
    def __init__(self, *args, **kwargs) -> None:
        self.__choices = kwargs.pop('choices', None)
        super(ListArgAction, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None) -> None:
        result_raw = []

        for val in values:
            result_raw.extend([i.strip() for i in val.split(',')])

        result = []
        for val in result_raw:
            if val == '':
                continue
            elif self.__choices is not None and val not in self.__choices:
                raise argparse.ArgumentError(self, f'{val} not in {self.__choices}')
            result.append(val)

        setattr(namespace, self.dest, result)
