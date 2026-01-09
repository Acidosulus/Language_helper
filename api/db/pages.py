from sqlalchemy import select
from sqlalchemy.orm import Session
from db import models, users


async def get_start_page(db: Session, user_name: str):
    ln_user_id = users.get_user_id(db, user_name)

    def _to_str(val):
        return "None" if val is None else str(val)

    def _get_tiles_for_row(row_id: int) -> list[dict]:
        tiles = (
            db.query(
                models.Tile,
                models.RowTile.id,
                models.RowTile.row_id,
                models.RowTile.tile_index,
            )
            .join(models.RowTile, models.RowTile.tile_id == models.Tile.tile_id)
            .filter(
                models.RowTile.user_id == ln_user_id,
                models.RowTile.row_id == row_id,
            )
            .order_by(models.RowTile.tile_index)
            .all()
        )
        out = []
        for tile_obj, rt_id, rt_row_id, rt_index in tiles:
            out.append(
                {
                    "tile_id": _to_str(tile_obj.tile_id),
                    "user_id": _to_str(tile_obj.user_id),
                    "name": _to_str(tile_obj.name),
                    "hyperlink": _to_str(tile_obj.hyperlink),
                    "onclick": _to_str(tile_obj.onclick),
                    "icon": _to_str(tile_obj.icon),
                    "color": _to_str(tile_obj.color),
                    "id": _to_str(rt_id),
                    "row_id": _to_str(rt_row_id),
                    "tile_index": _to_str(rt_index),
                }
            )
        return out

    # Page (по образцу page_id == 1)
    page = (
        db.query(models.Page)
        .filter(models.Page.user_id == ln_user_id, models.Page.page_id == 1)
        .first()
    )
    if not page:
        return {}

    result = {
        "page_id": _to_str(page.page_id),
        "user_id": _to_str(page.user_id),
        "page_name": _to_str(page.page_name),
        "index": _to_str(page.index),
        "default": _to_str(page.default),
        "rows": [],
    }

    # Rows для этой страницы (порядок по PageRows.row_index)
    rows = (
        db.query(models.Row, models.PageRows.row_index)
        .join(models.PageRows, models.PageRows.row_id == models.Row.row_id)
        .filter(
            models.Row.user_id == ln_user_id,
            models.PageRows.user_id == ln_user_id,
            models.PageRows.page_id == page.page_id,
        )
        .order_by(models.PageRows.row_index)
        .all()
    )

    for row_obj, _row_order in rows:
        result["rows"].append(
            {
                "row_id": _to_str(row_obj.row_id),
                "user_id": _to_str(row_obj.user_id),
                "row_name": _to_str(row_obj.row_name),
                "row_type": _to_str(row_obj.row_type),
                # В образце row_index = "0". Беру из модели Row.row_index.
                # Если нужно именно позицию в странице — можно подставить _row_order.
                "row_index": _to_str(row_obj.row_index),
                "tiles": _get_tiles_for_row(row_obj.row_id),
            }
        )

    return result


async def get_icon(
    db: Session,
    file_name: str,
) -> tuple[bytes, str, "datetime | None"]:
    result = db.execute(
        select(models.UserIcon).where(models.UserIcon.filename == file_name)
    )
    icon = result.scalar_one_or_none()
    if icon:
        return (
            icon.image,
            icon.content_type,
            icon.created_at,
        )
    else:
        return (
            None,
            None,
            None,
        )


# ----- Mutations for tiles -----
def create_tile(db: Session, user_name: str, *, row_id: int, tile_index: int, name: str, hyperlink: str | None, onclick: str | None, icon: str | None, color: str | None) -> models.Tile:
    user_id = users.get_user_id(db, user_name)
    if not user_id:
        raise ValueError("User not found")

    # Create tile record
    tile = models.Tile(
        user_id=user_id,
        name=name,
        hyperlink=hyperlink,
        onclick=onclick,
        icon=icon,
        color=color,
    )
    db.add(tile)
    db.flush()  # get tile_id

    # Attach to row with specified index
    rt = models.RowTile(
        row_id=row_id,
        tile_id=tile.tile_id,
        tile_index=tile_index,
        user_id=user_id,
    )
    db.add(rt)
    return tile


def update_tile(db: Session, user_name: str, *, tile_id: int, name: str | None = None, hyperlink: str | None = None, onclick: str | None = None, icon: str | None = None, color: str | None = None) -> models.Tile:
    user_id = users.get_user_id(db, user_name)
    if not user_id:
        raise ValueError("User not found")
    tile = db.query(models.Tile).filter(models.Tile.tile_id == tile_id, models.Tile.user_id == user_id).first()
    if not tile:
        raise ValueError("Tile not found")
    if name is not None:
        tile.name = name
    if hyperlink is not None:
        tile.hyperlink = hyperlink
    if onclick is not None:
        tile.onclick = onclick
    if icon is not None:
        tile.icon = icon
    if color is not None:
        tile.color = color
    db.add(tile)
    return tile


def delete_tile(db: Session, user_name: str, *, tile_id: int) -> None:
    user_id = users.get_user_id(db, user_name)
    if not user_id:
        raise ValueError("User not found")
    # Remove row links first
    db.query(models.RowTile).filter(models.RowTile.user_id == user_id, models.RowTile.tile_id == tile_id).delete()
    # Remove tile
    db.query(models.Tile).filter(models.Tile.user_id == user_id, models.Tile.tile_id == tile_id).delete()


def set_row_tile_index(db: Session, user_name: str, *, row_id: int, tile_id: int, tile_index: int) -> None:
    user_id = users.get_user_id(db, user_name)
    if not user_id:
        raise ValueError("User not found")
    # Ensure a tile belongs to only one row for this user: delete other links
    db.query(models.RowTile).filter(
        models.RowTile.user_id == user_id,
        models.RowTile.tile_id == tile_id,
        models.RowTile.row_id != row_id,
    ).delete()

    rt = (
        db.query(models.RowTile)
        .filter(
            models.RowTile.user_id == user_id,
            models.RowTile.row_id == row_id,
            models.RowTile.tile_id == tile_id,
        )
        .first()
    )
    if not rt:
        rt = models.RowTile(
            row_id=row_id,
            tile_id=tile_id,
            user_id=user_id,
            tile_index=tile_index,
        )
        db.add(rt)
    else:
        rt.tile_index = tile_index
        db.add(rt)


def create_row(db: Session, user_name: str, *, row_name: str, row_type: int = 0, row_index: int = 0, page_id: int = 1) -> models.Row:
    user_id = users.get_user_id(db, user_name)
    if not user_id:
        raise ValueError("User not found")
    # Create row
    row = models.Row(user_id=user_id, row_name=row_name, row_type=row_type, row_index=row_index)
    db.add(row)
    db.flush()
    # Attach to page
    pr = models.PageRows(page_id=page_id, row_id=row.row_id, row_index=row_index, user_id=user_id)
    db.add(pr)
    return row


def delete_row(db: Session, user_name: str, *, row_id: int) -> None:
    user_id = users.get_user_id(db, user_name)
    if not user_id:
        raise ValueError("User not found")
    # Remove all tiles bindings inside this row
    db.query(models.RowTile).filter(models.RowTile.user_id == user_id, models.RowTile.row_id == row_id).delete()
    # Remove page-row mapping
    db.query(models.PageRows).filter(models.PageRows.user_id == user_id, models.PageRows.row_id == row_id).delete()
    # Remove the row
    db.query(models.Row).filter(models.Row.user_id == user_id, models.Row.row_id == row_id).delete()


def save_icon(db: Session, *, filename: str, content_type: str, data: bytes) -> models.UserIcon:
    # Upsert by filename
    existing = db.execute(select(models.UserIcon).where(models.UserIcon.filename == filename)).scalar_one_or_none()
    if existing:
        existing.content_type = content_type
        existing.image = data
        db.add(existing)
        return existing
    icon = models.UserIcon(filename=filename, content_type=content_type, image=data)
    db.add(icon)
    return icon
