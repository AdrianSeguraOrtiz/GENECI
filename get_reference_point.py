import argparse
import pandas as pd

def main(file_path, column):
    # Read the CSV file while skipping the first header row and interpreting the second row as actual column names
    data = pd.read_csv(file_path, skiprows=[0])
    
    # Find the row with the maximum value in the column
    max_row = data.loc[data[column].idxmax()]
    
    # Extract the required columns
    result = max_row[['quality', 'degreedistribution', 'motifs']]
    
    # Print the result
    print(f"{result['quality']};{result['degreedistribution']};{result['motifs']}")

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Extract specific values from a CSV file.")
    parser.add_argument("file_path", type=str, help="Path to the input CSV file.")
    parser.add_argument("column", type=str, help="Columns to extract from the CSV file.")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute the main function
    main(args.file_path, args.column)
