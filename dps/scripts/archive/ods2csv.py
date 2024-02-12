#!/usr/bin/env python3

"""convering ods into csv keeping bold <b> and new line formating <br> and sort result in pali alpabetical order also cheking duplicates before caving"""

import zipfile
from rich.console import Console

from bs4 import BeautifulSoup
import pandas as pd
from tools.pali_sort_key import pali_sort_key
from dps.tools.paths_dps import DPSPaths
from tools.tic_toc import tic, toc

console = Console()

dpspth = DPSPaths()

class ReadOds:

    def __init__(self, filename, sheets_name):
        console.print("[bold green]opening ods")
        # get content xml data from OpenDocument file
        ziparchive = zipfile.ZipFile(filename, "r")
        xmldata = ziparchive.read("content.xml")
        ziparchive.close()
        
        #find bold styles
        self.soup = BeautifulSoup(xmldata, 'xml')
        self.sheets_name = sheets_name
        self.df = {}
        self.bold_names = self.get_bold_styles()
        
        if isinstance(sheets_name, str):
            self.sheets_name = [sheets_name]
            
        for sheet_name in sheets_name:
            sheet_rows = self.get_rows_in_sheet(sheet_name)
            if sheet_rows is not None:
                header = self.get_columns_in_row(sheet_rows[0])
                header = [it for it in header if it]
                
                n_row = len(header)
                data = [dict(zip(header, (self.get_columns_in_row(row)[:n_row]))) for row in sheet_rows[1:]]
            
                self.df[sheet_name] = pd.DataFrame(data)
        

    def check_for_duplicates(self, sheet_df):
        # Checking for duplicates in the 'id' column
        duplicated_rows = sheet_df[sheet_df['id'].duplicated(keep=False)]

        # If no duplicates found, print "no duplicates"
        if duplicated_rows.empty:
            console.print("[bold green]No duplicates found.")
        else:
            # Print the duplicates
            console.print("[bold red]Duplicates found in 'id' column:")
            console.print(duplicated_rows[['id']])
            
            # Raise an exception to halt the code
            raise ValueError("Duplicates found in 'id' column. Halting execution.")


    def save_csv(self):
        console.print("[bold green]saving csvs")
        for sheet_name in self.df:
            
            self.df[sheet_name].sort_values(by = ['lemma_1'], ignore_index=True, inplace=True, key=lambda x: x.map(pali_sort_key))
            filter = self.df[sheet_name]['lemma_1'] != ""
            self.df[sheet_name] = self.df[sheet_name][filter]

            # Call the duplicate-checking method
            self.check_for_duplicates(self.df[sheet_name])

            rows = self.df[sheet_name].shape[0]
            columns = self.df[sheet_name].shape[1]
            self.df[sheet_name].to_csv(dpspth.dps_csv_path, sep='\t', index=False, quoting=1)
            console.print(f"{dpspth.dps_path} {rows} rows {columns} columns")

    def get_bold_styles(self):
        ''' 
        in xml has office:automatic-styles to configure automatic styles for document
        each style name is under style:style > style:text-properties [@fo:font-weight="bold"]
        '''
        all_auto_styles = self.soup.find_all('office:automatic-styles')
        all_text_properties = all_auto_styles[0].find_all('style:text-properties')
        all_bolds = [item for item in all_text_properties if item.has_attr('fo:font-weight') and item['fo:font-weight'] == 'bold']
        bold_names = [item.parent['style:name'] for item in all_bolds]
        return bold_names


    def get_rows_in_sheet(self, sheet_name):
        console.print(f"[bold green]processing cell data for sheet {sheet_name.lower()}")
        current_sheet = self.soup.find('table:table', {'table:name':sheet_name})

        if current_sheet is None:
            console.print('[bold red]could not find sheet', sheet_name)
            return None

        if isinstance(current_sheet, BeautifulSoup):
            rows = current_sheet.find_all('table:table-row')
            #not ignore first row
            return rows[0:]
        else:
            console.print(f"[bold red]current_sheet is not a BeautifulSoup object for sheet {sheet_name}")
            return None


    def get_columns_in_row(self, row):
        ret_cells = []
        cells = row.find_all('table:table-cell')
        for cell in cells:
            cell_value = self.process_text(cell)

            if cell.has_attr('table:number-columns-repeated'):
                num_repeate = 0
                try:
                    num_repeate = int(cell['table:number-columns-repeated'])
                except ValueError:
                    console.print('[bold red]failed to parse repeated cell under', cell)
                for _ in range(num_repeate - 1):
                    ret_cells.append(cell_value)
            ret_cells.append(cell_value)
        return ret_cells


    def process_text(self, cell):
        '''tex process for each column go here'''

        p_texts = cell.find_all('text:p')
        if p_texts is None:
            return ''

        ret_str = ''
        for p_text in p_texts:
            styled_texts = p_text.find_all('text:span')
            for styled_text in styled_texts:
                # Check if styled_text.string is not None
                if styled_text.string is not None:  
                #find bold styles and replace with b tag
                    if styled_text.has_attr('text:style-name'):
                        if styled_text['text:style-name'] in self.bold_names:
                            new_b_tag = self.soup.new_tag('b')
                            new_b_tag.string = styled_text.string
                            styled_text.replace_with(new_b_tag)
                        else:
                            styled_text.replace_with(styled_text.string)
                    else:
                        styled_text.replace_with(styled_text.string)

            #implement for <text:s text:c="5"> //5 spaces
            styled_texts = p_text.find_all('text:s')
            for styled_text in styled_texts:
                if styled_text.has_attr('text:c'):
                    styled_text.replace_with(' '*int(styled_text['text:c']))
                else:
                    styled_text.replace_with(' ')

            #convert tags to text
            ret_str += ''.join([str(it) for it in p_text.contents]) + '<br/>'

        return ret_str.removesuffix('<br/>')


if __name__ == '__main__':
    tic()
    sheet_name = "PALI"

    console.print(f"[bold bright_yellow]converting {dpspth.dps_path} to csv")
    a = ReadOds(dpspth.dps_path, {sheet_name})
    a.save_csv()
    toc()

