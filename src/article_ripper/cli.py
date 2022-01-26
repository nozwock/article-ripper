import click


@click.command()
@click.option("--url")
@click.option("--out", default="out.md")
def cli(url, out):
    click.echo("Hey ✨")
# ! Pending


if __name__ == "__main__":
    cli()
