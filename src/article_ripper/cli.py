import click
from article_ripper.main import get_document, html_to_md


@click.command()
@click.option("--url")
@click.option("--out", default="out.md")
def cli(url, out):
    click.echo("Hey ✨")


if __name__ == "__main__":
    cli()
