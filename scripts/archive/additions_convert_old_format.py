"""Convert from old additions tuple to new class."""

from rich import print
from tools.addition_class import Addition


def convert_old_format():
    new_additions_list = []

    additions_list = Addition.load_additions()

    for a in additions_list:
        # there are two pieces of data, a DpdHeadword and a comment
        pali_word, comment = a
        if int(pali_word.id) >= 75577:
            a = Addition(pali_word, comment, date_created="2023-12-01")
            new_additions_list += [a]
        
    print(new_additions_list)
    print(len(new_additions_list))
    
    Addition.save_additions(additions_list)
                

def update_old_id():
    additions_list = Addition.load_additions()

    for a in additions_list:
        a.old_id = a.pali_word.id
        print(a)

    Addition.save_additions(additions_list)


def partial_update():
    additions_list = Addition.load_additions()
    new_word, comment = additions_list[-1]
    print(new_word, comment)
    additions_list = additions_list[:-1]
    addition = Addition(new_word, comment)
    additions_list.append(addition)
    Addition.save_additions(additions_list)
    print([a for a in additions_list])


if __name__ == "__main__":
    # convert_old_format()
    # update_old_id()
    # partial_update()
