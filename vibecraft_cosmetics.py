"""VibeCraft cosmetic PNG validation and local texture import."""
from pathlib import Path
from PIL import Image
import shutil

class CosmeticError(ValueError):
    pass

def can_use_custom_cape(user):
    return bool(user and (user.get("role") in {"moderator", "owner"} or float(user.get("hours", 0)) >= 25))

def import_texture(source, minecraft_dir, kind):
    source = Path(source)
    if kind not in {"skin", "cape", "elytra"}:
        raise CosmeticError("Неизвестный тип косметики.")
    if not source.is_file() or source.suffix.lower() != ".png":
        raise CosmeticError("Выбери существующий PNG-файл.")
    try:
        with Image.open(source) as image:
            if image.format != "PNG":
                raise CosmeticError("Файл должен быть настоящим PNG.")
            image.load()
            if image.width > 4096 or image.height > 4096:
                raise CosmeticError("Слишком большое изображение. Максимум 4096×4096.")
            image = image.convert("RGBA")
            if kind == "skin":
                # Minecraft Java uses 64x64 (modern) or 64x32 (legacy) skins.
                if image.size not in {(64, 64), (64, 32)}:
                    # Accept common larger skin templates and normalize them.
                    if image.width == image.height:
                        image = image.resize((64, 64), Image.Resampling.NEAREST)
                    elif image.width == image.height * 2:
                        image = image.resize((64, 32), Image.Resampling.NEAREST)
                    else:
                        raise CosmeticError(f"Неподходящий размер скина {image.width}×{image.height}. Нужен квадратный PNG (например 64×64 или 128×128) либо 64×32.")
            elif image.size != (64, 32):
                raise CosmeticError(f"Для {kind} нужен PNG 64×32, получен {image.width}×{image.height}.")
            folder = Path(minecraft_dir) / f"vibecraft_{kind}s"
            folder.mkdir(parents=True, exist_ok=True)
            target = folder / f"selected_{kind}.png"
            image.save(target, format="PNG", optimize=True)
            return target
    except CosmeticError:
        raise
    except Exception as exc:
        raise CosmeticError(f"PNG не читается: {exc}") from exc
