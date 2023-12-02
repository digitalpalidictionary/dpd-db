"""Add user additions to db, saving the old & new IDs."""

import pickle
import re

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord

from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    # get the very last id number
    last_id = max(db_session.query(PaliWord.id).all())[0]
    next_id = last_id + 1
    print(f"{'last_id:':<10}{last_id}")
    print(f"{'next_id:':<10}{next_id}")

    # save the old and new id's in a dict
    id_dict = {}

    # open the additions pickle file
    with open(pth.additions_pickle_path, "rb") as file:
        additions_list = pickle.load(file)
        
        for a in additions_list:
            # there are two pieces of data, a PaliWord and a comment
            p, comment = a
            print(f"{'comment:':<10}{comment}")
            print(p)
            
            # id values
            old_id = p.id
            p.id = next_id
            
            # test if pali_1 exists or not
            try:
                test = db_session.query(PaliWord).filter(
                    PaliWord.pali_1 == p.pali_1).one()
                print(f"[red]{'error:':<10}pali_1 already exists in db")

                # add a number if one doesnt exist
                # or increment the number if it does
                print(f"[red]{'':<10}incrementing number")

                word = re.sub(" \\d.*", "", p.pali_1)
                print(f"{'word:':<10}{word}")
                digit = int(re.sub("(.+ )(\\d.*)", "\\2", p.pali_1))
                if digit:
                    new_digit = digit + 1
                    print(f"{'digit:':<10}{digit}")
                    p.pali_1 = f"{word} {new_digit}"
                else:
                    p.pali_1 = f"{word} 2"
                print(p)  
                 
            except:
                pass

            # update the id dict
            id_dict[old_id] = next_id
            next_id = next_id + 1
            db_session.add(p)
            print()
            
    
    # db_session.commit()
    print(f"{'added:':<10}{len(additions_list)}")

    # save the id_dict as a csv
    # print(id_dict)
    with open("temp/additions.tsv", "w") as tsv_file:
        tsv_file.write("old_id\tnew_id\n")
        for k,v in id_dict.items():
            tsv_file.write(f"{k}\t{v}\n")
    print(f"{'tsv_file:':<10}saved!")

if __name__ == "__main__":
    main()

