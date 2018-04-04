from __future__ import division, unicode_literals, absolute_import

import os
from tempfile import NamedTemporaryFile

from pillow_lut import Image, ImageFilter, load_cube_file, load_hald_image
from pillow_lut import loaders

from . import PillowTestCase, resource, disable_numpy


class TestLoadCubeFile(PillowTestCase):
    def test_minimal(self):
        lut = load_cube_file([
            "LUT_3D_SIZE 2",
            "0    0 0.031",
            "0.96 0 0.031",
            "0    1 0.031",
            "0.96 1 0.031",
            "0    0 0.931",
            "0.96 0 0.931",
            "0    1 0.931",
            "0.96 1 0.931",
        ])
        self.assertTrue(isinstance(lut, ImageFilter.Color3DLUT))
        self.assertEqual(tuple(lut.size), (2, 2, 2))
        self.assertEqual(lut.name, "Color 3D LUT")
        self.assertEqual(lut.table[:12], [
            0, 0, 0.031,  0.96, 0, 0.031,  0, 1, 0.031,  0.96, 1, 0.031])

    def test_parser(self):
        lut = load_cube_file([
            " # Comment",
            'TITLE "LUT name from file"',
            "  LUT_3D_SIZE 2 3 4",
            " SKIP THIS",
            "",
            " # Comment",
            "CHANNELS 4",
            "",
        ] + [
            " # Comment",
            "0    0 0.031 1",
            "0.96 0 0.031 1",
            "",
            "0    1 0.031 1",
            "0.96 1 0.031 1",
        ] * 6, target_mode='HSV')
        self.assertTrue(isinstance(lut, ImageFilter.Color3DLUT))
        self.assertEqual(tuple(lut.size), (2, 3, 4))
        self.assertEqual(lut.channels, 4)
        self.assertEqual(lut.name, "LUT name from file")
        self.assertEqual(lut.mode, 'HSV')
        self.assertEqual(lut.table[:12], [
            0, 0, 0.031, 1,  0.96, 0, 0.031, 1,  0, 1, 0.031, 1])

    def test_errors(self):
        with self.assertRaisesRegexp(ValueError, "No size found"):
            lut = load_cube_file([
                'TITLE "LUT name from file"',
            ] + [
                "0    0 0.031",
                "0.96 0 0.031",
            ] * 3)

        with self.assertRaisesRegexp(ValueError, "number of colors on line 3"):
            lut = load_cube_file([
                'LUT_3D_SIZE 2',
            ] + [
                "0    0 0.031",
                "0.96 0 0.031 1",
            ] * 3)

        with self.assertRaisesRegexp(ValueError, "1D LUT cube files"):
            lut = load_cube_file([
                'LUT_1D_SIZE 2',
            ] + [
                "0    0 0.031",
                "0.96 0 0.031 1",
            ])

        with self.assertRaisesRegexp(ValueError, "Not a number on line 2"):
            lut = load_cube_file([
                'LUT_3D_SIZE 2',
            ] + [
                "0  green 0.031",
                "0.96 0 0.031",
            ] * 3)

    def test_filename(self):
        with NamedTemporaryFile('w+t', delete=False) as f:
            f.write(
                "LUT_3D_SIZE 2\n"
                "0    0 0.031\n"
                "0.96 0 0.031\n"
                "0    1 0.031\n"
                "0.96 1 0.031\n"
                "0    0 0.931\n"
                "0.96 0 0.931\n"
                "0    1 0.931\n"
                "0.96 1 0.931\n"
            )

        try:
            lut = load_cube_file(f.name)
            self.assertTrue(isinstance(lut, ImageFilter.Color3DLUT))
            self.assertEqual(tuple(lut.size), (2, 2, 2))
            self.assertEqual(lut.name, "Color 3D LUT")
            self.assertEqual(lut.table[:12], [
                0, 0, 0.031,  0.96, 0, 0.031,  0, 1, 0.031,  0.96, 1, 0.031])
        finally:
            os.unlink(f.name)


class TestLoadHaldImage(PillowTestCase):
    def test_wrong_size(self):
        with self.assertRaisesRegexp(ValueError, "should be a square"):
            load_hald_image(Image.new('RGB', (8, 10)))

        with self.assertRaisesRegexp(ValueError, "Can't detect hald size"):
            load_hald_image(Image.new('RGB', (7, 7)))

        with self.assertRaisesRegexp(ValueError, "Can't detect hald size"):
            load_hald_image(Image.new('RGB', (729, 729)))

    def test_simple_parse(self):
        lut = load_hald_image(Image.new('RGB', (64, 64)), target_mode='HSV')
        self.assertTrue(isinstance(lut, ImageFilter.Color3DLUT))
        self.assertEqual(tuple(lut.size), (16, 16, 16))
        self.assertEqual(lut.channels, 3)
        self.assertEqual(lut.mode, 'HSV')

    def test_parse_file(self):
        lut = load_hald_image(resource('files', 'hald.6.hefe.png'))
        self.assertTrue(isinstance(lut, ImageFilter.Color3DLUT))
        self.assertEqual(tuple(lut.size), (36, 36, 36))
        self.assertEqual(lut.channels, 3)
        self.assertEqual(lut.mode, None)

    def test_correctness(self):
        lut_unit = ImageFilter.Color3DLUT.generate(
            16, lambda a, b, c: (a, b, c))
        image = Image.open(resource('files', 'hald.4.png'))

        lut_numpy = load_hald_image(image)
        self.assertEqual(tuple(lut_numpy.size), tuple(lut_unit.size))
        self.assertNotEqual(lut_numpy.table, lut_unit.table)
        for left, right in zip(lut_numpy.table, lut_unit.table):
            self.assertAlmostEqual(left, right, 7)

        with disable_numpy(loaders):
            lut_pillow = load_hald_image(image)
        self.assertEqual(tuple(lut_pillow.size), tuple(lut_unit.size))
        self.assertNotEqual(lut_pillow.table, lut_unit.table)
        for left, right in zip(lut_pillow.table, lut_unit.table):
            self.assertAlmostEqual(left, right, 7)

        for left, right in zip(lut_pillow.table, lut_numpy.table):
            self.assertAlmostEqual(left, right, 10)

