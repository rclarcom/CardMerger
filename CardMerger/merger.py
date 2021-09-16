import glob
import logging
import os
import pprint
import re
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Callable, Collection, Dict, List, Optional, Tuple

import PyPDF2 as pdf
import PyPDF2.generic

logger = logging.getLogger(__name__)

spell_file_prefix_re = re.compile("^\d*_")
monster_file_suffix_re = re.compile("\s*\([LS]\)$")


class PaperSize(Enum):
    # In 'PDF units', 72 PPI
    LETTER = (612, 792)
    LEGAL = (612, 1008)
    A4 = (595, 842)


MIN_LEFT_MARGIN = 18  # 0.25 in. margin
MIN_RIGHT_MARGIN = 18
MIN_TOP_MARGIN = 18
MIN_BOTTOM_MARGIN = 36  # 0.5 in. margin for letter bottom


def extract_spell_name(spell_path: str):
    """
    Extract a spell name if possible from the path to a spell card file.  Handles the Matthew Perkins 5e Spell Card
    Individual archive naming convention by:
    - returning None for files that begin with '!' or are not .pdfs
    - stripping the leading number + underscore

    :param spell_path: path to a potential individual spell card .pdf file
    :return: the spell name in lowercase, or None
    """
    file_name, ext = os.path.splitext(os.path.basename(spell_path))

    if ext != ".pdf" or file_name.startswith("!"):
        return None

    return spell_file_prefix_re.sub("", file_name).lower()


def extract_monster_name(monster_path: str):
    """
    Extract a monster name if possible from the path to a monster card file.  Handles the Matthew Perkins 5e Monster
    Card Individual archive naming convention by:
    - returning None for files that begin with '!' or are not .pdfs
    - stripping the trailing (Size) designator

    :param monster_path: path to a potential individual monster card .pdf file
    :return: the monster name in lowercase, or None
    """
    file_name, ext = os.path.splitext(os.path.basename(monster_path))

    if ext != ".pdf" or file_name.startswith("!"):
        return None

    return monster_file_suffix_re.sub("", file_name).lower()


def extract_card_name(card_path: str):
    """
    Extract a card name if possible from the path to a file.
    - returning None for files that begin with '!' or are not .pdfs

    :param card_path: path to a potential individual card .pdf file
    :return: the card name in lowercase, or None
    """
    file_name, ext = os.path.splitext(os.path.basename(card_path))

    if ext != ".pdf" or file_name.startswith("!"):
        return None

    return file_name.lower()


@dataclass()
class CardInfo:
    path_to_pdf: str
    card_size: Tuple[Decimal, Decimal]  # (W,H)


def make_card_info(path_to_pdf: str) -> Optional[CardInfo]:
    file_reader = pdf.PdfFileReader(open(path_to_pdf, "rb"))
    if file_reader.getNumPages() != 1:
        return None

    card_page = file_reader.getPage(0)
    card_size = (
        card_page.mediaBox.getWidth(),
        card_page.mediaBox.getHeight(),
    )

    return CardInfo(path_to_pdf, card_size)


@dataclass()
class PageLayout:
    paper_size: Tuple[int, int]
    cards_per_page: int
    card_rows: int
    card_cols: int
    card_height: Decimal
    card_width: Decimal
    card_scale: Decimal
    left_margin: Decimal
    bottom_margin: Decimal


class CardMerger:
    def __init__(
        self,
        path_to_card_pdfs: str,
        name_filter: Callable[[str], str] = extract_card_name,
    ):
        """
        Configure the CardMerger given a path to a directory containing individual card pdfs.

        :param path_to_card_pdfs: directory containing individual card pdfs
        :param name_filter: filter to extract card names from pdf file name
        """
        self.paper_size = PaperSize.LETTER
        self.name_filter = name_filter
        self.card_dict: Dict[str:CardInfo] = {}
        self.card_scale = Decimal(1.0)

        self.create_card_pdf_dict(path_to_card_pdfs)

    def create_card_pdf_dict(self, path_to_pdf_directory: str):
        """
        Create a card lookup dict given a path to a directory containing card pdfs.

        This will also configure layout based on the size of cards in the directory.

        :param path_to_pdf_directory: a directory containing individual card files.
        :return:
        """
        card_names = {
            card_name: card_path
            for card_path in glob.iglob(f"{path_to_pdf_directory}/*.pdf")
            for card_name in [self.name_filter(card_path)]
            if card_name
        }

        self.card_dict = {
            card_name: card_info
            for card_name, card_path in card_names.items()
            for card_info in [make_card_info(card_path)]
            if card_info
        }

    def determine_page_layout(
        self, original_card_size: Tuple[Decimal, Decimal]
    ) -> Optional[PageLayout]:
        """
        Create a layout for same sized cards arranged on a page.  If cards will not fit, returns None

        Cards will be laid out to fit the maximum number (with configured scaling) on the configured paper size.

        :param original_card_size: (Width, Height) original size of cards.
        :return: The optimal layout for merging cards of this size
        """
        scaled_card_width = self.card_scale * original_card_size[0]
        scaled_card_height = self.card_scale * original_card_size[1]

        # Evaluate without rotation
        card_cols_portrait = int(
            (self.paper_size.value[0] - MIN_LEFT_MARGIN - MIN_RIGHT_MARGIN)
            / scaled_card_width
        )
        card_rows_portrait = int(
            (self.paper_size.value[1] - MIN_TOP_MARGIN - MIN_BOTTOM_MARGIN)
            / scaled_card_height
        )

        # Evaluate landscape paper layout
        card_rows_landscape = int(
            (self.paper_size.value[0] - MIN_LEFT_MARGIN - MIN_RIGHT_MARGIN)
            / scaled_card_height
        )
        card_cols_landscape = int(
            (self.paper_size.value[1] - MIN_TOP_MARGIN - MIN_BOTTOM_MARGIN)
            / scaled_card_width
        )

        if (
            card_cols_landscape * card_rows_landscape
            > card_cols_portrait * card_rows_portrait
        ):
            use_landscape = True
            card_cols = card_cols_landscape
            card_rows = card_rows_landscape
        else:
            use_landscape = False
            card_cols = card_cols_portrait
            card_rows = card_rows_portrait

        if card_cols < 1 or card_rows < 1:
            logger.error(
                f"Paper size {self.paper_size.value} too small for card size {original_card_size} "
                f"at scale {self.card_scale}"
            )
            return None

        # Set margins to center cards on page
        if use_landscape:
            paper_size = (self.paper_size.value[1], self.paper_size.value[0])

            excess_vertical_margin = (
                self.paper_size.value[0]
                - MIN_LEFT_MARGIN
                - MIN_RIGHT_MARGIN
                - scaled_card_height * card_rows
            )
            bottom_margin = MIN_LEFT_MARGIN + excess_vertical_margin / 2

            excess_horizontal_margin = (
                self.paper_size.value[1]
                - MIN_TOP_MARGIN
                - MIN_BOTTOM_MARGIN
                - scaled_card_width * card_cols
            )
            left_margin = MIN_TOP_MARGIN + excess_horizontal_margin / 2
        else:
            paper_size = self.paper_size.value

            excess_horizontal_margin = (
                self.paper_size.value[0]
                - MIN_LEFT_MARGIN
                - MIN_RIGHT_MARGIN
                - scaled_card_width * card_cols
            )
            left_margin = MIN_LEFT_MARGIN + excess_horizontal_margin / 2
            excess_vertical_margin = (
                self.paper_size.value[1]
                - MIN_TOP_MARGIN
                - MIN_BOTTOM_MARGIN
                - scaled_card_height * card_rows
            )
            bottom_margin = MIN_BOTTOM_MARGIN + excess_vertical_margin / 2

        return PageLayout(
            paper_size=paper_size,
            cards_per_page=card_rows * card_cols,
            card_rows=card_rows,
            card_cols=card_cols,
            card_height=scaled_card_height,
            card_width=scaled_card_width,
            card_scale=self.card_scale,
            left_margin=left_margin,
            bottom_margin=bottom_margin,
        )

    def group_cards_by_sizes(self, cards: Collection[str]) -> List[List[CardInfo]]:
        """
        Divide the provided set of cards into lists of same-sized cards

        :param cards: a vetted (all present in card_dict) set of cards to group
        :return: List of same-sized card lists
        """
        card_infos = [self.card_dict[card] for card in cards]
        card_sizes = {card_info.card_size for card_info in card_infos}
        grouped_cards = [
            [card_info for card_info in card_infos if card_info.card_size == size]
            for size in card_sizes
        ]
        return grouped_cards

    def create_cards_file(self, path_to_card_list: str):
        """
        Create a .pdf file containing all cards listed in a .txt list.  The pdf will be created in the
        same directory as the card list and with the same basename.  One card per line.

        Card names are evaluated without capitalization (.lower()).

        :param path_to_card_list: Path to the .txt card list
        :return:
        """
        list_base_name, ext = os.path.splitext(path_to_card_list)
        if ext != ".txt":
            logger.error(f"Card list must be .txt file.  Quitting.")
            return

        if not os.path.isfile(path_to_card_list):
            logger.error(f"Could not find card list {path_to_card_list}.  Quitting.")
            return

        pdf_name = list_base_name + ".pdf"

        with open(path_to_card_list) as f:
            card_set = {
                line.rstrip().lower()
                for line in f
                if not line.startswith(("!", "#", "/")) and not line.isspace()
            }

        known_cards = card_set & self.card_dict.keys()

        unknown_cards = card_set - self.card_dict.keys()

        if unknown_cards:
            logger.warning(f"Could not find the following {len(unknown_cards)} cards:")
            logger.warning(pprint.pformat(unknown_cards))

        if len(known_cards) == 0:
            logger.error(f"No known cards.  Quitting.")
            return

        grouped_cards = self.group_cards_by_sizes(known_cards)

        pdf_writer = pdf.PdfFileWriter()

        for card_group in grouped_cards:
            original_card_size = card_group[0].card_size
            page_layout = self.determine_page_layout(original_card_size)

            for card_ct, card in enumerate(card_group):
                page_position = card_ct % page_layout.cards_per_page
                row_no = page_position // page_layout.card_cols
                col_no = page_position % page_layout.card_cols

                if page_position == 0:
                    current_page = pdf_writer.addBlankPage(
                        width=page_layout.paper_size[0],
                        height=page_layout.paper_size[1],
                    )

                card_page = pdf.PdfFileReader(open(card.path_to_pdf, "rb")).getPage(0)

                tx = page_layout.left_margin + col_no * page_layout.card_width
                ty = page_layout.bottom_margin + row_no * page_layout.card_height
                rotation = 0

                # Fix offsets of any annotations (Generating new cards from editable templates creates annotations)
                if "/Annots" in card_page:
                    for annot_indirect in card_page.get("/Annots").getObject():
                        annot = annot_indirect.getObject()
                        if "/Rect" in annot:
                            bounding_rect = annot["/Rect"].getObject()

                            annot.update(
                                {
                                    PyPDF2.generic.NameObject(
                                        "/Open"
                                    ): PyPDF2.generic.BooleanObject(False),
                                    PyPDF2.generic.NameObject(
                                        "/Rect"
                                    ): PyPDF2.generic.RectangleObject(
                                        [
                                            bounding_rect[0] + tx,
                                            bounding_rect[1] + ty,
                                            bounding_rect[2] + tx,
                                            bounding_rect[3] + ty,
                                        ]
                                    ),
                                }
                            )

                current_page.mergeRotatedScaledTranslatedPage(
                    card_page,
                    rotation=rotation,
                    scale=page_layout.card_scale,
                    tx=tx,
                    ty=ty,
                )

        with open(pdf_name, "wb") as out_stream:
            pdf_writer.write(out_stream)
