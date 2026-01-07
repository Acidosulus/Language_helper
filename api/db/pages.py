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
