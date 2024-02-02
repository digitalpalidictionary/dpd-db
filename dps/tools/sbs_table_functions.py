"""Functions for properties in SBS table"""

import csv
import os

from dps.tools.paths_dps import DPSPaths

dpspth = DPSPaths()

class SBS_table_tools:
    def load_chant_index_map(self):
        """Load the chant-index mapping from a TSV file into a dictionary."""
        chant_index_map = {}
        with open(dpspth.sbs_index_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            next(reader)  # Skip header row
            for row in reader:
                index, chant = row[0], row[1]
                chant_index_map[chant] = int(index)
        return chant_index_map


    def load_chant_link_map(self):
        """Load the chant-link mapping from a TSV file into a dictionary."""
        chant_link_map = {}
        with open(dpspth.sbs_index_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            next(reader)  # Skip header row
            for row in reader:
                chant, link = row[1], row[4]
                chant_link_map[chant] = link
        return chant_link_map


    def load_class_link_map(self):
        """Load the class-link mapping from a TSV file into a dictionary."""
        class_link_map = {}
        with open(dpspth.class_index_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            next(reader)  # Skip header row
            for row in reader:
                class_num, link = int(row[0]), row[2]  # Convert class_num to integer
                class_link_map[class_num] = link
        return class_link_map


    def load_sutta_link_map(self):
        """Load the sutta-link mapping from a TSV file into a dictionary."""
        sutta_link_map = {}
        with open(dpspth.sutta_index_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            next(reader)  # Skip header row
            for row in reader:
                sutta_num, link = row[0], row[2]
                sutta_link_map[sutta_num] = link
        return sutta_link_map

    
    def generate_sbs_audio(self, pali_clean):
        """Generate the sbs_audio string based on the presence of an audio file."""
        if dpspth.anki_media_dir:
            audio_path = os.path.join(dpspth.anki_media_dir, f"{pali_clean}.mp3")
            if os.path.exists(audio_path):
                return f"[sound:{pali_clean}.mp3]"
        return ''
