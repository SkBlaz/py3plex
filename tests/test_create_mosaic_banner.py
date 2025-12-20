from pathlib import Path

import matplotlib
from PIL import Image

# Use a non-interactive backend suitable for headless test environments
matplotlib.use("Agg")

import create_mosaic_banner as cmb  # noqa: E402


MOSAIC_IMAGES = [
    "multilayer.png",
    "multilayer_edge_projection_spring.png",
    "multilayer_flow.png",
    "multilayer_radial_with_inter.png",
    "multilayer_supra_heatmap_inter.png",
    "hairball.png",
    "communities.png",
    "embedding.png",
    "temporal.png",
]

SHOWCASE_IMAGES = [
    "multilayer.png",
    "multilayer_edge_projection_spring.png",
    "multilayer_small_multiples_shared.png",
    "communities.png",
    "embedding.png",
    "multilayer_flow.png",
    "multilayer_supra_heatmap_inter.png",
    "hairball.png",
    "temporal.png",
    "multilayer_ego_circular.png",
    "multilayer_radial_compact.png",
    "networkx_wrapper.png",
    "spreading.png",
    "part1.png",
    "part2.png",
]

ALL_IMAGES = sorted(set(MOSAIC_IMAGES + SHOWCASE_IMAGES))


def _create_placeholder_images(base_dir: Path, names):
    base_dir.mkdir(parents=True, exist_ok=True)
    for idx, name in enumerate(names):
        color = (idx % 255, (idx * 3) % 255, (idx * 7) % 255)
        Image.new("RGB", (10, 6), color).save(base_dir / name)


def test_load_and_resize_image_respects_aspect_ratio(tmp_path):
    img_path = tmp_path / "orig.png"
    Image.new("RGB", (20, 10), "red").save(img_path)

    resized_h = cmb.load_and_resize_image(str(img_path), target_height=5)
    resized_w = cmb.load_and_resize_image(str(img_path), target_width=4)

    assert resized_h.shape == (5, 10, 3)
    assert resized_w.shape == (2, 4, 3)


def test_load_and_resize_image_supports_explicit_dimensions(tmp_path):
    img_path = tmp_path / "orig.png"
    Image.new("RGB", (6, 4), "blue").save(img_path)

    original = cmb.load_and_resize_image(str(img_path))
    resized = cmb.load_and_resize_image(str(img_path), target_height=8, target_width=10)

    assert original.shape == (4, 6, 3)
    assert resized.shape == (8, 10, 3)


def test_load_and_resize_image_returns_none_and_logs_error(tmp_path, capsys):
    missing = tmp_path / "missing.png"

    result = cmb.load_and_resize_image(str(missing), target_height=5)
    out = capsys.readouterr().out

    assert result is None
    assert f"Error loading {missing}" in out


def test_create_mosaic_banner_writes_png_in_custom_base_dir(tmp_path, capsys):
    _create_placeholder_images(tmp_path, MOSAIC_IMAGES)

    output_path = Path(cmb.create_mosaic_banner(base_dir=str(tmp_path)))
    out = capsys.readouterr().out

    assert output_path == tmp_path / "py3plex_mosaic_banner.png"
    assert output_path.exists() and output_path.stat().st_size > 0
    assert "Warning" not in out


def test_create_mosaic_banner_recovers_from_corrupt_image(tmp_path, capsys):
    _create_placeholder_images(tmp_path, MOSAIC_IMAGES)

    corrupt_file = tmp_path / MOSAIC_IMAGES[0]
    corrupt_file.write_text("not an image payload")

    output_path = Path(cmb.create_mosaic_banner(base_dir=str(tmp_path)))
    out = capsys.readouterr().out

    assert output_path.exists() and output_path.stat().st_size > 0
    assert f"Error processing {corrupt_file}" in out


def test_create_compact_banner_warns_when_images_missing(tmp_path, capsys):
    _create_placeholder_images(tmp_path, ["multilayer.png"])

    output_path = Path(cmb.create_compact_banner(base_dir=str(tmp_path)))
    out = capsys.readouterr().out

    assert output_path.exists() and output_path.stat().st_size > 0
    assert "not found, skipping" in out


def test_create_showcase_collage_succeeds_with_all_images(tmp_path, capsys):
    _create_placeholder_images(tmp_path, ALL_IMAGES)

    output_path = Path(cmb.create_showcase_collage(base_dir=str(tmp_path)))
    out = capsys.readouterr().out

    assert output_path == tmp_path / "py3plex_showcase.png"
    assert output_path.exists() and output_path.stat().st_size > 0
    assert "Warning" not in out


def test_create_showcase_collage_warns_when_images_missing(tmp_path, capsys):
    # No images provided -> every slot should warn and still produce an output
    output_path = Path(cmb.create_showcase_collage(base_dir=str(tmp_path)))
    out = capsys.readouterr().out

    assert output_path.exists() and output_path.stat().st_size > 0
    assert "not found, skipping" in out
