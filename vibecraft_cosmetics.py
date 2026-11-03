"""VibeCraft cosmetic PNG validation and rank rules. Rendering requires a game mod."""
from pathlib import Path
from PIL import Image
import shutil
class CosmeticError(ValueError): pass
def can_use_custom_cape(user):
    # VibeCraft 2.2: custom capes are free for every local profile.
    return True
def import_texture(source, minecraft_dir, kind):
    source=Path(source)
    if kind not in {"skin","cape","elytra"}: raise CosmeticError("Неизвестный тип косметики.")
    if not source.is_file() or source.suffix.lower() != ".png": raise CosmeticError("Выбери существующий PNG-файл.")
    try:
        with Image.open(source) as im: im.verify()
        with Image.open(source) as im: size=im.size; fmt=im.format
    except Exception as exc: raise CosmeticError(f"PNG не читается: {exc}") from exc
    allowed={(64,64),(64,32)} if kind=="skin" else {(64,32)}
    if fmt!="PNG" or size not in allowed:
        expected="64×64 или 64×32" if kind=="skin" else "64×32"
        raise CosmeticError(f"Нужен PNG {expected}; получен {size[0]}×{size[1]}.")
    folder=Path(minecraft_dir)/f"vibecraft_{kind}s"; folder.mkdir(parents=True,exist_ok=True)
    target=folder/f"selected_{kind}.png"; shutil.copy2(source,target); return target
