# EDOAL-2-CSV
As EDOAL Alignments can be challenging to read and process by humans, this small tool aims to convert EDOAL alignments into a human-friendly CSV files.
The EDOAL alignment elements are divided into columns, having each line represent a mapping. The columns include the list of single entities involved in a complex entity expression, an external constructor (AND, OR, COMPOSE), mapping relationship and mapping score. It also includes columns with the type of entities involved (class or property) and whether the mapping is complex, for filtering purposes. 

![Screenshot 2021-10-04 at 23 01 35](https://user-images.githubusercontent.com/43668147/135930746-c40677f5-287f-4860-9783-900a21f544e4.png)

This tool also implements evaluation methods based on direct comparison of table cells in order to find exact matches between two alignments (usually reference and candidate alignment), but also the mappings that were missing in the candidate alignment, which facilitates an overview analysis of the results when assessing performance in terms of precision and recall, respectively.

Check the tutorial python notebook for more information on how to use the tool.

## Authors
- Beatriz Lima

## License
See the LICENSE file for details.

## Acknowledgements
BL is funded by the FCT through LASIGE Research Unit, ref. UIDB/00408/2020 and ref. UIDP/00408/2020, and by projects SMILAX (ref. PTDC/EEI-ESS/4633/2014).
