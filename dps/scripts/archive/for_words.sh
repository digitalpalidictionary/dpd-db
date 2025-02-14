#clone suttacentral sc-data repi
# git clone https://github.com/suttacentral/sc-data

#save words to a input.txt e.g.
echo "paste words in one column
press ctrl+d when done
"
cat > temp/input.txt


#update basedir to actual
basedir=resources/sc-data/sc_bilara_data

srcfolder=$basedir/root/pli/ms/vinaya/pli-tv-kd/
trnfiolder=$basedir/translation/en/brahmali/vinaya/pli-tv-kd/
varfolder=$basedir/variant/


function clearSearch() {
sed 's/.*.json://g' | sed 's/:.*": "/ /g'| sed 's/ ",//g' | sed 's/"pli-tv-//g'
}

separator=';'

cat temp/input.txt | grep -v "^$" | while read word; 
do  
echo -n $word 
echo -n "$separator"

grep -riE "${word}" $srcfolder/* $varfolder/* | while read paliline
	do  
	id=$( echo $paliline | awk '{print $2}')
	echo -n "$paliline" | clearSearch 
echo -n "$separator"
grep -i "$id" $trnfiolder/* | while read engline
do	
cleanedEngLine=$( echo "$engline" | clearSearch )

case "$cleanedEngLine" in
    *[0-9]\.*) 
#echo "Строка содержит цифры с точкой."
topic=$(echo "$cleanedEngLine" | sed 's/.*[0-9]*\. //' | awk '{ $1 = tolower($1); print }')
section_number=$(echo "$cleanedEngLine"  | awk '{print $2}' | sed 's/\.//')
khandakha=$(echo "$cleanedEngLine" | awk '{print $1}'| sed 's/kd//g')
result="${topic} - section #${section_number} of the khandakha #${khandakha}"
#echo topic $topic
#echo section_number $section_number
#echo khandakha $khandakha
#echo result $result
echo -n "$result"
echo -n "$separator"
        ;;
    *)
#echo "Строка не содержит цифры с точкой."
echo "$cleanedEngLine"  | awk '{for (i=2; i<=NF; i++) printf $i (i<NF ? OFS : "\n")}'
        ;;
esac
echo
done
done 
#echo ";\=https://find.dhamma.gift/?p=-all+-vin&q=$word"
echo 
done 

rm temp/input.txt
exit 0