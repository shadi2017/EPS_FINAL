import tempfile
import unittest
from pathlib import Path
import pandas as pd
from PIL import Image
from eps_studio.core import (safe_name, open_image, prepare_frame, frame_photo,
    export_certificates, export_photos, render_certificate, TextStyle, default_font, read_table)

class ProductionTests(unittest.TestCase):
    def test_reserved_names(self):
        self.assertEqual(safe_name("CON"),"record_CON")
        self.assertNotIn("/",safe_name("a/b"))
        self.assertTrue(safe_name("..."))

    def test_table_empty_rows_and_leading_zero(self):
        frame = read_table(b"name,id\nAli,001\n,\n", ".csv")
        self.assertEqual(len(frame),1)
        self.assertEqual(frame.iloc[0]["id"],"001")

    def test_duplicate_and_missing_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = pd.DataFrame({"name":["أحمد", "أحمد", ""]})
            renderer = lambda row: render_certificate(Image.new("RGB",(300,200),"white"),row["name"],TextStyle(size=24),default_font())
            folder, records = export_certificates(data,"name",renderer,tmp)
            self.assertEqual([r["status"] for r in records],["success","success","skipped"])
            self.assertEqual(len(list(folder.glob("*.jpg"))),2)
            self.assertTrue((folder/"certificates.pdf").read_bytes().startswith(b"%PDF"))
            other, _ = export_certificates(data,"name",renderer,tmp,False)
            self.assertNotEqual(folder,other)

    def test_frame_and_corrupt_photo_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            good=root/"photo.png"
            bad=root/"broken.jpg"
            Image.new("RGB",(120,80),"red").save(good)
            bad.write_text("broken")
            frame=Image.new("RGBA",(120,80),(0,0,0,0))
            folder,records=export_photos([bad,good],{"landscape":frame},root,max_edge=60)
            self.assertEqual([r["status"] for r in records],["failed","success"])
            output=folder/records[1]["output"]
            self.assertEqual(output.suffix,".jpg")
            with Image.open(output) as image:
                self.assertEqual(image.size,(60,40))
                self.assertEqual(image.format,"JPEG")
            self.assertEqual(open_image(good).size,(120,80))

    def test_exif_orientation(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"rotated.jpg"
            image=Image.new("RGB",(80,120))
            exif=Image.Exif()
            exif[274]=6
            image.save(target,exif=exif)
            self.assertEqual(open_image(target).size,(120,80))

    def test_transparent_frame_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"frame.png"
            image=Image.new("RGBA",(30,30),(0,0,0,0))
            image.putpixel((0,0),(0,0,255,255))
            image.save(target)
            frame=prepare_frame(target)
            self.assertEqual(frame.getpixel((0,0)),(0,0,255,255))
            self.assertEqual(frame_photo(Image.new("RGBA",(30,30),"red"),frame).getpixel((15,15)),(255,0,0))

if __name__ == "__main__":
    unittest.main()
