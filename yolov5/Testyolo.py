import unittest
from detect import parse_opt, main

class TestYOLOv5Detection(unittest.TestCase):
    def test_parse_opt(self):
        args = ["--weights", "yolov5s.pt", "--source", "img.jpg"]
        opt = parse_opt()
        self.assertEqual(str(opt.weights), "yolov5s.pt")
        expected_source = "data\\images"
        self.assertEqual(str(opt.source), expected_source)

    def test_main(self):
        opt = parse_opt()
        self.assertIsNone(main(opt))

if __name__ == "__main__":
    unittest.main()
