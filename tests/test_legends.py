import pathlib
import tempfile
import textwrap
import unittest
from geemap import legends


class LegendsTest(unittest.TestCase):

    def test_ee_table_to_legend(self):
        in_table_content = textwrap.dedent("""\
            Value\tColor\tDescription
            11\t466b9f\tOpen Water
            12\td1def8\tPerennial Ice/Snow
            21\tdec5c5\tDeveloped, Open Space
        """)
        expected_output = textwrap.dedent("""\
            {
            \t'11 Open Water': '466b9f',
            \t'12 Perennial Ice/Snow': 'd1def8',
            \t'21 Developed, Open Space': 'dec5c5'
            }
        """)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = pathlib.Path(tmpdir)
            in_table_path = tmpdir / "in_table.txt"
            out_file_path = tmpdir / "out_file.txt"

            in_table_path.write_text(in_table_content)
            legends.ee_table_to_legend(str(in_table_path), str(out_file_path))

            actual_output = out_file_path.read_text()
            self.assertEqual(expected_output, actual_output)


if __name__ == "__main__":
    unittest.main()
