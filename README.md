# CardMerger

A simple command line utility for merging multiple single page card pdfs into a single pdf file for convenient printing.

In particular, this tool is intended to help printing the excellent D&D 5th Edition [Spell Cards](https://www.drivethrurpg.com/product/173582/DD-5th-Edition-Spell-Cards) 
and [Monster Cards](https://www.drivethrurpg.com/product/205572/DD-5th-Edition-Monster-Cards) by Matthew Perkins.

## Requirements

The tool requires a Python 3.7+ environment with the modules listed in `requirements.txt`.

Additionally, a directory containing appropriately named single card pdfs is required.  My recommendation is to purhcase the OGL cards from the link above, and extract
the individual cards .rar archive into the project folder.

An appopriate [card list](#Card-Lists) must be created for the pdf you want to create.

## Command Line Interface

Two primary commands are available, one for spell cards, one for monster cards.  The only significant difference between each is the ability to correctly strip monster
size suffixes or spell level prefixes from card file names.

Optionally, paper size can be set to something other than letter 8" x 11", and cards can be scaled larger or smaller.

### Spell Cards

Example command line:

```
python -m CardMerger.cli merge-spell-cards -l ./examples/Brutalitops_Spells.txt -d ./DD_5e_Spell_Cards_INDIVIDUAL
```

```
python -m CardMerger.cli merge-spell-cards [OPTIONS]

Options:
  -l, --spell-list TEXT           Path to list .txt file  [required]
  -d, --path-to-pdf-directory TEXT
                                  Directory containing individual pdf files
                                  [required]
  -s, --card-scale FLOAT          Card size scale factor  [default: 1.0]
  -p, --paper-size [LETTER|LEGAL|A4]
                                  [default: LETTER]
  --help                          Show this message and exit.
```

### Monster Cards

Example command line:

```
python -m CardMerger.cli merge-monster-cards -l ./examples/Caverns_of_Draconis.txt -d ./DD_5e_Monster_Cards_INDIVIDUAL
```

```
Usage: python -m CardMerger.cli merge-monster-cards [OPTIONS]

Options:
  -l, --monster-list TEXT         Path to list .txt file  [required]
  -d, --path-to-pdf-directory TEXT
                                  Directory containing individual pdf files.
                                  [required]
  -s, --card-scale FLOAT          Card size scale factor  [default: 1.0]
  -p, --paper-size [LETTER|LEGAL|A4]
                                  [default: LETTER]
  --help                          Show this message and exit.

```

## Card Lists

Card lists are simply text files listing the cards to assemble, with names matching the individual file names (sans prefixes/suffixes).
The list file can include comment lines beginning with '#'.

Example spell list for a 1st level wizard:

```
# Cantrips
dancing lights
minor illusion
mage hand
ray of frost

# L1
color spray
detect magic
grease
identify
mage armor
shield
```