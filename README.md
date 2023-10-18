# nmea_toolbox

## Usage

- Generate single file in the same folder.
  ```bash
  python csv_generator.py csv_file
  python kml_generator.py kml_file
  ```
- Generate multiple files in folders.
  ```bash
  # read files in data_folder/raw and generate files in data_folder/csv
  python csv_generator.py data_folder
  # read files in data_folder/csv and generate files in data_folder/kml
  python kml_generator.py data_folder
  ```