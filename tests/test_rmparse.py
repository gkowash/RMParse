"""Unit tests for rmparse.py"""
import unittest
from unittest.mock import patch, mock_open, MagicMock
import yaml
from rmparse import (
    CommandCase, County, RMConfig,
    parse_args, read_file, load_county_config,
    parse_nodes, format_nodes, get_command_case,
    get_flowrate, get_toc, get_csv_filepath, write_to_csv
)

class TestRMParse(unittest.TestCase):
    """Unit tests for rmparse.py"""

    @patch('builtins.open', new_callable=mock_open, read_data='TEST DATA')
    def test_read_file(self, mock_file):
        """Test file read and conversion to lowercase."""
        filepath = 'test.out'
        lines = read_file(filepath)
        self.assertEqual(lines, ['test data'])
        mock_file.assert_called_once_with(filepath, 'r', encoding='utf-8')

    @patch('argparse.ArgumentParser.parse_args', return_value=MagicMock(paths=['test.out'], digits=2, print=True))
    @patch('rmparse.Path.is_file', return_value=True)
    def test_parse_args(self, mock_is_file, mock_parse_args):
        """Test argument parsing."""
        files, precision, print_data = parse_args()
        self.assertEqual(len(files), 1)
        self.assertEqual(precision, 2)
        self.assertTrue(print_data)

    @patch('rmparse.Path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data=yaml.dump({
        "commands": {"INITIAL_AREA": ["init"]},
        "flowrate": {"INITIAL_AREA": ["flow"]},
        "time-of-concentration": {"INITIAL_AREA": ["toc"]},
        "new-section-text": "section",
        "confluence-summary-text": "summary"
    }))
    def test_load_county_config(self, mock_file, mock_exists):
        """Test reading of YAML template into Config object."""
        county = County.SAN_BERNARDINO
        template_dir = 'templates'
        config = load_county_config(county, template_dir)
        self.assertEqual(config.command_map[CommandCase.INITIAL_AREA], ['init'])
        self.assertEqual(config.flowrate_map[CommandCase.INITIAL_AREA], ['flow ='])
        self.assertEqual(config.toc_map[CommandCase.INITIAL_AREA], ['toc ='])
        self.assertEqual(config.new_section_text, 'section')
        self.assertEqual(config.confluence_summary_text, 'summary')

    def test_parse_nodes(self):
        """Test node line is parsed properly."""
        text = "	Process from Point/Station      101.000 to Point/Station      102.000"
        node1, node2 = parse_nodes(text)
        self.assertEqual(node1, 101)
        self.assertEqual(node2, 102)
    
    def test_format_nodes(self):
        """Test nodes are formatted correctly, with asterisk added for main confluences."""
        self.assertEqual(format_nodes(1, 2, CommandCase.INITIAL_AREA), '1-2')
        self.assertEqual(format_nodes(3, 4, CommandCase.CONFLUENCE_MAIN), '*3-4')

    def test_get_command_case(self):
        """Test success and failure cases for parsing command from output file."""
        config = RMConfig()
        config.command_map = {CommandCase.INITIAL_AREA: ["INITIAL AREA EVALUATION"]}
        self.assertEqual(get_command_case("	**** INITIAL AREA EVALUATION ****", config), CommandCase.INITIAL_AREA)
        self.assertIsNone(get_command_case("unknown command", config))

    def test_get_flowrate(self):
        """Test parsing of flowrate."""
        self.assertEqual(get_flowrate("	Total runoff =      3.141(CFS)	"), 3.141)
    
    def test_get_toc(self):
        """Test parsing of time of concentration."""
        self.assertEqual(get_toc("	Initial area time of concentration =   17.553 min."), 17.553)
    
    def test_get_csv_filepath(self):
        """Test conversion of .out filepath to .csv"""
        self.assertEqual(get_csv_filepath("test.out"), "test.csv")
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('csv.writer')
    def test_write_to_csv(self, mock_csv_writer, mock_file):
        """Test CSV writer."""
        data = [("1-2", 10.5, 15.2)]
        filepath = "output.csv"
        write_to_csv(data, filepath, 2, verbose=False)
        mock_file.assert_called_once_with(filepath, 'w', newline='', encoding='utf-8')
        mock_csv_writer().writerow.assert_any_call(['Nodes', 'Q', 'TC'])
        mock_csv_writer().writerow.assert_any_call(['1-2', '10.50', '15.20'])

if __name__ == '__main__':
    unittest.main()
