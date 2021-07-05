from decimal import Decimal

import click

from CardMerger.merger import (
    CardMerger,
    PaperSize,
    extract_monster_name,
    extract_spell_name,
)


@click.group()
def MergeCards():
    pass


@MergeCards.command(name="merge-spell-cards")
@click.option("-l", "--spell-list", help="Path to list .txt file", required=True)
@click.option(
    "-d",
    "--path-to-pdf-directory",
    help="Directory containing individual pdf files",
    required=True,
)
@click.option(
    "-s",
    "--card-scale",
    type=float,
    default=1.0,
    help="Card size scale factor",
    show_default=True,
)
@click.option(
    "-p",
    "--paper-size",
    type=click.Choice(PaperSize.__members__),
    callback=lambda c, p, v: getattr(PaperSize, v) if v else None,
    default="LETTER",
    show_default=True,
)
def merge_spell_cards(
    spell_list: str,
    path_to_pdf_directory: str,
    card_scale: float,
    paper_size: PaperSize,
):
    print(f"Merging cards for: {spell_list}")
    print(f"Single spell pdfs at: {path_to_pdf_directory}")
    merger = CardMerger(
        path_to_card_pdfs=path_to_pdf_directory, name_filter=extract_spell_name
    )
    merger.card_scale = Decimal(card_scale)
    merger.paper_size = paper_size
    merger.create_cards_file(spell_list)


@MergeCards.command(name="merge-monster-cards")
@click.option("-l", "--monster-list", help="Path to list .txt file", required=True)
@click.option(
    "-d",
    "--path-to-pdf-directory",
    help="Directory containing individual pdf files.",
    required=True,
)
@click.option(
    "-s",
    "--card-scale",
    type=float,
    default=1.0,
    help="Card size scale factor",
    show_default=True,
)
@click.option(
    "-p",
    "--paper-size",
    type=click.Choice(PaperSize.__members__),
    callback=lambda c, p, v: getattr(PaperSize, v) if v else None,
    default="LETTER",
    show_default=True,
)
def merge_monster_cards(
    monster_list: str,
    path_to_pdf_directory: str,
    card_scale: float,
    paper_size: PaperSize,
):
    print(f"Merging cards for: {monster_list}")
    print(f"Single monster pdfs at: {path_to_pdf_directory}")
    merger = CardMerger(
        path_to_card_pdfs=path_to_pdf_directory, name_filter=extract_monster_name
    )
    merger.card_scale = Decimal(card_scale)
    merger.paper_size = paper_size
    merger.create_cards_file(monster_list)


if __name__ == "__main__":
    MergeCards()
