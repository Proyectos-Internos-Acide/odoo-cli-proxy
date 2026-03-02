#!/usr/bin/env python3
"""Upload user guides to Odoo Knowledge module.

Reads the markdown guide files, converts them to HTML, and uploads them
as Knowledge articles under a "Manuales" parent article (production).

Usage:
    uv run python business_units/hotel-trip-agency/guides/upload_guides.py
    uv run python business_units/hotel-trip-agency/guides/upload_guides.py --target prod
    uv run python business_units/hotel-trip-agency/guides/upload_guides.py --target test
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import typer
from odoo_cli import OdooClient

app = typer.Typer(help="Upload user guides to Odoo Knowledge")

GUIDES_DIR = os.path.dirname(os.path.abspath(__file__))

GUIDES = [
    {
        "file": "01_GUIA_VENTAS_TOURS.md",
        "name": "Venta de Paquetes Turísticos con Biblia Operativa",
        "icon": "📋",
        "sequence": 10,
    },
    {
        "file": "02_GUIA_HOSPEDAJE.md",
        "name": "Gestión de Reservas y Ventas de Hospedaje",
        "icon": "🏨",
        "sequence": 20,
    },
    {
        "file": "03_GUIA_ECOMMERCE.md",
        "name": "Gestión y Personalización del E-commerce",
        "icon": "🛒",
        "sequence": 30,
    },
    {
        "file": "SCREENSHOTS_CHECKLIST.md",
        "name": "Checklist de Capturas de Pantalla",
        "icon": "📸",
        "sequence": 40,
    },
]

PARENT_NAME = "Manuales"
PARENT_ICON = "📚"


def md_to_html(md_content: str) -> str:
    """Convert markdown to HTML body for Knowledge article."""
    try:
        import markdown
        return markdown.markdown(
            md_content,
            extensions=['tables', 'fenced_code', 'toc'],
        )
    except ImportError:
        import html as html_mod
        typer.echo("  ⚠ python-markdown no instalado, usando texto plano")
        typer.echo("    Instalar con: uv pip install markdown")
        return f"<pre>{html_mod.escape(md_content)}</pre>"


def get_client(target: str) -> OdooClient:
    """Create OdooClient for the specified target."""
    if target == "prod":
        url = os.getenv("TARGET_MIGRATION_URL")
        db = os.getenv("TARGET_MIGRATION_DB")
        user = os.getenv("TARGET_MIGRATION_USERNAME")
        pwd = os.getenv("TARGET_MIGRATION_PASSWORD")
        if not all([url, db, user, pwd]):
            typer.echo("❌ Missing TARGET_MIGRATION_* env vars for production")
            raise typer.Exit(1)
        return OdooClient(url=url, db=db, username=user, password=pwd)
    else:
        return OdooClient()


def ensure_parent_article(client, name: str, icon: str) -> int:
    """Find or create the parent Knowledge article. Returns article_id."""
    existing = client.search_read(
        'knowledge.article',
        domain=[['name', '=', name], ['parent_id', '=', False]],
        fields=['id', 'name'],
        limit=1,
    )
    if existing:
        typer.echo(f"  ✓ Artículo padre '{name}' ya existe (id={existing[0]['id']})")
        return existing[0]['id']

    article_id = client.execute('knowledge.article', 'create', [{
        'name': name,
        'icon': icon,
        'body': '<p>Guías de uso del sistema para el personal de A y F Destiny.</p>',
        'category': 'workspace',
        'internal_permission': 'write',
        'is_article_visible_by_everyone': True,
    }])
    if isinstance(article_id, list):
        article_id = article_id[0]

    # Add current user as member so articles are visible in sidebar
    user = client.search_read('res.users', [['id', '=', client.uid]], fields=['partner_id'], limit=1)
    partner_id = user[0]['partner_id'][0]
    client.execute('knowledge.article.member', 'create', [{
        'article_id': article_id,
        'partner_id': partner_id,
        'permission': 'write',
    }])

    typer.echo(f"  ✓ Artículo padre '{name}' creado (id={article_id})")
    return article_id


def upsert_article(client, parent_id: int, name: str, html_body: str, icon: str, sequence: int) -> int:
    """Create or update a Knowledge article under the parent."""
    existing = client.search_read(
        'knowledge.article',
        domain=[['name', '=', name], ['parent_id', '=', parent_id]],
        fields=['id'],
        limit=1,
    )

    if existing:
        article_id = existing[0]['id']
        client.execute('knowledge.article', 'write', [article_id], {
            'body': html_body,
            'icon': icon,
            'sequence': sequence,
        })
        typer.echo(f"  ✓ Actualizado: {icon} {name} (id={article_id})")
        return article_id

    article_id = client.execute('knowledge.article', 'create', [{
        'name': name,
        'parent_id': parent_id,
        'body': html_body,
        'icon': icon,
        'sequence': sequence,
        'category': 'workspace',
        'is_article_visible_by_everyone': True,
    }])
    if isinstance(article_id, list):
        article_id = article_id[0]
    typer.echo(f"  ✓ Creado: {icon} {name} (id={article_id})")
    return article_id


@app.command()
def upload(
    target: str = typer.Option("test", help="Target instance: 'test' or 'prod'"),
    dry_run: bool = typer.Option(False, help="Only convert to HTML, don't upload"),
):
    """Upload user guides as Knowledge articles."""
    typer.echo(f"\n📚 Subiendo guías a Knowledge ({target})\n")

    # Read and convert all guides
    converted = []
    for guide in GUIDES:
        filepath = os.path.join(GUIDES_DIR, guide["file"])
        if not os.path.exists(filepath):
            typer.echo(f"  ⚠ Archivo no encontrado: {guide['file']}")
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            md_content = f.read()

        html_body = md_to_html(md_content)
        converted.append({
            "name": guide["name"],
            "html": html_body,
            "icon": guide["icon"],
            "sequence": guide["sequence"],
            "file": guide["file"],
        })
        typer.echo(f"  ✓ Convertido: {guide['file']} ({len(md_content)} → {len(html_body)} chars)")

    if not converted:
        typer.echo("\n❌ No se encontraron guías.")
        raise typer.Exit(1)

    if dry_run:
        typer.echo(f"\n✅ Dry run: {len(converted)} guías convertidas (no subidas)")
        raise typer.Exit(0)

    # Connect to Odoo
    client = get_client(target)
    client.connect()
    typer.echo(f"  ✓ Conectado a Odoo ({target})\n")

    # Create parent article
    parent_id = ensure_parent_article(client, PARENT_NAME, PARENT_ICON)

    typer.echo(f"\n📤 Subiendo {len(converted)} artículos...\n")

    for item in converted:
        upsert_article(client, parent_id, item["name"], item["html"], item["icon"], item["sequence"])

    typer.echo(f"\n✅ {len(converted)} guías subidas a Knowledge")
    typer.echo(f"   Ubicación: Knowledge > {PARENT_ICON} {PARENT_NAME}")


if __name__ == "__main__":
    app()
