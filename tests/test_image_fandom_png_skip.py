# Test for Fandom PNG skip logic in images_mismatch when resuming
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import builtins

from wikiteam3.dumpgenerator.dump.image.image import Image

class DummyConfig:
	api = "https://spongebob.fandom.com/api.php"
	path = "/tmp/testdump"

class DummyOtherConfig:
	image_timestamp_interval = None
	ia_wbm_booster = None
	hard_retries = 0

@pytest.fixture
def fandom_png_in_mismatch(tmp_path):
	# Setup test directory and file
	images_mismatch = tmp_path / "images_mismatch"
	images_mismatch.mkdir()
	png_name = "Test_Image.png"
	(images_mismatch / png_name).write_bytes(b"fakepngdata")
	return tmp_path, png_name

def test_fandom_png_skip(monkeypatch, fandom_png_in_mismatch, capsys):
	tmp_path, png_name = fandom_png_in_mismatch
	config = DummyConfig()
	config.path = str(tmp_path)
	other = DummyOtherConfig()
	# Fandom PNG in images_mismatch
	images = [[png_name, "https://static.wikia.nocookie.net/abcdefg/images/1/11/Test_Image.png?cb=20210101010101", "Uploader", "123", "fake_sha1", "2021-01-01T01:01:01Z"]]

	# Patch Path.is_file to return True only for the images_mismatch PNG
	orig_is_file = Path.is_file
	def is_file_patch(self):
		if str(self) == str(tmp_path / "images_mismatch" / png_name):
			return True
		return orig_is_file(self)
	monkeypatch.setattr(Path, "is_file", is_file_patch)

	# Patch print to capture output
	with patch.object(builtins, "print") as mock_print:
		# Should skip and not attempt download
		Image.generate_image_dump(config, other, images, MagicMock())
		# Check that skip message was printed
		found = False
		for call in mock_print.call_args_list:
			if f"Skipping Fandom PNG/JPG (already in images_mismatch): {png_name}" in str(call):
				found = True
		assert found, "Did not skip Fandom PNG in images_mismatch as expected"
