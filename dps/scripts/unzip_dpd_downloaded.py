# unip dpd from local folder Download inlt the fileserver 
# ...../Software/Golden Dictionary/Default

from datetime import date
from zipfile import ZipFile
import os


today = date.today()

output_directory = os.path.join(
   '/home/deva/filesrv1', 
   'share1', 
   'Sharing between users', 
   '1 For Everyone', 
   'Software', 
   'Golden Dictionary', 
   'Default'
)

dpd_zip = '../../../Downloads/dpd.zip'
dpd_deconstructor = '../../../Downloads/dpd-deconstructor.zip'
dpd_grammar = '../../../Downloads/dpd-grammar.zip'

with ZipFile(dpd_zip, 'r') as zipObj:
   # Extract all the contents of zip file in current directory
   zipObj.extractall(output_directory)

# Print completion message in green color
print("\033[1;33m from Downloads/ \033[0m")

# Print completion message in green color
print("\033[1;32m dpd.zip has been unpacked to the server folder \033[0m")

with ZipFile(dpd_deconstructor, 'r') as zipObj:
   # Extract all the contents of zip file in current directory
   zipObj.extractall(output_directory)

# Print completion message in green color
print("\033[1;32m dpd-deconstructor.zip has been unpacked to the server folder \033[0m")


with ZipFile(dpd_grammar, 'r') as zipObj:
   # Extract all the contents of zip file in current directory
   zipObj.extractall(output_directory)


# Print completion message in green color
print("\033[1;32m dpd-grammar.zip has been unpacked to the server folder \033[0m")


