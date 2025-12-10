Here's my problem:

I previously had a python script which:
- read through all the files in resources/dpd_submodules/bjt/public/static/roman_json beginning with "an-" and 
- captured the relevant data into scripts/suttas/bjt/an.bak.tsv

Unfortunately the script got deleted by a careless AI agent, before all the mistakes in scripts/suttas/bjt/an.bak.tsv were properly addressed. So the file is mostly correct, but with some errors. 

Now, I would like to recreate the script "an.py" to mimic the behaviour of the previous script, capture all the same data from iterating through the same files, and save it to scripts/suttas/bjt/an.tsv. 

Do you think you can help with this?

First start by 
1. studying the scripts/suttas/bjt/an.bak.tsv. 
2. then look at the JSON source data, not just one, cos they are all different, and work how how to extract the same data as in the tsv
3. modularize your functions to they are easy to debug. 
4. save the python script to scripts/suttas/bjt/an.py
5. run the python script with uv and save to scripts/suttas/bjt/an.tsv

Ask if you have any questions.